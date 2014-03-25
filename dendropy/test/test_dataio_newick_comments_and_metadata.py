#! /usr/bin/env python

##############################################################################
##  DendroPy Phylogenetic Computing Library.
##
##  Copyright 2010 Jeet Sukumaran and Mark T. Holder.
##  All rights reserved.
##
##  See "LICENSE.txt" for terms and conditions of usage.
##
##  If you use this work or any portion thereof in published work,
##  please cite it as:
##
##     Sukumaran, J. and M. T. Holder. 2010. DendroPy: a Python library
##     for phylogenetic computing. Bioinformatics 26: 1569-1571.
##
##############################################################################

"""
Tests for correct comment handling in NEWICK-formatted trees.
"""

import unittest
import dendropy

class TreeWithCommentsTestCase(unittest.TestCase):

    def test_comment_association(self):
        tree_strings = [
                "([a1][a2]a[a3]:[a4]1[a5],[h1][h2][h3]([b1]b[b2]:[b3][b4]2[b5],[g1][g2]([c1]c[c2]:[c3]3[c4][c5],[f1]([d1]d[d2][d3]:[d4]4[d5],[e1]e[e2]:5[e3][e4][e5])[f2]f[f3]:[f4]6[f5])[g3][g4]g:7[g5])[h4]h[h5]:8)[i1][i2]i[i3]:[i4]9[i5];",
            ]
        for tree_string in tree_strings:
            tree = dendropy.Tree.get_from_string(
                    tree_string,
                    "newick",
                    suppress_external_node_taxa=True)
            for nd in tree:
                exp_brlen = ord(nd.label[0]) - ord('a') + 1
                self.assertEqual(nd.edge.length, exp_brlen)
                self.assertEqual(len(nd.comments), 5)
                for comment in nd.comments:
                    self.assertEqual(comment[0], nd.label)

if __name__ == "__main__":
    unittest.main()
