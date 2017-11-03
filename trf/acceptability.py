import errno
import os
from typing import Dict, List, Tuple, Union
import tempfile
from subprocess import Popen, PIPE
import math
import numpy

import trf.constant as const


class Acceptability:

    def __init__(self, text: str, rnnlm_model_path: str):

        self.text = text
        self.sentences = [s.strip() for s in text.split('\n')
                          if s.strip() != '']

        if not os.path.isfile(rnnlm_model_path):
            raise FileNotFoundError(errno.ENOENT,
                                    os.strerror(errno.ENOENT),
                                    rnnlm_model_path)
        self.rnnlm_model_path = rnnlm_model_path

        self.word_freq, self.n_total_words = self._load_word_freq(threshold=1)

        self.rnnlm_scores = self.get_rnnlm_scores()
        self.unigram_scores = self.calc_unigram_scores()

        self.mean_unigram_scores = self.calc_mean_unigram_scores()

        self.normalized_scores_div = \
            self.calc_normalized_scores('div')

        self.normalized_scores_sub = \
            self.calc_normalized_scores('sub')

        self.normalized_scores_len = \
            self.calc_normalized_scores('len')

    def get_rnnlm_scores(self) -> List[Union[None, float]]:
        """Get log likelihood scores by calling RNNLM
        """

        textfile = tempfile.NamedTemporaryFile(delete=True)
        textfile.write(str.encode(self.text))
        textfile.seek(0)

        command = ['rnnlm', '-rnnlm', self.rnnlm_model_path,
                   '-test', textfile.name]
        process = Popen(command, stdout=PIPE, stderr=PIPE)
        output , _ = process.communicate()
        lines = [line.strip() for line in output.decode('UTF-8').split('\n')
                 if line.strip() != '']
        scores = []
        for line in lines:
            if line == const.OUT_OF_VOCABULARY:
                scores.append(None)
            else:
                try:
                    score = float(line)
                    scores.append(score)
                except ValueError:
                    pass
        textfile.close()
        return scores

    def _load_word_freq(self, threshold: int) -> Tuple[Dict[str, int], int]:
        n_total_words = 0
        word_freq = {}
        with open(self.rnnlm_model_path, mode='r') as f:
            for line in f:

                n_total_words += 1

                word, freq = line.split(' ')
                freq = int(freq)
                if freq > threshold:
                    word_freq[word] = freq
                else:
                    word_freq['<unk/>'] = word_freq.get('<unk/>', 0) + 1

        return (word_freq, n_total_words)

    def calc_unigram_scores(self) -> List[float]:

        unigram_scores = []
        for s in self.sentences:
            unigram_score = 0.0

            for word in s.split():
                n = float(self.n_total_words)
                x = float(self.word_freq.get(word, self.word_freq['<unk/>']))
                unigram_score += math.log(x / n)

            unigram_scores.append(unigram_score)

        return unigram_scores

    def calc_mean_unigram_scores(self) -> List[Union[None, float]]:
        mean_unigram_scores = []
        for score, sentence in zip(self.unigram_scores, self.sentences):
            n = len(self.sentences)
            x = None \
                if score is None or n == 0 \
                else float(score) / float(len(self.sentences))
            mean_unigram_scores.append(x)
        return mean_unigram_scores

    def calc_normalized_scores(self, method: str) -> List[Union[None, float]]:

        normalized_scores = []
        for score, unigram_score, s in zip(self.rnnlm_scores,
                                           self.unigram_scores,
                                           self.sentences):
            x = None \
                if score is None or numpy.isclose(unigram_score,
                                                  0.0, rtol=1e-05) \
                else _f(score, unigram_score, len(s), method)
            normalized_scores.append(x)
        return normalized_scores


def _f(score: float, unigram_score: float, length: int, method: str) -> float:

    if method == 'div':
        return (-1) * float(score) / float(unigram_score)
    elif method == 'sub':
        return float(score) - float(unigram_score)
    elif method == 'len':
        return (float(score) - float(unigram_score)) / length
    else:
        raise ValueError
