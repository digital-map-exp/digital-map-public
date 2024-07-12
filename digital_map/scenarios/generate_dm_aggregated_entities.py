import os
import json

from util.app_logger import get_my_logger, login_decorator
from util.dir_util import copy_dir, del_dir, copy_files

from digital_map.model.digital_map_entity import DigitalMapEntity
from digital_map.model.digital_map_files import find_all_entity_types, find_entity_instances,generate_entity_file, \
    find_json_file_on_subdirs

logger = get_my_logger(__name__)

@login_decorator
def generate_dm_aggregated_entities(datetime_results_path, dm_directories):

    entity_types, entity_files = find_all_entity_types(dm_directories['input']['knowledge']['entities'])
    aggregation_types, aggregation_files = find_all_entity_types(dm_directories['input']['knowledge']['aggregations'])

    for aggregation_type in aggregation_types:
        if aggregation_type not in entity_types:
            logger.error("Aggregated Entity is not specified as entity: " + aggregation_type)

        aggregation_knowledge_file = aggregation_files[aggregation_type]
        entity_knowledge_file = entity_files[aggregation_type]

        if not aggregation_knowledge_file or not entity_knowledge_file:
            logger.error("Aggregation File cannot be found for this entity type: ", aggregation_type)
            continue

        with open(aggregation_knowledge_file) as fo:
            aggregation = json.load(fo)

            with open(entity_knowledge_file) as entity_file:
                json_model_entity = json.load(entity_file)

            entity = DigitalMapEntity(aggregation_type)
            entity.set_entity_model(json_model_entity[aggregation_type])
            entity.set_aggregation_model(aggregation)

            all_src_nodes = []
            all_dst_nodes = []

            src_type = aggregation[aggregation_type]['Rules']['src_entity']
            dst_type = aggregation[aggregation_type]['Rules']['dst_entity']
            if src_type not in entity_types or dst_type not in entity_types:
                logger.error("Aggregated Entity is not specified as entity: " + aggregation_type)
                continue

            # relationship type can be equal, contains or intersects
            correlation_logic = aggregation[aggregation_type]['Rules']['correlation_logic']
            src_attr = [i.strip().strip('[').strip('[').strip().split('|')[0].strip() for i in aggregation[aggregation_type]['Rules']['src_entity_attr'].split("&")]
            dst_attr = [i.strip().strip('[').strip('[').strip().split('|')[0].strip() for i in aggregation[aggregation_type]['Rules']['dst_entity_attr'].split("&")]

            src_file = find_json_file_on_subdirs(dm_directories['input']['knowledge']['entities'], src_type)
            with open(src_file) as src_entity_file:
                json_model_src = json.load(src_entity_file)
            dst_file = find_json_file_on_subdirs(dm_directories['input']['knowledge']['entities'], dst_type)
            with open(dst_file) as dst_entity_file:
                json_model_dst = json.load(dst_entity_file)

            attr_error = False
            attr_error_val = ""
            for attr in src_attr:
                if attr not in json_model_src[src_type]['properties']:
                    attr_error_val = attr
                    attr_error = True
            for attr in dst_attr:
                if attr not in json_model_dst[dst_type]['properties']:
                    attr_error_val = attr
                    attr_error = True
            if attr_error:
                logger.error("Attribute Error in aggregation: " + attr_error_val + " aggregation type: " + attr_error_val +
                             " source entity: " + src_type + " dest type: " + dst_type)
                continue

            all_src_nodes = find_entity_instances(dm_directories['generated']['entities'], src_type)
            if src_type != dst_type:
                all_dst_nodes = find_entity_instances(dm_directories['generated']['entities'], dst_type)
            else:
                all_dst_nodes = all_src_nodes

            aggr_instances = []
            for src_node in all_src_nodes:
                src_flag = True
                for i in range(len(src_attr)):
                    if src_attr[i].strip() not in src_node:
                        src_flag = False
                        break
                if not src_flag:
                    continue
                for dst_node in all_dst_nodes:
                    if (src_node['entityID'] == dst_node['entityID']):
                        continue
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
                                 str(dst_node[dst_attr[i]]) not in eval(src_node[src_attr[i]])):
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
                        aggr_instance = entity.generate_instance_aggregated(src_type, src_node, dst_type, dst_node)
                        aggr_instances.append(aggr_instance)

            if aggr_instances:
                # check if the entities file already exists
                entities_instances = find_entity_instances(dm_directories['generated']['entities'], aggregation_type)
                if entities_instances:
                    logger.error("NOT IMPLEMENTED")
                else:
                    # create a new file
                    entity_columns = entity.get_columns()
                    generate_entity_file(datetime_results_path, datetime_results_path + "/" +
                                         dm_directories['results']['aggregations'],
                                         entity.type, entity_columns, aggr_instances)

    del_dir(dm_directories['generated']['aggregations'])
    copy_dir(datetime_results_path + "/" + dm_directories['results']['aggregations'],
             dm_directories['generated']['aggregations'])
    copy_files(dm_directories['generated']['aggregations'], dm_directories['generated']['entities'])