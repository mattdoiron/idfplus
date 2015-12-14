#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Copyright (c) 2014, Matthew Doiron. All rights reserved.

IDF+ is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

IDF+ is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with IDF+. If not, see <http://www.gnu.org/licenses/>.
"""

# System imports
import logging
import networkx as nx
import math

# Setup logging
log = logging.getLogger(__name__)


class ReferenceModel(object):
    """Wrapper around a NetworkX DiGraph that stores relationships between fields.
    """

    def __init__(self, outer):
        self._ref_graph = nx.DiGraph()
        self._idf = outer
        self._idd = None

    def set_idd(self, idd):
        """Sets the IDD file because it might not have existed during init.

        :param idd:
        """

        self._idd = idd

    def reference_count(self, field):
        """Returns the sum of incoming and outgoing references.

        :param field:
        :return:
        """

        # Continue only if a valid field is present and the right type
        if not field:
            return -1
        if field.ref_type != 'object-list' and field.ref_type != 'reference':
            return -1

        # Find incoming and outgoing references
        try:
            ancestors = nx.ancestors(self._ref_graph, field.uuid)
            descendants = nx.descendants(self._ref_graph, field.uuid)
        except nx.exception.NetworkXError:
            return -1

        return len(ancestors) + len(descendants)

    def update_reference(self, field, old_value):
        """Updates the specified references involving the given field.

        :param old_value:
        :param field:
        """

        # Continue only if there is a value and it's different
        if not field.value:
            return
        if field.value == old_value:
            return

        parser = self._idf.parser

        with self._idf.index.searcher() as searcher:

            if field.ref_type == 'reference':

                # Remove all current references to the old value
                query = 'value:"{}" ref_type:object-list'.format(old_value.lower())
                results = searcher.search(parser.parse(query), limit=None)
                edge_list = [(hit['uuid'], field.uuid) for hit in results]
                self._ref_graph.remove_edges_from(edge_list)

                # Add new edges to node graph for references to the new value
                query = 'value:"{}" ref_type:object-list'.format(field.value.lower())
                results = searcher.search(parser.parse(query), limit=None)
                edge_list = [(hit['uuid'], field.uuid) for hit in results]
                self._ref_graph.add_edges_from(edge_list)

            elif field.ref_type == 'object-list':

                # Remove all current references to the old value
                query = 'value:"{}" ref_type:reference'.format(old_value.lower())
                results = searcher.search(parser.parse(query), limit=None)
                edge_list = [(field.uuid, hit['uuid']) for hit in results]
                self._ref_graph.remove_edges_from(edge_list)

                # Add new edges to node graph for references to the new value
                query = 'value:"{}" ref_type:reference'.format(field.value.lower())
                results = searcher.search(parser.parse(query), limit=None)
                edge_list = [(field.uuid, hit['uuid']) for hit in results]
                self._ref_graph.add_edges_from(edge_list)

    def insert_nodes(self, objects_to_insert, update_references=True):
        """Inserts fields into the reference node graph and optionally update relationships.

        :param update_references:
        :param objects_to_insert:
        """

        # First, create nodes for all fields in these objects
        for obj in objects_to_insert:
            nodes = [(field.uuid, {'data': field}) for field in obj if field]
            self._ref_graph.add_nodes_from(nodes)

        # Continue only if we want to also update references
        if update_references is False:
            return

        with self._idf.index.searcher() as searcher:

            for obj in objects_to_insert:

                for i, field in enumerate(obj):

                    # Continue only if there is a field and it's the right type
                    if not field:
                        continue
                    if not field.value or field.ref_type != 'reference':
                        continue

                    query = 'value:"{}" ref_type:object-list'.format(field.value.lower())
                    results = searcher.search(self._idf.parser.parse(query), limit=None)
                    edge_list = [(hit['uuid'], field.uuid) for hit in results]
                    self._ref_graph.add_edges_from(edge_list)

    def connect_nodes(self):
        """Processes the entire reference graph to connect its nodes. Yield progress.
        """

        obj_list_length = self._idd.object_list_length
        k = 0

        with self._idf.index.searcher() as searcher:

            for object_list_name, object_list_set in self._idd.object_lists.iteritems():
                object_lists = list(object_list_set)

                for object_class in object_lists:

                    for obj in self._idf.get(object_class, []):

                        for i, field in enumerate(obj):

                            # If this field is a reference-type then connect nodes
                            if field and field.value and field.ref_type == 'reference':
                                query = 'value:"{}" ref_type:object-list'.format(field.value.lower())
                                results = searcher.search(self._idf.parser.parse(query), limit=None)
                                edge_list = [(hit['uuid'], field.uuid) for hit in results]
                                self._ref_graph.add_edges_from(edge_list)

                    yield math.ceil(50 + (100 * 0.5 * (k+1) / obj_list_length))
                    k += 1
