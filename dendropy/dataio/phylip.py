#! /usr/bin/env python

###############################################################################
##  DendroPy Phylogenetic Computing Library.
##
##  Copyright 2009 Jeet Sukumaran and Mark T. Holder.
##
##  This program is free software; you can redistribute it and/or modify
##  it under the terms of the GNU General Public License as published by
##  the Free Software Foundation; either version 3 of the License, or
##  (at your option) any later version.
##
##  This program is distributed in the hope that it will be useful,
##  but WITHOUT ANY WARRANTY; without even the implied warranty of
##  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
##  GNU General Public License for more details.
##
##  You should have received a copy of the GNU General Public License along
##  with this program. If not, see <http://www.gnu.org/licenses/>.
##
###############################################################################

"""
Implementation of PHYLIP-schema i/o client(s).
"""

from dendropy.utility import iosys

class PhylipWriter(iosys.DataWriter):
    "Implements the DataWriter interface for handling PHYLIP files."

    def __init__(self, **kwargs):
        "Calls the base class constructor."
        iosys.DataWriter.__init__(self, **kwargs)

    def write(self, stream, **kwargs):
        "Writes dataset to a full PHYLIP document."
        if self.exclude_chars:
            return
        assert self.dataset is not None, \
            "NexusWriter instance is not attached to a DataSet: no source of data"
        char_matrix = self.dataset.char_matrices[0]
        n_seqs = len(char_matrix)
        n_sites = len(char_matrix.values()[0])
        stream.write("%d %d\n" % (n_seqs, n_sites))
        maxlen = max([len(str(taxon)) for taxon in char_matrix])
        for taxon in char_matrix.taxon_set:
            stream.write("%s        %s\n" % ( str(taxon).ljust(maxlen), str(char_matrix[taxon].symbols_as_string()).replace(' ', '')))