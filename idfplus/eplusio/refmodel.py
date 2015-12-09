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
from whoosh.qparser import QueryParser

# Setup logging
log = logging.getLogger(__name__)


class ReferenceModel(object):
    """Wrapper around a dictionary and DiGraph that stores object references.
    """

    def __init__(self, outer):
        self._ref_graph = nx.DiGraph()
        self._idf = outer
        self._idd = None

    def set_idd(self, idd):
        """Sets the IDD file and takes care of some setup operations
        """

        self._idd = idd

    def _populate_ref_list(self):
        """Populates the reference list using the idf file
        """

        obj_lists = self._idd.object_lists
        self._ref_lists.update((k, dict()) for k in obj_lists.iterkeys())

    def reference_count(self, field):
        ref_graph = self._ref_graph
        try:
            ancestors = nx.ancestors(ref_graph, field.uuid)
            descendants = nx.descendants(ref_graph, field.uuid)
        except nx.exception.NetworkXError:
            # Doesn't exist in the network
            return -1
        else:
            if not ancestors or not descendants:
                return -1
        return len(ancestors) + len(descendants)

    def add_field(self, field, idd_obj_tags):
        """Adds a new field and takes care of the references

        :param field:
        :param idd_obj_tags:
        """

        tag_set = set(idd_obj_tags)
        ref_set = {'object-list', 'reference'}

        # We now want to add ALL fields
        # if (field and len(tag_set & ref_set) <= 0) or not field:
        #     return

        # print('add_field called for field: {}'.format(len(tag_set & ref_set)))
        # print('tag set: {}'.format(tag_set))
        # print('ref set: {}'.format(ref_set))

        # Add a node to the graph for the new field
        self._ref_graph.add_node(field.uuid, data=field)

        # Add new entries to the reference list for the new field
        if 'reference' in idd_obj_tags:

            # Ensure we have a list of object classes
            obj_list_names = idd_obj_tags['reference']
            if not isinstance(obj_list_names, list):
                obj_list_names = [idd_obj_tags['reference']]

            # Save the node in the idf file's reference list
            for object_list in obj_list_names:
                id_tup = (field.uuid, field)
                try:
                    self._ref_lists[object_list][field.value].append(id_tup)
                except (AttributeError, KeyError):
                    self._ref_lists[object_list][field.value] = [id_tup]

        # Connect the reference to other existing references
        self.update_references(field)

    # def add_reference(self, field, cls_list, object_list_name):
    #     """Creates the specified reference.
    #     :param field:
    #     :param cls_list:
    #     :param object_list_name:
    #     """
    #
    #     ref_node = self._ref_lists[cls_list][field.value]
    #     for ref_uuid, ref in ref_node:
    #         self._ref_graph.add_edge(field._uuid,
    #                                  ref_uuid,
    #                                  obj_list=object_list_name)

    def remove_references(self, objects_to_delete):

        obj_class = objects_to_delete[0].obj_class
        idd_obj = self._idd[obj_class]

        # Delete objects and update reference list
        for obj in objects_to_delete:
            field_uuids = [field._uuid for field in obj]
            self._ref_graph.remove_nodes_from(field_uuids)

            # Also update reference list if required
            for j, field in enumerate(obj):
                tags = idd_obj[field.key].tags

                if 'reference' in tags:
                    object_list_names = tags['reference']
                    if not isinstance(object_list_names, list):
                        object_list_names = [tags['reference']]
                    for object_list in object_list_names:
                        tup_list = self._ref_lists[object_list][field.value]
                        for id_tup in tup_list:
                            if id_tup[0] == field._uuid:
                                # Should only be one so it's ok to modify list here!
                                tup_list.remove(id_tup)

    def update_reference(self, obj_class, index, new_values):
        """Updates the specified reference.
        """

        pass

    def delete_reference(self):
        """Deletes the specified reference.
        """
        print('del called')
        # pass

    def update_references(self, field):
        """Updates the reference graph for the specified field

        :param field:
        """

        # Continue only if this field references an object from an object-list
        object_list_name = field.tags.get('object-list', '')
        if not object_list_name:
            return

        graph = self._ref_graph
        # node_count = graph.number_of_nodes()

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
                        # print('removing old ref')

            except (IndexError, KeyError):
                continue

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

        # print('--------')
        # pprint.pprint(ref_lists['ScheduleTypeLimitsNames'])

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

        # print('list of obj_lists: {}'.format(obj_list_set))

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

        # print('--------')
        # pprint.pprint(self._ref_lists['ScheduleTypeLimitsNames'])
        # print('--------')

    def connect_references(self):
        """Processes the entire reference graph to connect its nodes. Yield progress.
        """

        index = self._idf.index
        parser = QueryParser("value", index.schema)
        obj_list_length = self._idd.object_list_length
        ref_set = {'object-list', 'reference'}
        k = 0

        # Open the searcher
        with index.searcher() as searcher:

            # Loop through all object classes in the object-lists
            for object_list_name, object_list_set in self._idd.object_lists.iteritems():
                object_list = list(object_list_set)

                # Loop through all classes in this object-list
                for object_class in object_list:
                    idd_object = self._idd.get(object_class)

                    # Loop through all objects in this class
                    for obj in self._idf.get(object_class, []):

                        # Loop through all fields in this object
                        for i, field in enumerate(obj):
                            key = idd_object.key(i)
                            idd_obj_tags = set(idd_object[key].tags)

                            # If this field is a reference-type then connect nodes
                            if field and field.value and len(idd_obj_tags & ref_set) > 0:
                                my_query = parser.parse('"{}"'.format(field.value.lower()))
                                results = searcher.search(my_query, limit=None)

                                for hit in results:
                                    self._ref_graph.add_edge(field.uuid, hit['uuid'],
                                                             obj_list=object_list)

                    yield math.ceil(50 + (100 * 0.5 * (k+1) / obj_list_length))
                    k += 1
