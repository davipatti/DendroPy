#! /usr/bin/env python

############################################################################
##  treesum.py
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
Tree summarization.
"""

import sys
from dendropy import splits
from dendropy import taxa
from dendropy import trees
from dendropy import treegen

def deepest_compatible_node(start_node, split, taxa_mask, unrooted):
    """
    Assumes:
        - start_node is a node on a tree
        - edges on tree have been decorated with splits
        - start_node is compatible with split (root if all else fails)
    Returns:
        - deepest node in tree (i.e., furthest from root) that is
          compatible with split (i.e, includes all taxa in split) yet
          not equal to the split.
    """
    for node in start_node.child_nodes():
        if (node.edge.split_mask & split) \
            and (unrooted and (node.edge.split_mask & (split ^ taxa_mask))) \
            and (node.edge.split_mask != split):
            return deepest_compatible_node(node, split, taxa_mask, unrooted)
    return start_node        

class TreeSummarizer(object):
    """
    Summarizes a distribution of trees.
    """
    
    def __init__(self):
        """
        Initializes settings.
        """
        self.burnin = None 
        self.support_as_labels = True 
        self.support_as_percentages = False
        self.support_label_decimals = 2               
        self.verbose=False
        self.write_message = None# sys.stderr.write
        self.progress_message_prefix = None
        self.progress_message_suffix = None
        self.ignore_node_ages = True
        self.total_trees_read = 0    
        self.total_trees_counted = 0         
        self.total_trees_ignored = 0
        
    def send_progress_message(self, msg):
        """
        Writes progress message.
        """
        if self.verbose and self.write_message:
            if self.progress_message_prefix:
                prefix = self.progress_message_prefix
            else:
                prefix = ""
            if self.progress_message_suffix:
                suffix = self.progress_message_suffix
            else:
                suffix = ""                
            self.write_message("%s%s%s" % (prefix, msg, suffix))                    
            
    def compose_support_label(self, split_support_freq):
        """
        Returns an appropriately composed and formatted support label.
        """
        if self.support_as_percentages:
            if self.support_label_decimals <= 0:
                support_label = "%d" % round(split_support_freq * 100, 0)
            else:                
                support_label_template = "%%0.%df" % self.support_label_decimals
                support_label = support_label_template % round(split_support_freq * 100, 
                    self.support_label_decimals)
        else:                
            if self.support_label_decimals <= 0:
                support_label_decimals = 2
            else:
                support_label_decimals = self.support_label_decimals
            support_label_template = "%%0.%df" % support_label_decimals
            support_label = support_label_template % round(split_support_freq, 
                support_label_decimals)
        return support_label            
        
    def map_split_support_to_node(self, node, split_support):
        """
        Appropriately sets up a node.
        """
        if self.support_as_labels:
            node.label = self.compose_support_label(split_support)
        else:
            if self.support_as_percentages:
                node.edge.length = split_support * 100
            else:                        
                node.edge.length = split_support
        return node                
        
    def map_split_support_to_tree(self, tree, split_distribution):
        """
        Maps splits support to the given tree.
        """
        split_frequencies = split_distribution.split_frequencies
        tree.normalize_taxa(taxa_block=split_distribution.taxa_block)
        splits.encode_splits(tree, 
                             taxa_block=split_distribution.taxa_block,
                             unrooted=split_distribution.unrooted)                            
        for split in tree.split_edges:
            if split in split_frequencies:
                split_support = split_frequencies[split]
            else:
                split_support = 0.0
            self.map_split_support_to_node(tree.split_edges[split].head_node, split_support)                  
        return tree            
            
    def tree_from_splits(self, 
                         split_distribution, 
                         min_freq=0.5,
                         include_edge_lengths=True):
        """
        Returns a consensus tree constructed from splits given in `split_distribution`.
        """                      
        taxa_block = split_distribution.taxa_block
        con_tree = treegen.star_tree(taxa_block)
        split_freqs = split_distribution.split_frequencies
        taxa_mask = taxa_block.all_taxa_bitmask()
        splits.encode_splits(con_tree, 
                             taxa_block, 
                             unrooted=split_distribution.unrooted)         
        #start_leaf = con_tree.split_edges[0x01].head_node        
        for split in split_freqs:          
            if (split_freqs[split] > min_freq) \
                and (split ^ taxa_mask) \
                and ((split-1) & split) \
                and (((split ^ taxa_mask) -1) & (split ^ taxa_mask)):  
                # ^^^^^^^
                # above min freq
                # not root (i.e., all "1's")
                # not singleton (i.e., one "1")
                # not singleton (i.e., one "0")               
#                 parent_node = start_leaf
#                 while (parent_node.edge.split_mask & split) != split:
#                     parent_node = parent_node.parent_node
                parent_node = deepest_compatible_node(start_node=con_tree.seed_node, 
                    split=split, 
                    taxa_mask=taxa_mask, 
                    unrooted=split_distribution.unrooted)
                if parent_node.edge.split_mask == split:
                    #or (split_distribution.unrooted and parent_node.edge.split_mask == (split ^ taxa_mask)):                                    
                    pass
                else:                    
                    new_node = trees.Node()
                    self.map_split_support_to_node(node=new_node, split_support=split_freqs[split])                
                    if self.support_as_labels and include_edge_lengths:
                            new_node.edge.length = float(sum(split_distribution.split_edge_lengths[split])) / len(split_distribution.split_edge_lengths[split])
                    new_node_children = []
                    new_node.edge.split_mask = 0
                    for child in parent_node.child_nodes():
                        # might need to modify the following if rooted splits
                        # are used
                        if (child.edge.split_mask & (split ^ taxa_mask) ) \
                            and ((child.edge.split_mask ^ taxa_mask) & split):
                            assert child.edge.split_mask != split
                            new_node_children.append(child)
                    for child in new_node_children:
                        parent_node.remove_child(child)
                        new_node.add_child(child)
                        new_node.edge.split_mask = new_node.edge.split_mask | child.edge.split_mask
                    parent_node.add_child(new_node)

        ## here we add the support values and/or edge lengths for the terminal taxa ##
        for node in con_tree.leaf_nodes():
            if split_distribution.unrooted:                                     
                split = con_tree.split_edges.normalize_key(node.edge.split_mask)
            else:
                split = node.edge.split_mask
            self.map_split_support_to_node(node, 1.0)
            if self.support_as_labels and include_edge_lengths:
                if split in split_distribution.split_edge_lengths:
                    node.edge.length = float(sum(split_distribution.split_edge_lengths[split])) / len(split_distribution.split_edge_lengths[split])
                else:
                    node.edge.length = 0.0
        return con_tree                
                                                
    def count_splits_on_trees(self, tree_files, tree_iterator, split_distribution=None, taxa_block=None):
        """
        Given a list of trees file, a SplitsDistribution object (a new one, or,
        if passed as an argument) is returned collating the split data in the files.
        """
        if split_distribution is None:
            split_distribution = splits.SplitDistribution()
        split_distribution.ignore_node_ages = self.ignore_node_ages            
        if taxa_block is not None:
            split_distribution.taxa_block = taxa_block            
#         if not isinstance(tree_files, list):
#             tree_files = [tree_files]
        total_tree_files = len(tree_files)
        for tree_file_idx, tree_file in enumerate(tree_files):
            file_trees_read = 0
            if isinstance(tree_file, str):
                tree_file_obj = open(tree_file, "r")
            else:
                tree_file_obj = tree_file             
            current_file_note = "Tree file %d of %d: " % (tree_file_idx+1, total_tree_files)
            for tree_idx, tree in enumerate(tree_iterator(file_obj=open(tree_file, "r"))):
                self.total_trees_read += 1
                file_trees_read += 1
                if not self.burnin or file_trees_read > self.burnin:
                    self.total_trees_counted += 1
                    self.send_progress_message("%sCounting splits in tree %d" % (current_file_note, (tree_idx+1)))
                    split_distribution.count_splits_on_tree(tree)
                else:
                    self.total_trees_ignored += 1
                    self.send_progress_message("%sSkipping tree %d (burn-in=%d)" % (current_file_note, (tree_idx+1), self.burnin))        
        return split_distribution                        
