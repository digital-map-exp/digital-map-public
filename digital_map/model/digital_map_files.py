
import csv
import random
import pandas as pd

from util.app_logger import get_my_logger, login_decorator
from util.dir_util import create_dir, get_files, is_file, get_all_files, get_file_name, exists_path

logger = get_my_logger(__name__)


# generate entity csv file from intent instances
@login_decorator
def generate_entity_file(base_path, entity_path, entity_type, entity_columns, entity_instances):
    # Create entities dir if not already created
    create_dir(base_path)
    create_dir(entity_path)

    file_name = entity_path + "/" + entity_type + '.csv'
    file_exists = False
    if exists_path(file_name) and is_file(file_name):
        file_exists = True

    # create a separate csv file for each entity type
    csvfile = open(file_name, 'a', newline='')

    with csvfile:
        writer = csv.writer(csvfile)
        if not file_exists:
            writer.writerow(entity_columns)

        for entity_instance in entity_instances:
            values = []
            for entity_column in entity_columns:
                try:
                    if entity_column in entity_instance:
                        column_value = entity_instance[entity_column]
                    else:
                        column_value = [""]
                    values.append(column_value)
                except Exception as e:
                    logger.error("ERROR: Column not found ", e)
                    logger.error("For Entity:Column: " + entity_type + ":" + entity_column)

            writer.writerow(values)

# generate entity csv file from intent instances
@login_decorator
def generate_relations_file(base_path, relations_path, src_type, relation_type, dst_type, relations_instances):
    # Create entities dir if not already created
    create_dir(base_path)
    create_dir(relations_path)

    file_name = relations_path + "/" + src_type + "-" + relation_type + "-" + dst_type + ".csv"
    file_exists = False
    if exists_path(file_name) and is_file(file_name):
        file_exists = True

    # create a separate csv file for each entity type
    csvfile = open(file_name, 'a', newline='')

    with csvfile:
        writer = csv.writer(csvfile)
        columns = ['src_entity', 'src_entity_id', 'type', 'dst_entity', 'dst_entity_id']
        if not file_exists:
            writer.writerow(columns)

        for relations_instance in relations_instances:
            values = []
            for column in columns:
                values.append(relations_instance[column])
            writer.writerow(values)

# Find entity types based on the file names on the specified path
@login_decorator
def find_entity_types(path):
    entity_types = []
    node_files = get_files(path)
    for node_file in node_files:
        entity_type = node_file.split('.')[0]
        entity_types.append(entity_type)
    return entity_types

# Find entity types and full paths based file names on the specified path, including subdirectories
@login_decorator
def find_all_entity_types(path):
    entity_types = []
    entity_file_info = {}
    entity_files = get_all_files(path)
    for entity_file in entity_files:
        file_name = get_file_name(entity_file)
        entity_type = file_name.split('.')[0]
        entity_types.append(entity_type)
        entity_file_info[entity_type] = entity_file
    return entity_types, entity_file_info

def find_json_file_on_subdirs(path, name):
    all_files = get_all_files(path)
    for this_file in all_files:
        this_file_name = get_file_name(this_file)
        base_file_name = this_file_name.split('.')[0]
        if base_file_name == name:
            return this_file

    return None

# Returns all entities for the specified entity type in the file on the specified path
@login_decorator
def find_entity_instances(path, entity_type):
    entity_instances = []
    node_file = entity_type + ".csv"
    file_name = path + "/" + node_file
    if is_file(file_name):
        real_nodes = pd.read_csv(file_name)
        real_nodes = real_nodes.fillna('')
        data_columns = real_nodes.columns.values
        for index, row in real_nodes.iterrows():
            node = {}
            for column in data_columns:
                node[column] = row[column]
            entity_instances.append(node)

    return entity_instances

# Find relations types based on the file names on the specified path
@login_decorator
def find_relation_types_old(path):
    relations_types = []
    relations_files = get_files(path)
    for relations_file in relations_files:
        relation_type = relations_file.split('.')[0]
        relation_type_split = relation_type.split('-')
        src_entity = relation_type_split[0]
        relation_type = relation_type_split[1]
        dst_entity = relation_type_split[2]
        relation_set = (src_entity, relation_type, dst_entity)
        relations_types.append(relation_set)
    return relations_types

# Find relations types based on the file names on the specified path
@login_decorator
def find_relation_types(path):
    relations_types = []
    relations_files = get_files(path)
    for relations_file in relations_files:

        # Get the file and columns
        file_name = path + "/" + relations_file

        if is_file(file_name):
            src_entity = ""
            dst_entity = ""
            relation_type = ""

            real_nodes = pd.read_csv(file_name, nrows=1)
            real_nodes = real_nodes.fillna('')
            columns = real_nodes.columns.values

            for index, row in real_nodes.iterrows():
                for column in columns:
                    # Get the first value of source_entity column, all should be the same
                    if column == 'src_entity':
                        src_entity = row[column]
                    # Get the first value of dst_entity column, all should be the same
                    elif column == "dst_entity":
                        dst_entity = row[column]
                    # Get the relationship type
                    elif column == "type":
                        relation_type = row[column]

                relation_set = (src_entity, relation_type, dst_entity)
                relations_types.append(relation_set)
    return relations_types
# Returns all entities for the specified entity type in the file on the specified path
@login_decorator
def find_relation_instances(path, relation_type):
    entity_instances = []
    node_file = relation_type[0] + "-" + relation_type[1]  + "-" + relation_type[2] + ".csv"
    file_name = path + "/" + node_file
    if is_file(file_name):
        real_nodes = pd.read_csv(file_name)
        real_nodes = real_nodes.fillna('')
        data_columns = real_nodes.columns.values
        for index, row in real_nodes.iterrows():
            node = {}
            for column in data_columns:
                node[column] = row[column]
            entity_instances.append(node)
    return entity_instances