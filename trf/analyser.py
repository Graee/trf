import re
from typing import Dict
from collections import Counter

import numpy as np
from pyknp import KNP, Juman

from trf.chunk import Chunk
from trf.constant import DefaultOptions
import trf.util as util


class Tree:

    def __init__(self, sentence, chunks):
        self.sentence = sentence
        self.chunks = chunks
        self.depth = self.depth()

    def find_next_chunk(self, chunk_id, depth):
        """Recursively find the next chunk until reaching the root
        """
        if self.chunks[chunk_id].link == -1:
            return depth
        else:
            next_chunk_id = self.chunks[chunk_id].link
            return self.find_next_chunk(next_chunk_id,
                                        depth + 1)

    def depth(self):
        """Calculate the mean depth of dependency tree
        Returns:
            int: The depth of given tree
        """
        current_tree_depth = 0

        for i, chunk in enumerate(self.chunks):
            depth = self.find_next_chunk(i, 0)
            if depth > current_tree_depth:
                current_tree_depth = depth

        return current_tree_depth


class Analyser:
    """Class for syntactic Analysis
    """

    def __init__(self, text, delimiter='\n'):
        self.text = text
        self.delimiter = delimiter
        self.sentences = util.split_text(self.text, delimiter)
        self.n_sentences = len(self.sentences)
        self.knp = KNP(option=DefaultOptions.KNP)
        self.trees = self._trees()
        self.juman = Juman()
        self.pos_rates = self._pos_rates()
        self.n_mrphs = self.calc_num_of_mrphs()
        self.n_types = self.calc_num_of_types()
        self.mean_n_mrphs = None \
            if self.n_sentences == 0 \
            else self.n_mrphs / self.n_sentences
        self.modality_rates = self.calc_modality_rates()

    def _trees(self):
        """Analyse dependency structure using KNP
        Returns:
            list(trf.Tree)
        """

        results = []

        for sentence in self.sentences:
            chunks = []
            for bnst in self.knp.parse(sentence).bnst_list():
                chunk = Chunk(chunk_id=bnst.bnst_id,
                              link=bnst.parent_id,
                              description=bnst.fstring)
                chunks.append(chunk)

            results.append(Tree(sentence, chunks))

        return results

    def _pos_rates(self):
        """Calculate the ratio of each pos of words in input text
        Returns:
            float: the ratio of each pos of words in input text
        """
        pos = []
        for sentence in self.sentences:
            juman_result = self.juman.analysis(sentence)
            pos += [mrph.hinsi for mrph in juman_result.mrph_list()]
        pos_counter = Counter(pos)
        total = sum(pos_counter.values())
        return {name: float(num)/total for name, num in pos_counter.items()}

    def calc_mean_tree_depth(self):
        """Calculate the mean depth of dependency tree
        Returns:
            float: The mean depth of trees
        """
        return np.mean([tree.depth for tree in self.trees])

    def calc_mean_sentence_length(self):
        """Calculate the mean length (# of morphs) of sentences
        Returns:
            float: the mean length of sentences
        """
        result = 0
        for sentence in self.sentences:
            juman_result = self.juman.analysis(sentence)
            result += len(juman_result.mrph_list())
        return result / self.n_sentences

    def calc_num_of_sentences(self):
        """Calculate the number of sentences of input text
        Returns:
            int: the number of sentences of input text splitted by delimiter (default '。')
        """
        return self.n_sentences

    def calc_num_of_types(self):
        """Calculate the number of types of input text
        Returns:
            int: the number of types of input text
        """
        surfaces = []
        for sentence in self.sentences:
            juman_result = self.juman.analysis(sentence)
            surfaces += [mrph.midasi for mrph in juman_result.mrph_list()]
        word_type_counter = Counter(surfaces)
        return len(word_type_counter)

    def calc_num_of_mrphs(self):
        """Calculate the number of morphemes of input text
        Returns:
            int: the number of morphemes of input text
        """
        result = 0
        for sentence in self.sentences:
            juman_result = self.juman.analysis(sentence)
            result += len(juman_result.mrph_list())
        return result

    def calc_modality_rates(self) -> Dict[str, float]:

        modality_counter = Counter()
        for i, s in enumerate(self.sentences):
            chunks = []
            for bnst in self.knp.parse(s).bnst_list():
                chunk = Chunk(chunk_id=bnst.bnst_id,
                              link=bnst.parent,
                              description=bnst.fstring)
                chunks.append(chunk)

            s = "".join([chunk.description for chunk in chunks])
            ms = set(re.findall("<モダリティ-(.+?)>", s))
            modality_counter += Counter(ms)

            n = len(self.sentences)

        return dict([(k, float(c) / n)
                     for k, c in modality_counter.items()])
