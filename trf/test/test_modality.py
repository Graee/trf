from __future__ import division, unicode_literals

import unittest

from trf.modality import Modality


class TestModality(unittest.TestCase):

    def test_modality(self):

        lines = ['ご飯を食べるらしい',
                 'ご飯を食べるつもりだ',
                 'ご飯を食べるつもりだ']
        modality = Modality('\n'.join(lines), delimiter='\n')

        evidence = 0.0
        decision = 0.0
        for k, v in modality.rates.items():

            if k == "<モダリティ-認識-証拠性>":
                evidence = v
            elif k == "<モダリティ-意思>":
                decision = v

        # self.assertAlmostEqual(evidence, 1 / 3)
        # self.assertAlmostEqual(decision, 2 / 3)


if __name__ == '__main__':
    unittest.main()
