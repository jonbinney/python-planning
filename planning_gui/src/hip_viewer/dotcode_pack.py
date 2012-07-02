# Software License Agreement (BSD License)
#
# Copyright (c) 2008, Willow Garage, Inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
#  * Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#  * Redistributions in binary form must reproduce the above
#    copyright notice, this list of conditions and the following
#    disclaimer in the documentation and/or other materials provided
#    with the distribution.
#  * Neither the name of Willow Garage, Inc. nor the names of its
#    contributors may be used to endorse or promote products derived
#    from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

from __future__ import with_statement, print_function

import rospkg
import pydot
import sys

def get_graph():
    graph = pydot.Dot('graphname', graph_type='digraph', rank = 'same', simplify = True)
    graph.set_ranksep(2.0);
    graph.set_compound(True)
    return graph


                
class Generator:
    
    def __init__(self, selected_names = [], excludes = [], with_stacks = False, hide_transitives = True, depth = 1):
        """
        
        :param hide_transitives: if true, then dependency of children to grandchildren will be hidden if parent has same dependency
        """
        self.rospack = rospkg.RosPack()
        self.rosstack = rospkg.RosStack()
        self.stacks = {}
        self.packages = {}
        self.edges = []
        self.excludes = excludes
        self.with_stacks = with_stacks
        self.depth = depth
        self.selected_names = selected_names
        self.hide_transitives = hide_transitives
        
        for name in self.selected_names:
            if name is None or name.strip() == '':
                continue
            namefound = False
            if name in self.rospack.list():
                self.add_package_recursively(name)
                namefound = True
            if name in self.rosstack.list():
                namefound = True
                for package_name in self.rosstack.packages_of(name):
                    self.add_package_recursively(package_name)

    def node_for_package(self, package_name):
        node = pydot.Node(package_name)
        node.set_shape('box')
        if package_name in self.selected_names:
            node.set_color('red')
        return node
    
    def graph_for_stack(self, stackname):
        if stackname is None:
            return None
        g = pydot.Cluster(stackname, rank = 'same', simplify = True)
        g.set_style('bold')
        g.set_label("Stack: %s \\n"%stackname)
        if stackname in self.selected_names:
            g.set_color('red')
        return g

    def generate(self):
        graph = get_graph()
        if self.with_stacks:
            for stackname in self.stacks:
                g = self.graph_for_stack(stackname)
                for package_name in self.stacks[stackname]['packages']:
                    g.add_node(self.node_for_package(package_name))
                graph.add_subgraph(g)
        else:
            for package_name in self.packages:
                graph.add_node(self.node_for_package(package_name))
        for edge_tupel in self.edges:
            edge = pydot.Edge(edge_tupel[0], edge_tupel[1])
            
            graph.add_edge(edge)
        return graph
        
    def _add_stack(self, stackname):
        if stackname is None or stackname in self.stacks:
            return
        self.stacks[stackname] = {'packages': []}
        
    def _add_package(self, package_name):
        if package_name in self.packages:
            return False
        self.packages[package_name] = {}
        if self.with_stacks:
            stackname = self.rospack.stack_of(package_name)
            if not stackname is None:
                if not stackname in self.stacks:
                    self._add_stack(stackname)
                self.stacks[stackname]['packages'].append(package_name)
        return True
    
    def _add_edge(self, name1, name2, attributes = None):
        self.edges.append((name1, name2, attributes))
        

    def add_package_recursively(self, package_name, expanded = None, depth = None):
        if package_name in self.excludes:
            return False
        if (depth == 0):
            return False
        if (depth == None):
            depth = self.depth
        self._add_package(package_name)
        if expanded is None:
            expanded = []
        expanded.append(package_name)
        if (depth != 1):
            depends = self.rospack.get_depends(package_name, implicit = False)
            new_nodes = []
            for dep_name in [x for x in depends if x not in self.excludes]:
                if not self.hide_transitives or not dep_name in expanded:
                    new_nodes.append(dep_name)
                    self._add_edge(package_name, dep_name)
                    self._add_package(dep_name)
                    expanded.append(dep_name)
            for dep_name in new_nodes:
                self.add_package_recursively(package_name = dep_name, 
                                             expanded = expanded,
                                             depth = depth-1)

def generate_dotcode(selected_names = [], depth = 3, excludes = [], with_stacks = False):
    if depth is None:
        depth = -1
    gen = Generator(selected_names = selected_names,
                    depth = depth, 
                    excludes = excludes, 
                    with_stacks = with_stacks)
    
    graph = gen.generate()
    import pydb; pydb.set_trace()
    dot = graph.create_dot()
    # sadly pydot generates line wraps cutting between numbers
    return dot.replace("\\\n", "")
