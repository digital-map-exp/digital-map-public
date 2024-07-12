

import json
import logging

from py2neo import Graph, Node, Relationship, NodeMatcher, Subgraph

from util.app_logger import login_decorator
from util.app_logger import get_my_logger
from util.database import DatabaseInfo

logger = get_my_logger(__name__)

# Class for accessing the Digital Map Database for write, there were some problems with tstring using the GraphDatabase
class DigitalMapDB_py2neo:

    @login_decorator
    def __init__(self, database_info: DatabaseInfo):
        self.__name = database_info.name
        self.__uri = database_info.uri
        self.__user = database_info.user
        self.__password = database_info.password
        self.__graph = None

        try:
            self.__graph = Graph(self.__uri, auth=(self.__user, self.__password), max_age=360000)

        except Exception as e:
            logger.error("ERROR: Failed to create the Graph:", e)

    @login_decorator
    def create_entity_node(self, entity_instance):
        label = entity_instance['entityType']
        entity_id = entity_instance['entityID']

        node = Node(label, entityID=entity_id)

        for column in entity_instance:
            if entity_instance[column] == "":
                continue
            node[column] = entity_instance[column]

        graph_nodes = []
        graph_nodes.append(node)
        graph_nodes = Subgraph(graph_nodes)
        self.__graph.create(graph_nodes)
        logger.info("NODE CREATED: " + label + " : " + entity_id)

    @login_decorator
    def delete_entity_node(self, entity_type, entity_id):
        matcher = NodeMatcher(self.__graph)
        node = matcher.match(entity_type, entityID=entity_id).first()
        subgraph_nodes = []
        subgraph_nodes.append(node)
        nodes = Subgraph(subgraph_nodes)
        self.__graph.delete(nodes)
        logger.info("NODE DELETED: " + entity_type + " : " + entity_id)

    @login_decorator
    def delete_entity_nodes(self, entity_type):
        matcher = NodeMatcher(self.__graph)
        nodes = matcher.match(entity_type)
        subgraph_nodes = []
        for node in nodes:
            subgraph_nodes.append(node)
            logger.info("NODE TO DELETE: " + entity_type + " : " + node['entityID'])
        nodes = Subgraph(subgraph_nodes)
        self.__graph.delete(nodes)

    @login_decorator
    def find_entity_instances(self, entity_type):
        matcher = NodeMatcher(self.__graph)
        nodes = list(matcher.match(entity_type))
        return nodes

    @login_decorator
    def match_node(self, entity_type, entity_id):
        matcher = NodeMatcher(self.__graph)
        node = matcher.match(entity_type, entityID=entity_id).first()
        return node

    @login_decorator
    def modify_entity_node(self, entity_instance):
        label = entity_instance['entityType']
        entity_id = entity_instance['entityID']

        node = Node(label, entityID=entity_id)

        for column in entity_instance:
            if entity_instance[column] == "":
                continue
            node[column] = entity_instance[column]

        graph_nodes = []
        graph_nodes.append(node)
        graph_nodes = Subgraph(graph_nodes)
        self.__graph.merge(graph_nodes, label, 'entityID')
        logger.info("NODE MODIFIED: " + label + " : " + entity_id)

    @login_decorator
    def create_relation(self, relation_instance):
        src_entity = relation_instance['src_entity']
        src_entity_id = relation_instance['src_entity_id']
        relation_type = relation_instance['type']
        dst_entity = relation_instance['dst_entity']
        dst_entity_id = relation_instance['dst_entity_id']

        src_node = self.match_node(src_entity, src_entity_id)
        dst_node = self.match_node(dst_entity, dst_entity_id)

        rela = Relationship(src_node, relation_type, dst_node)
        graph_relationships = []
        graph_relationships.append(rela)
        subgraph = Subgraph(relationships=graph_relationships)
        self.__graph.create(subgraph)
        logger.info("RELATIONSHIP CREATED: " + src_entity + ":" + src_entity_id +
                    "-" + relation_type + "-" + dst_entity + ":" + dst_entity_id)

    @login_decorator
    def delete_relation(self, relation_instance):
        src_entity = relation_instance[0]
        src_id = relation_instance[1]
        src_entity_id = relation_instance[2]
        relation_type = relation_instance[3]
        rel_id = relation_instance[4]
        dst_entity = relation_instance[5]
        dst_id = relation_instance[6]
        dst_entity_id = relation_instance[6]
        # 7 is for entityID
        query = "MATCH (a:" + src_entity + ")-[r:" + relation_type + "]->(b:" + dst_entity + ") WHERE ID(r) = $x DELETE r"
        self.__graph.run(query,x=rel_id)
        logger.info("RELATIONSHIP DELETED: " + src_entity + ":" + str(src_entity_id) +
                    "-" + relation_type + "-" + dst_entity + ":" + str(dst_entity_id))
        logger.info("QUERY: " + query)

