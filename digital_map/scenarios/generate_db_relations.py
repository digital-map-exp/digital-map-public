import logging

from util.app_logger import get_my_logger, login_decorator
from util.app_list import compare_lists

from digital_map.model.digital_map_files import find_relation_types, find_relation_instances
from digital_map.database.digital_map_db_py2neo import DigitalMapDB_py2neo
from digital_map.database.digital_map_db_neo4j import DigitalMapDB_neo4j

logger = get_my_logger(__name__)


@login_decorator
def generate_db_relations(generated_database, files_path):

    input_db = DigitalMapDB_neo4j(generated_database)
    output_db = DigitalMapDB_py2neo(generated_database)

    # find relation types
    file_relations_types = find_relation_types(files_path)
    db_relations_types = input_db.find_relation_types()
    new_relation_types, same_relation_types, deleted_relation_types = \
        compare_lists(db_relations_types, file_relations_types)

    # add relations for the new relation type
    for relation_type in new_relation_types:
        relation_instances = find_relation_instances(files_path, relation_type)
        for relation_instance in relation_instances:
            try:
                output_db.create_relation(relation_instance)
            except Exception as e:
                logger.error("ERROR: Failed to create relation:", e)

    # delete relations for the deleted relation type
    for relation_type in deleted_relation_types:
        relation_instances = input_db.find_relation_instances(relation_type[0], relation_type[1], relation_type[2])
        for relation_instance in relation_instances:
            try:
                output_db.delete_relation(relation_instance)
            except Exception as e:
                logger.error("ERROR: Failed to delete relation:", e)

    # relation type exists, check the relation instances for add/delete
    for relation_type in same_relation_types:
        file_relation_instances = find_relation_instances(files_path, relation_type)
        db_relation_instances = input_db.find_relation_instances(relation_type[0], relation_type[1], relation_type[2])

        same_instances, new_instances, deleted_instances = \
            compare_old_new(input_db, db_relation_instances, file_relation_instances)

        # add nodes
        for relation_instance in new_instances:
            try:
                output_db.create_relation(relation_instance)
            except Exception as e:
                logger.error("ERROR: Failed to create relation:", e)

        # delete nodes
        for relation_instance in deleted_instances:
            try:
                output_db.delete_relation(relation_instance)
            except Exception as e:
                logger.error("ERROR: Failed to delete relation:", e)

    input_db.close()

@login_decorator
def compare_old_new(input_db, db_relation_instances, file_relation_instances):

    new_relations = []
    deleted_relations = db_relation_instances
    same_relations = []

    for new_relation in file_relation_instances:
        src_entity = new_relation['src_entity']
        src_entity_id = new_relation['src_entity_id']
        relation_type = new_relation['type']
        dst_entity = new_relation['dst_entity']
        dst_entity_id = new_relation['dst_entity_id']

        relation_found = None
        for relation in db_relation_instances:
            src_entity_db = relation[0]
            src_id_db = relation[1]
            src_entity_id_db = relation[2]
            relation_type_db = relation[3]
            relation_id_db = relation[4]
            dst_entity_db = relation[5]
            dst_id_db = relation[6]
            dst_entity_id_db = relation[7]
            if (src_entity_db == src_entity) & (src_entity_id_db == src_entity_id) &\
                    (relation_type_db == relation_type) & \
                    (dst_entity_db == dst_entity) & (dst_entity_id_db ==dst_entity_id):
                relation_found = relation
#        relation = input_db.match_relation(src_entity, src_entity_id, relation_type, dst_entity, dst_entity_id)

        if relation_found is not None:
            same_relations.append(new_relation)
            deleted_relations.remove(relation_found)
        else:
            new_relations.append(new_relation)

    return same_relations, new_relations, deleted_relations

@login_decorator
def are_nodes_same(db_node, file_node):
    for x in file_node:
        if x == 'entityType' or file_node[x] == "":
            continue
        if db_node[x] != file_node[x]:
            return False
    return True

