#! /usr/bin/env python

############################################################################
##  popgensim.py
##
##  Part of the DendroPy library for phylogenetic computing.
##
##  Copyright 2008 Jeet Sukumaran and Mark T. Holder.
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
############################################################################

"""
Generate sequences under population genetic models.
"""

import StringIO
import random
import copy

from dendropy import GLOBAL_RNG
from dendropy import datasets
from dendropy import treegen
from dendropy import chargen
from dendropy import nexus

try:
    from pyseqgen import seqgen
    SEQGEN = True
except:
    from dendropy import chargen
    SEQGEN = False

class FragmentedPopulations(object):

    def __init__(self, 
                 div_time_gens,
                 num_desc_pops = 2,
                 mutrate_per_site_per_generation=10e-8,                  
                 desc_pop_size=10000,
                 rng=GLOBAL_RNG):
        """
        `div_time_gens` : generations since divergence,
        `num_desc_pops` : number of descendent populations,
        `mutrate_per_site_per_generation` : sequence mutation rate, per-site per-generation
        `desc_diploid_pop_size` : descendent lineage population size (=N; ancestral pop size = num_desc_pops * N)
        `rng` : random number generator
        """
        self.div_time_gens = div_time_gens
        self.num_desc_pops = num_desc_pops
        self.mutrate_per_site_per_generation = mutrate_per_site_per_generation
        self.desc_pop_size = desc_pop_size
        self.rng = rng
        self.kappa = 1.0
        self.base_freqs=[0.25, 0.25, 0.25, 0.25]
        self.seqgen_path = 'seq-gen'
        self.gene_tree = None
        self.pop_tree = None
        self.mutation_tree = None
        
    def _get_theta(self):
        return 4 * self.mutrate_per_gene_per_generation * self.desc_pop_size
        
    def generate_sequences(self, 
                           species_name, 
                           samples_per_pop=10, 
                           seq_len=2000, 
                           use_seq_gen=True):
                           
        self.generate_pop_tree(species_name=species_name, samples_per_pop=samples_per_pop)                           
        self.generate_gene_tree(species_name=species_name, samples_per_pop=samples_per_pop)                                
        d = datasets.Dataset()
        d.add_taxa_block(taxa_block=self.mutation_tree.taxa_block)

        if SEQGEN and use_seq_gen:

            sg = seqgen.SeqGen()
            sg.seqgen_path = self.seqgen_path
            sg.num_replicates = 1
            sg.quiet = True
            sg.rng = self.rng
            sg.seq_len = seq_len
            sg.char_model = 'HKY'
            sg.ti_tv = float(self.kappa) / 2
            sg.state_freqs = self.base_freqs
            sg.trees = [self.mutation_tree]    
            d = sg.generate_dataset(dataset=d)
            d.taxa_blocks[0].sort()      
              
            return d
        else:
            return chargen.generate_hky_dataset(seq_len=seq_len,
                                                tree_model=self.mutation_tree,                   
                                                mutation_rate=1.0, 
                                                kappa=1.0,
                                                base_freqs=[0.25, 0.25, 0.25, 0.25],
                                                root_states=None,    
                                                dataset=d,
                                                rng=self.rng)
                                                
    def generate_pop_tree(self, species_name, samples_per_pop=10):
        tree_data = { 'sp': species_name, 'divt': self.div_time_gens }
        desc_lineages = []
        for i in xrange(self.num_desc_pops):
            tree_data['id'] = i+1
            desc_lineages.append("%(sp)s%(id)d:%(divt)d" % tree_data)
        tree_string = "(" + (",".join(desc_lineages)) + ("):%d" % 0) #% (self.num_desc_pops * self.desc_pop_size * 10))
        self.pop_tree = nexus.read_trees(StringIO.StringIO(tree_string))[0][0]
        return self.pop_tree
                                                
    def generate_gene_tree(self, species_name, samples_per_pop=10):
        """
        Given:
            `species_name` : string identifying species/taxon       
            `samples_per_pop` : number of samples (genes) per population
        Returns:
            DendroPy tree, with branch lengths in generations
        """
        if self.pop_tree is None:
            self.generate_pop_tree(species_name, samples_per_pop=10)
        for idx, leaf in enumerate(self.pop_tree.leaf_iter()):
            if idx == 1:
                # ancestral population = num_desc_pops * desc population
                leaf.parent_node.edge.pop_size = self.num_desc_pops * self.desc_pop_size
            leaf.edge.pop_size = self.desc_pop_size 
            leaf.num_genes = samples_per_pop      
        self.gene_tree, self.pop_tree = treegen.constrained_kingman(self.pop_tree, 
                                                          gene_node_label_func=lambda x,y: "%sX%d" % (x,y),
                                                          rng=self.rng)
                                                          
        self.mutation_tree = copy.deepcopy(self.gene_tree)
        for edge in self.mutation_tree.preorder_edge_iter():
            edge.length = edge.length * self.mutrate_per_site_per_generation                                                          
        return self.gene_tree
    