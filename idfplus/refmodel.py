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

# Prepare for Python 3
from __future__ import (print_function, division, absolute_import)

# System imports
import networkx as nx
import pprint
import math

# Package imports
from . import logger

# Constants
from . import config

# Setup logging
log = logger.setup_logging(config.LOG_LEVEL, __name__, config.LOG_PATH)


class ReferenceModel(object):
    """Wrapper around a dictionary and DiGraph that stores object references.
    """

    def __init__(self):
        self._ref_graph = nx.DiGraph()
        self._ref_lists = dict()

    def populate_ref_list(self, idf):
        """Populates the reference list using the idf file
        :param idf:
        """

        self._ref_lists.update((k, dict()) for k, v in idf._idd.object_lists.iteritems())

    def reference(self, node_id):
        """Returns the node for the specified reference.
        :param node_id:
        """

    def add_field(self, field, tags):
        """Adds a new field and takes care of the references
        :param field:
        :param tags:
        """

        # Add a node to the graph for the new field
        self._ref_graph.add_node(field.uuid, data=field)

        # Add new entries to the reference list for the new field
        try:
            # Ensure we have a list of object classes
            obj_list_names = tags['reference']
            if not isinstance(obj_list_names, list):
                obj_list_names = [tags['reference']]

            # Save the node in the idf file's reference list
            for object_list in obj_list_names:
                id_tup = (field.uuid, field)
                try:
                    self._ref_lists[object_list][field.value].append(id_tup)
                except (AttributeError, KeyError):
                    self._ref_lists[object_list][field.value] = [id_tup]
        except KeyError:
            pass

    def add_reference(self, field, cls_list, object_list_name):
        """Creates the specified reference.
        :param field:
        :param cls_list:
        :param object_list_name:
        """

        ref_node = self._ref_lists[cls_list][field.value]
        for ref_uuid, ref in ref_node:
            self._ref_graph.add_edge(field._uuid,
                                     ref_uuid,
                                     obj_list=object_list_name)

    def update_reference(self):
        """Updates the specified reference.
        """

        pass

    def delete_reference(self):
        """Deletes the specified reference.
        """

        pass

    def update_references(self, field):
        """Updates the reference graph

        :param field:
        :return: :rtype:
        """

        # Continue only if this field references an object from an object-list
        object_list_name = field.tags.get('object-list', '')
        if not object_list_name:
            return

        graph = self._ref_graph
        node_count = graph.number_of_nodes()

        # Cycle through only nodes to avoid cycling through all objects
        for k, node in enumerate(graph.nodes_iter(data=True)):

            try:
                # Ensure we have a list to simplify later operations
                if not isinstance(object_list_name, list):
                    object_list_name = [field.tags['object-list']]

                # Cycle through all class names in the object lists
                for cls_list in object_list_name:
                    ref_nodes = self._ref_lists[cls_list].get(field.value, None)
                    if not ref_nodes:
                        return
                    for ref_uuid, ref in ref_nodes:
                        # Add edges to the graph for the new reference
                        graph.add_edge(field._uuid,
                                       ref_uuid,
                                       obj_list=object_list_name)

                        # Remove old reference

            except (IndexError, KeyError):
                continue

            yield math.ceil(50 + (100 * 0.5 * (k+1) / node_count))

    def update_reference_names(self, field, old_value):
        """Update the list of names used for references

        :param field:
        :param old_value:
        :return: :rtype:
        """

        # Get the graph and the connections to this field
        ref_graph = self._ref_graph
        ref_lists = self._ref_lists
        new_value = field.value
        obj_list_set = set()

        print('--------')
        pprint.pprint(ref_lists['ScheduleTypeLimitsNames'])

        # Continue only if there is a new value
        if new_value == old_value:
            return

        # Continue only if this field is a node in the ref_graph and has ancestors
        try:
            ancestors = nx.ancestors(ref_graph, field._uuid)
        except nx.exception.NetworkXError:
            return
        else:
            if not ancestors:
                return

        # Update ancestor values
        for node in ancestors:
            idf_field = ref_graph.node[node]['data']
            idf_field.value = new_value

            # make a list of object lists to use later
            edge = ref_graph.edge[node][field._uuid]
            obj_list_set.update(edge['obj_list'])

        print('list of obj_lists: {}'.format(obj_list_set))

        # Update the IDF's reference dictionary for each obj_list
        for obj_list in obj_list_set:
            if new_value not in ref_lists[obj_list]:
                ref_lists[obj_list][new_value] = [(field._uuid, field)]
            else:
                try:
                    ref_lists[obj_list][new_value].append((field._uuid, field))
                except AttributeError:
                    ref_lists[obj_list][new_value] = [(field._uuid, field)]

            if len(ref_lists[obj_list][old_value]) <= 1:
                del ref_lists[obj_list][old_value]
            else:
                ref_lists[obj_list][old_value].remove((field._uuid, field))

        print('--------')
        pprint.pprint(self._ref_lists['ScheduleTypeLimitsNames'])
        print('--------')

    def connect_references(self):
        """Processes the reference graph to connect its nodes.
        """

        node_count = self._ref_graph.number_of_nodes()

        # Cycle through only nodes to avoid cycling through all objects
        for k, node in enumerate(self._ref_graph.nodes_iter(data=True)):

            try:
                field = node[1]['data']
                object_list_name = field.tags['object-list']

                # Ensure we have a list to simplify later operations
                if not isinstance(object_list_name, list):
                    object_list_name = [field.tags['object-list']]

                # Cycle through all class names in the object lists
                for cls_list in object_list_name:
                    ref_node = self._ref_lists[cls_list][field.value]
                    for ref_uuid, ref in ref_node:
                        self._ref_graph.add_edge(field._uuid,
                                                 ref_uuid,
                                                 obj_list=object_list_name)
                    yield math.ceil(50 + (100 * 0.5 * (k+1) / node_count))

            except (IndexError, KeyError) as e:
                continue

            yield math.ceil(50 + (100 * 0.5 * (k+1) / node_count))
