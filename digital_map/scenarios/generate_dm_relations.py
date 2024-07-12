import os
import json

from util.app_logger import get_my_logger, login_decorator
from util.dir_util import copy_dir, del_dir, get_all_files

from digital_map.model.digital_map_files import find_all_entity_types, find_entity_instances
from digital_map.model.digital_map_files import generate_relations_file, find_json_file_on_subdirs
logger = get_my_logger(__name__)

@login_decorator
def generate_dm_relations(datetime_results_path, dm_directories):

    entity_types, entity_files  = find_all_entity_types(dm_directories['input']['knowledge']['entities'])

    # go through the list of files and generate relations from them
    file_list = get_all_files(dm_directories['input']['knowledge']['relations'])
    relations = []
    for file_name in file_list:
        with open(file_name) as fo:
            file_relations = json.load(fo)
            for relation in file_relations:
                relations.append(relation)

    for relation in relations:
        all_src_nodes = []
        all_dst_nodes = []
        relation_type = relation['type']
        src_type = relation['src_entity']
        dst_type = relation['dst_entity']
        if src_type not in entity_types or dst_type not in entity_types:
            continue

        # relationship type can be equal, contains or intersects
        correlation_logic = relation['correlation_logic']
        src_attr = [i.strip().strip('[').strip('[').strip().split('|')[0].strip() for i in relation['src_entity_attr'].split("&")]
        dst_attr = [i.strip().strip('[').strip('[').strip().split('|')[0].strip() for i in relation['dst_entity_attr'].split("&")]

        json_model_src = {}
        src_file = find_json_file_on_subdirs(dm_directories['input']['knowledge']['entities'], src_type)
        with open(src_file) as src_entity_file:
            json_model_src = json.load(src_entity_file)

        json_model_dst = {}
        dst_file = find_json_file_on_subdirs(dm_directories['input']['knowledge']['entities'], dst_type)
        with open(dst_file) as dst_entity_file:
            json_model_dst = json.load(dst_entity_file)

        if json_model_src is {}:
            logger.error("Model file for src cannot be found")
            continue

        if json_model_dst is {}:
            logger.error("Model file for dst cannot be found")
            continue

        attr_error = False
        attr_error_val = ""
        for attr in src_attr:
            if attr not in json_model_src[src_type]['properties']:
                    attr_error = True
                    attr_error_val=attr
            for attr in dst_attr:
                if attr not in json_model_dst[dst_type]['properties']:
                    attr_error = True
                    attr_error_val=attr
            if attr_error:
                logger.error("Attribute Error in relation: " + attr_error_val + " relation type: " + relation_type +
                             " source entity: " + src_type + " dest type: " + dst_type)
                continue

        all_src_nodes = find_entity_instances("data_generated/entities", src_type)
        if src_type != dst_type:
            all_dst_nodes = find_entity_instances("data_generated/entities", dst_type)
        else:
            all_dst_nodes = all_src_nodes

        rel_instances = []
        for src_node in all_src_nodes:
            src_flag = True
            for i in range(len(src_attr)):
                if src_attr[i].strip() not in src_node:
                    src_flag = False
                    break
            if not src_flag:
                continue
            for dst_node in all_dst_nodes:
                flag = True
                for i in range(len(src_attr)):
                    if dst_attr[i].strip() not in dst_node:
                        flag = False
                        break
                    if correlation_logic.lower() == 'equal' and src_node[src_attr[i]] != dst_node[dst_attr[i]]:
                        flag = False
                        break
                    elif correlation_logic.lower() == 'contains' and \
                            (src_node[src_attr[i]] != dst_node[dst_attr[i]] and
                                str(src_node[src_attr[i]]) not in str(dst_node[dst_attr[i]])):
                        flag = False
                        break
                    elif correlation_logic.lower() == 'intersect':
                        ins = []
                        if '[' in src_node[src_attr[i]] and '[' in dst_node[dst_attr[i]]:
                            ins = [i for i in eval(src_node[src_attr[i]]) if i in eval(dst_node[dst_attr[i]])]
                            if not ins:
                                flag = False
                                break
                        else:
                            if src_node[src_attr[i]] != dst_node[dst_attr[i]]:
                                flag = False
                                break
                if flag:
                    rel_instance = {
                        "src_entity": src_node['entityType'],
                        "src_entity_id": src_node['entityID'],
                        "type": relation['type'],
                        "dst_entity": dst_node['entityType'],
                        "dst_entity_id": dst_node['entityID']
                    }
                    rel_instances.append(rel_instance)

        if rel_instances:
            generate_relations_file(datetime_results_path,
                                    datetime_results_path + "/" + dm_directories['results']['relations'],
                                    src_type, relation_type, dst_type, rel_instances)

    del_dir(dm_directories['generated']['relations'])
    copy_dir(datetime_results_path + "/" + dm_directories['results']['relations'],
             dm_directories['generated']['relations'])