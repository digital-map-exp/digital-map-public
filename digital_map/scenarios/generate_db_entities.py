
from util.app_logger import get_my_logger, login_decorator
from util.app_list import compare_lists

from digital_map.model.digital_map_files import find_entity_types, find_entity_instances
from digital_map.database.digital_map_db_py2neo import DigitalMapDB_py2neo
from digital_map.database.digital_map_db_neo4j import DigitalMapDB_neo4j

logger = get_my_logger(__name__)

@login_decorator
def generate_db_entities(generated_database, files_path):

    input_db = DigitalMapDB_neo4j(generated_database)
    output_db = DigitalMapDB_py2neo(generated_database)

    # find entity types
    file_entity_types = find_entity_types(files_path)
    db_entity_types = input_db.find_entity_types()
    new_entity_types, same_entity_types, deleted_entity_types = \
        compare_lists(db_entity_types, file_entity_types)

    # add nodes for the new node type
    for entity_type in new_entity_types:
        entity_instances = find_entity_instances(files_path, entity_type)
        for entity_instance in entity_instances:
            output_db.create_entity_node(entity_instance)

    # delete nodes for the deleted node type
    for entity_type in deleted_entity_types:
        output_db.delete_entity_nodes(entity_type)

    # node type exists, check the node instances for add/delete/modify
    for entity_type in same_entity_types:
        file_entity_instances = find_entity_instances(files_path, entity_type)
        db_entity_instances = output_db.find_entity_instances(entity_type)

        same_instances, new_instances, updated_instances, deleted_instances = \
            compare_old_new(output_db, db_entity_instances, file_entity_instances)

        # add nodes
        for entity_instance in new_instances:
            output_db.create_entity_node(entity_instance)

        # delete nodes
        for entity_instance in deleted_instances:
            output_db.delete_entity_node(entity_type, entity_instance["entityID"])

        # modify nodes
        for entity_instance in updated_instances:
            output_db.modify_entity_node(entity_instance)

    input_db.close()

@login_decorator
def compare_old_new(output_db, db_entity_instances, file_entity_instances):

    new_members = []
    deleted_members = db_entity_instances
    same_members = []
    updated_members = []

    for new_member in file_entity_instances:
        label = new_member['entityType']
        entity_id = new_member['entityID']

        node = output_db.match_node(label, entity_id)

        if node is not None:
            nodes_same = are_nodes_same(node, new_member)
            if nodes_same is True:
                same_members.append(new_member)
            else:
                updated_members.append(new_member)
            deleted_members.remove(node)
        else:
            new_members.append(new_member)

    return same_members, new_members, updated_members, deleted_members

@login_decorator
def are_nodes_same(db_node, file_node):
    for x in file_node:
        if x == 'entityType' or file_node[x] == "":
            continue
        if db_node[x] != file_node[x]:
            return False
    return True

