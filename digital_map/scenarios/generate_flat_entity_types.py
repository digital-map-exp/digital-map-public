import json

from util.app_logger import get_my_logger, login_decorator
from util.dir_util import create_dir, del_dir, copy_dir
from util.dir_util import exists_path, get_all_files
from util.dir_util import create_dir, del_dir, copy_dir, create_dirs

logger = get_my_logger(__name__)

@login_decorator
def generate_flat_entity_types(dm_directories):
    target_entities_knowledge = dm_directories['input']['knowledge']['entities']
    source_entities_knowledge = dm_directories['input']['knowledge']['entities_inheritance']

    abstract_entities = {}
    concrete_entities = {}
    all_entities = {}
    file_paths = {}
    relative_file_path = ""

    entity_model_file_list = get_all_files(source_entities_knowledge)
    for entity_model_file_name in entity_model_file_list:
        try:
            with open(entity_model_file_name) as entity_file:
                json_model_data = json.load(entity_file)
        except Exception as e:
            logger.error("ERROR: find_digital_map_entities:", e)
            logger.error("Failed to read entity file: {}".format(entity_model_file_name))

        for entity_type in json_model_data:
            json_entity_data_model = json_model_data[entity_type]
            # Check if abstract
            if ('isAbstract' in json_entity_data_model) and (json_entity_data_model['isAbstract'] == "yes"):
                abstract_entities[entity_type] = json_entity_data_model
                all_entities[entity_type] = json_entity_data_model

            # Check if it inherits abstract
            else:
                concrete_entities[entity_type] = json_entity_data_model
                all_entities[entity_type] = json_entity_data_model
                file_paths[entity_type] = entity_model_file_name


    for concrete_entity_type in concrete_entities:
        concrete_entity_json = concrete_entities[concrete_entity_type]

        generated_entities = {}

        new_properties = {}

        top_parent_json = {}
        top_parent = ""
        parents = {}

        top_parent_json = concrete_entity_json
        i = 0
        while 'parent' in top_parent_json:
            parent = top_parent_json['parent']
            parents[i] = parent
            top_parent = parent
            top_parent_json = all_entities[parent]
            i += 1

        while i != 0:
            i -= 1
            parent = parents[i]
            parent_json = all_entities[parent]
            properties = parent_json["properties"]
            for property in properties:
                new_properties[property] = properties[property]

        if 'properties' in concrete_entity_json:
            for property in concrete_entity_json["properties"]:
                new_properties[property] = concrete_entity_json["properties"][property]

        generated_entity = {}
        generated_entity['layer'] = concrete_entity_json["layer"]
        generated_entity['sublayer'] = concrete_entity_json["sublayer"]

        if not top_parent:
            generated_entity["topologyRole"] = "none"
        elif top_parent == 'IETFNetwork' or top_parent == 'network':
            generated_entity["topologyRole"] = "network"
        elif top_parent == 'IETFNode' or top_parent == 'node':
            generated_entity["topologyRole"] = "node"
        elif top_parent == 'IETFTerminationPoint' or top_parent == 'termination-point':
            generated_entity["topologyRole"] = "termination-point"
        elif top_parent == 'IETFLink' or top_parent == 'link':
            generated_entity["topologyRole"] = "link"
        else:
            generated_entity["topologyRole"] = "none"

        if "key" in top_parent_json:
            generated_entity['key'] = top_parent_json["key"]
        else:
            generated_entity['key'] = concrete_entity_json["key"]
        generated_entity['properties'] = new_properties
        generated_entities[concrete_entity_type] = generated_entity

        # save in the file on knowledge/entities
        file_path = file_paths[concrete_entity_type]
        relative_file_path = file_paths[concrete_entity_type].replace(source_entities_knowledge, "")
        new_file_path = target_entities_knowledge + relative_file_path
        create_dirs(new_file_path)

        jsonString = json.dumps(generated_entities)

        jsonFile = open (new_file_path, "w")
        jsonFile.write(jsonString)
        jsonFile.close()
