

import json
from neo4j import GraphDatabase
from neo4j.graph import Node, Relationship

from util.app_logger import login_decorator
from util.app_logger import get_my_logger
from util.database import DatabaseInfo

logger = get_my_logger(__name__)

# Class for accessing the Digital Map Database for read
class DigitalMapDB_neo4j:

    @login_decorator
    def __init__(self, database_info: DatabaseInfo):
        self.__name = database_info.name
        self.__uri = database_info.uri
        self.__user = database_info.user
        self.__password = database_info.password
        self.__driver = None

        try:
            self.__driver = GraphDatabase.driver(self.__uri, auth=(self.__user, self.__password))
        except Exception as e:
            logger.error("ERROR: Failed to create the driver:", e)

    @login_decorator
    def close(self):
        if self.__driver is not None:
            try:
                self.__driver.close()
            except Exception as e:
                logger.error("ERROR: Failed to close the driver:", e)

    # Returns all distinct labels in the database
    @login_decorator
    def find_entity_types(self):
        entity_types = []

        try:
            session = self.__driver.session()
            result = session.read_transaction(self._find_and_return_distinct_labels)
            for row in result:
                entity_types += (row.value())
                logger.debug("Found distinct label: {row}".format(row=row.value()))

        except Exception as e:
            logger.error("ERROR: Failed to read transaction for distinct labels:", e)

        return entity_types

    @login_decorator
    def execute_query(self, query_string):
        entities = []
        try:
            session = self.__driver.session()
            result = session.read_transaction(self._execute_query, query_string)
            for row in result:
                row_value = row.value()._properties
                entities.append(row_value)

        except Exception as e:
            logger.error("ERROR: Failed to execute query:", e)

        return entities

    @login_decorator
    def execute_query_entity(self, query_string):
        entities = []
        columns = []
        entity_type = None
        try:
            session = self.__driver.session()
            result = session.read_transaction(self._execute_query, query_string)
            for row in result:
                entity = {}
                row_keys = row.keys()
                columns = row_keys
                for row_key in row_keys:
                    if row_key == "entityType":
                        entity_type = row[row_key]
                    entity[row_key] = row[row_key]
                entities.append(entity)

        except Exception as e:
            logger.error("ERROR: Failed to execute query:", e)

        return columns, entity_type, entities

    @login_decorator
    def execute_query_relation(self, query_string):
        relations = []
        src_type = None
        dst_type = None
        relation_type = "health"

        try:
            session = self.__driver.session()
            result = session.read_transaction(self._execute_query, query_string)
            for row in result:
                relation = {}
                row_keys = row.keys()
                columns = row_keys
                for row_key in row_keys:
                    if row_key == "src_entity":
                        src_type = row[row_key]
                    if row_key == "dst_entity":
                        dst_type = row[row_key]
                    relation[row_key] = row[row_key]
                relations.append(relation)

        except Exception as e:
            logger.error("ERROR: Failed to execute query:", e)
            logger.error("ERROR for Query String: ", query_string)

        return src_type, relation_type, dst_type, relations

    @staticmethod
    @login_decorator
    def _execute_query(tx, query_string):
        query = query_string
        try:
            result = tx.run(query)
            return [row for row in result]
        except Exception as e:
            logger.error("ERROR: Failed to execute query:", e)
            return []

    @staticmethod
    @login_decorator
    def _find_and_return_distinct_labels(tx):
        query = (
            "MATCH (n) RETURN distinct labels(n)"
        )
        result = tx.run(query)
        return [row for row in result]

    # Returns all entities for label=entity_type
    @login_decorator
    def find_entity_instances(self, entity_type):

        entities = []

        try:
            session = self.__driver.session()
            result = session.read_transaction(self._find_and_return_entities, entity_type)
            for row in result:
                #entities.append(row.value())
                row_value = row.value()._properties
                entities.append(row_value)
                #logger.debug("Found entity: {row}".format(row=row))
                #logger.debug("row.value: {row}".format(row=row.value()))
                #logger.debug("keys: {row}".format(row=row.value().keys()))

        except Exception as e:
            logger.error("ERROR: Failed to read transaction for entities:", e)

        return entities

    @staticmethod
    @login_decorator
    def _find_and_return_entities(tx, label):
        query = (
            "MATCH (p:`" + label + "`) "
            "RETURN p"
        )
        result = tx.run(query, label=label)
        return [row for row in result]

    # find all the relations n1-r-n2 where the combination of type (label) of n1 and type
    # (label) of n2 and type of r is unique
    @login_decorator
    def find_relation_types(self):
        relation_types = set(())

        try:
            session = self.__driver.session()
            results = session.read_transaction(self._find_and_return_relations)
            for record in results:
                # TODO could get these Nodes from the Relationship
                n1: Node = record.get("n1")
                #logger.debug("Node n1: "+n1.__str__())
                n1_label = list(n1.labels)[0]

                n2: Node = record.get("n2")
                #logger.debug("Node n2: "+n2.__str__())
                n2_label = list(n2.labels)[0]

                r: Relationship = record.get("r")
                r_tuple = (n1_label, r.type, n2_label)
                relation_types.add(r_tuple)
                #logger.debug("New relation: {0} ".format(r_tuple))
            logger.debug("New UNIQUE relation: {0} ".format(relation_types))

        except Exception as e:
            logger.error("ERROR: Failed to read transaction for relation types:", e)

        return list(relation_types)

    @staticmethod
    @login_decorator
    def _find_and_return_relations(tx):
        query = (
            "MATCH (n1)-[r]->(n2) RETURN n1, r, n2"
        )
        result = tx.run(query)
        return [row for row in result]

    # Returns all relations instances for a relations type
    @login_decorator
    def find_relation_instances(self, source_entity_type, relation_type, dest_entity_type):

        relations = []

        try:
            session = self.__driver.session()
            n1_type = source_entity_type
            n2_type = dest_entity_type
            r_type = relation_type
            result = session.read_transaction(self._find_and_return_specific_relations,
                                              source_entity_type, relation_type, dest_entity_type)
            for row in result:
                # TODO could get these Nodes from the Relationship
                n1: Node = row.get("n1")
                #logger.debug("Node n1: "+n1.__str__())
                n1_type = list(n1.labels)[0]
                n1_id = n1.id
                n1_entityID = n1.get('entityID')

                n2: Node = row.get("n2")
                #logger.debug("Node n2: "+n2.__str__())
                n2_type = list(n2.labels)[0]
                n2_id = n2.id
                n2_entityID = n2.get('entityID')

                r: Relationship = row.get("r")
                #logger.debug("Relationship r: "+ r.__str__())
                r_type = r.type
                r_id = r.id

                r_tuple = (n1_type, n1_id, n1_entityID, r_type, r.id, n2_type, n2_id, n2_entityID)
                relations.append(r_tuple)

        except Exception as e:
            logger.error("ERROR: Failed to read transaction for relation instance:", e)

        return relations

    @staticmethod
    @login_decorator
    def _find_and_return_specific_relations(tx, n1_type, r_type, n2_type):
        query = (
            "MATCH (n1:`" + n1_type + "`)-[r:`" + r_type + "`]->(n2:`" + n2_type + "`) RETURN n1, r, n2"
        )
        result = tx.run(query)
        return [row for row in result]

    @login_decorator
    def match_relation(self, src_entity, src_entity_id, relation_type, dst_entity, dst_entity_id):
        session = self.__driver.session()
        result = session.read_transaction(self._match_relation, src_entity, src_entity_id, relation_type, dst_entity, dst_entity_id)

        for row in result:
            n1: Node = row.get("n1")
            n1_type = list(n1.labels)[0]
            n1_id = n1.id

            n2: Node = row.get("n2")
            n2_type = list(n2.labels)[0]
            n2_id = n2.id

            r: Relationship = row.get("r")
            r_type = r.type
            r_id = r.id

            r_tuple = (n1_type, n1_id, r_type, r_id, n2_type, n2_id)
            return r_tuple

        return None

    @staticmethod
    @login_decorator
    def _match_relation(tx, src_entity, src_entity_id, relation_type, dst_entity, dst_entity_id):

        query = "MATCH (n1:`" + src_entity + "`)-[r:`" + relation_type + "`]->(n2:`" + dst_entity + \
                "`) WHERE n1.entityID = '" + src_entity_id + "'and n2.entityID = '" + dst_entity_id + \
                "' RETURN n1, r, n2"

        result = tx.run(query)
        return [row for row in result]

    @login_decorator
    def generate_entity_node(self, entity_instance):
        label = entity_instance['entityType']
        node_id = entity_instance['entityID']

        #remove these 2 from the properties to be able to create the string and decide where ' is needed
        #remove properties without value
        columns = []
        for column in entity_instance:
            if entity_instance[column] == "":
                columns.append(column)

        for column in columns:
            del entity_instance[column]

        node_properties = self._create_query_string(entity_instance)
        print(node_properties)

        try:
            session = self.__driver.session()
            result = session.write_transaction(self._create_node, label, node_properties)
            logger.debug("Node created: " + result)

        except Exception as e:
            logger.error("ERROR: Failed to write transaction for create node:", e)

    @staticmethod
    @login_decorator
    def _create_node(tx, label, properties):
        query = (
            "CREATE (n:$label $properties) RETURN n"
        )
        result = tx.run(query, label=label, properties=properties)
        record = result.single()
        return record["node_id"]

    def _create_query_string(self, entity_instance):

        node_properties = json.dumps(entity_instance)
        return node_properties

    def _create_query_string2(self, entity_instance):

        node_properties = "{"
        no_properties = len(entity_instance)
        for index, column in enumerate(entity_instance, start=1):
            node_properties += column + ":" + str(entity_instance[column])
            if (index < no_properties):
                node_properties += ", "

        node_properties += "}"
        return node_properties