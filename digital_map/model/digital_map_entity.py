import json
import requests
import re
from jsonpath_ng.ext import parse

from util.app_logger import login_decorator
from util.app_logger import get_my_logger

from util.external_system import ExternalSystemInfo
from util.dir_util import exists_path, get_all_files
from util.import_code import import_code

from config.config import dm_kb_entity_topology_roles

logger = get_my_logger(__name__)


# find entities from the model file, allows either 1 or multiple entities being defined in the entities knowledge file
# generate DigitalMapEntity instances with mapping for list of external systems: devices, controllers, etc

@login_decorator
def find_digital_map_entities(external_system_list, knowledge_entities_path, knowledge_mapping_path):
    entity_model_file_list = get_all_files(knowledge_entities_path)
    entities = []
    for entity_model_file_name in entity_model_file_list:
        try:
            with open(entity_model_file_name) as entity_file:
                json_model_data = json.load(entity_file)
        except Exception as e:
            logger.error("ERROR: find_digital_map_entities:", e)
            logger.error("Failed to read entity file: {}".format(entity_model_file_name))

        for entity_type in json_model_data:
            #set entity model
            entity = DigitalMapEntity(entity_type)
            json_entity_data_model = json_model_data[entity_type]
            entity.set_entity_model(json_entity_data_model)

            # set mapping  model for all external systems
            for external_system_info in external_system_list:
                vendor = external_system_info.sys_vendor
                sys_type = external_system_info.sys_type
                software_version = external_system_info.software_version
                entity_mapping_file_name = \
                    knowledge_mapping_path + "/" + vendor + "/" + sys_type + \
                    "/" + software_version + "/" + entity_type + ".json"
                if exists_path(entity_mapping_file_name):
                    with open(entity_mapping_file_name) as entity_mapping_file:
                        json_mapping_data = json.load(entity_mapping_file)
                        json_mapping_data_model = json_mapping_data[entity_type]
                        entity.add_entity_mapping_model(vendor, sys_type, software_version,
                                                        json_mapping_data_model)
                else:
                    logger.debug(
                        "Mapping File {0} does not exist for external system type {1} vendor {2} software version {3}".
                            format(entity_mapping_file_name, sys_type, vendor, software_version))
        entities.append(entity)

    return entities

@login_decorator
def find_digital_map_entities_db_kb(external_system_list, dm_kb_api_config, headers_config):
    entities = []
    entity_bulk_uri = dm_kb_api_config["dm_kb_api_base_url"] + dm_kb_api_config["dm_kb_api_entities_url"]
    bulk_resp = requests.get(entity_bulk_uri, headers=headers_config["json_headers"])
    if bulk_resp.status_code == 200:
        entity_model_name_list = json.loads(bulk_resp.content)
        for entity_model_name in entity_model_name_list:
            entity_model_resp = requests.get(entity_bulk_uri + "/" + entity_model_name, headers=headers_config["json_headers"])
            if entity_model_resp.status_code == 200:
                entity_model_data = json.loads(entity_model_resp.content)
                json_model_data = generate_entity_json_model_data(entity_model_data)
                for entity_type in json_model_data:
                    #set entity model
                    entity = DigitalMapEntity(entity_type)
                    json_entity_data_model = json_model_data[entity_type]
                    entity.set_entity_model(json_entity_data_model)

                    # set mapping model for all external systems
                    for external_system_info in external_system_list:
                        vendor = external_system_info.sys_vendor
                        sys_type = external_system_info.sys_type
                        software_version = external_system_info.software_version
                        mapping_uri = "{}/{}/mapping/{}/{}/{}".format(entity_bulk_uri, entity_model_name, vendor, sys_type, software_version)
                        mapping_model_resp = requests.get(mapping_uri, headers=headers_config["json_headers"])
                        if mapping_model_resp.status_code == 200:
                            mapping_data = json.loads(mapping_model_resp.content)
                            json_mapping_data = generate_mapping_json_model_data(mapping_data)["data"]
                            json_mapping_data_model = json_mapping_data[entity_type]
                            entity.add_entity_mapping_model(vendor, sys_type, software_version,
                                                            json_mapping_data_model)

                    entities.append(entity)

    return entities

#------------Generate Digital Map Knowledge Base data model based on KB stored in DB-------------
@login_decorator
def generate_entity_json_model_data(input):
    output = {}
    parent = input["parent"]
    input_properties = input["properties"]
    output_properties = {}
    keys = []
    # Generate subservice properties
    for input_prop in input_properties:
        output_prop_key = input_prop["name"]
        output_prop_value = {}
        output_prop_value["Description"] = input_prop["description"]
        output_prop_value["Type"] = input_prop["type"]
        output_properties[output_prop_key] = output_prop_value
        if input_prop["isKey"] == "true":
            keys.append(output_prop_key)
        
    model_data = {}
    model_data["layer"] = input["layer"]
    model_data["sublayer"] = input["sublayer"]
    if parent in dm_kb_entity_topology_roles:    
        model_data["topologyRole"] = dm_kb_entity_topology_roles[parent]
    else:
        model_data["topologyRole"] = "none"
    model_data["key"] = keys
    model_data["properties"] = output_properties

    data_key = input["name"]
    output[data_key] = model_data
    return output

@login_decorator
def generate_aggregation_json_model_data(input):
    output = {}
    output_properties = {}
    output_rules = {}
    build_method_key = ""
    if "jsonMethod" in input:
        build_method_key = "jsonMethod"
    elif "queryMethod" in input:
        build_method_key = "queryMethod"

    # Generate aggregation properties
    input_properties = input[build_method_key]["properties"]
    for input_prop in input_properties:
        output_prop_key = input_prop["name"]
        output_prop_value = {}
        output_prop_func = input_prop["function"]
        output_prop_func_key = output_prop_func
        if output_prop_func == "compute" or output_prop_func == "value":
            output_prop_value[output_prop_func_key] = input_prop["input"]
        elif output_prop_func == "src" or output_prop_func == "dst":
            output_prop_func_key = "{}_entity_attr".format(output_prop_func)
            output_prop_value[output_prop_func_key] = get_aggregation_entity_attr(input_prop["input"])
        output_properties[output_prop_key] = output_prop_value

    # Generate aggregation rules
    input_rules = input[build_method_key]["rules"]
    condition_attrs = get_condition_attrs(input_rules["condition"], "Equal")
    output_rules["src_entity"] = input_rules["src"]
    output_rules["src_entity_attr"] = condition_attrs["src_entity_attr"]
    output_rules["dst_entity"] = input_rules["dst"]
    output_rules["dst_entity_attr"] = condition_attrs["dst_entity_attr"]
    output_rules["correlation_logic"] = "Equal"  # All existing aggregations are with "Equal" correlation logic for now, to be extended

    model_data = {}
    model_data["Build_Mode"] = input["buildMode"]
    model_data["Build_Method"] = input["buildMethod"]
    model_data["Properties"] = output_properties
    model_data["Rules"] = output_rules

    data_key = input["name"]
    output[data_key] = model_data
    return output

@login_decorator
def generate_relation_json_model_data(input):
    output = {}
    condition_attrs = get_condition_attrs(input["condition"], "Equal")
    type = input["type"]
    
    output["src_entity"] = input["src"]
    output["src_entity_attr"] = condition_attrs["src_entity_attr"]
    output["dst_entity"] = input["dst"]
    output["dst_entity_attr"] = condition_attrs["dst_entity_attr"]
    output["correlation_logic"] = "Equal"  # All existing relations are with "Equal" correlation logic for now, to be extended
    output["type"] = type
    output["properties"] = ""
    if type == "supporting":
        output["show_name"] = "{} {} for {}".format(type, input["dst"], input["src"])
    elif type == "contains":
        output["show_name"] = "{} {} {}".format(input["src"], type, input["dst"])
    else:  # "source/dest" representing source/destination interface of entity
        output["show_name"] = "{} interface of the {}".format(type, input["src"])
    output["description"] = input["label"]

    return output

@login_decorator
def generate_mapping_json_model_data(input):
    output = {}

    vendor = input["vendor"]
    neType = input["neType"]
    osVersion = input["osVersion"]

    build_method = "{}Method".format(input["buildMethod"])
    input_method_specific_attrs = input[build_method]
    
    model_data = {}
    model_data["Build_Mode"] = input["buildMode"]
    model_data["Build_Method"] = input["buildMethod"]
    if "generatedFile" in input:
        model_data["Generated_File"] = input["generatedFile"]
    if "generatedFileConfig" in input_method_specific_attrs:
        model_data["Generated_File_Config"] = input_method_specific_attrs["generatedFileConfig"]
    if "inputExternalFiles" in input_method_specific_attrs:
        model_data["Input_External_Files"] = input_method_specific_attrs["inputExternalFiles"]
    if "inputInternalFiles" in input_method_specific_attrs:
        model_data["Input_Internal_Files"] = input_method_specific_attrs["inputInternalFiles"]
    if input["buildMode"] == "python" and "pythonFile" in input_method_specific_attrs:
        model_data["Python_File"] = input_method_specific_attrs["pythonFile"]
    if "key" in input:
        model_data["Key"] = input["key"]
    if "properties" in input_method_specific_attrs:
        input_props = input_method_specific_attrs["properties"]
        output_props = {}
        for input_prop in input_props:
            output_prop_key = input_prop["name"]
            output_prop_value = {}
            for key, value in input_prop.items():
                if key != "name":
                    output_prop_value[key] = value
            output_props[output_prop_key] = output_prop_value
        model_data["Properties"] = output_props

    #data_key = "{}-{}-{}-{}".format(input["name"], vendor, neType, osVersion)
    data_key = input["name"]
    output[data_key] = model_data

    #return output
    return {
        "data": output,
        "vendor": vendor,
        "neType": neType,
        "osVersion": osVersion
    }

def get_aggregation_entity_attr(value):
    attr = ""
    if isinstance(value, str):
        start_index = 3  # Characters after $['
        end_index = len(value) - 2  # Characters before ']
        attr = re.sub("(src|source|dst|dest)-", "", value[start_index:end_index])

    return attr

def get_condition_attrs(value, logic):
    condition_dict = {
        "src_entity_attr": "",
        "dst_entity_attr": ""
    }

    if isinstance(value, str):
        condition_list = value.split(" & ")
        src_entity_attr_value = ""
        dst_entity_attr_value = ""
        for index, condition_str in condition_list:
            if logic == "Equal":
                start_index = 1
                end_index = len(condition_str) - 1
                ends_list = condition_str[start_index:end_index].split(" == ")
                src_str = ends_list[0]
                dst_str = ends_list[len(ends_list) - 1]
                src_list = src_str.split(".")
                dst_list = dst_str.split(".")
                src_entity_attr_value += src_list[len(src_list) - 1]
                dst_entity_attr_value += dst_list[len(dst_list) - 1]
                if (index < len(condition_list) - 1): 
                    src_entity_attr_value += " & "
                    dst_entity_attr_value += " & "

        condition_dict["src_entity_attr"] = src_entity_attr_value
        condition_dict["dst_entity_attr"] = dst_entity_attr_value

    return condition_dict
#------------------------------------------------------------------------------------------------

class DigitalMapEntity:
    @login_decorator
    def __init__(self, type):
        self.type = type

        self.json_entity_model = None
        self.layer = None
        self.sublayer = None
        self.topology_role = None
        self.key = []
        self.properties = []
        self.properties_json = {}

        # this will have to be multiple mapping models, based on the system type and software version
        self.json_mapping_model = {}

    @login_decorator
    def set_entity_model(self, json_entity_model):
        self.json_entity_model = json_entity_model

        self.layer = json_entity_model['layer']
        self.sublayer = json_entity_model['sublayer']
        self.topology_role = json_entity_model['topologyRole']
        self.key = json_entity_model['key']
        self.properties_json = json_entity_model['properties']

        for key in self.properties_json:
            self.properties.append(key)

    @login_decorator
    def set_aggregation_model(self, json_aggregation_model):
        self.json_aggregation_model = json_aggregation_model

    @login_decorator
    def add_entity_mapping_model(self, vendor, sys_type, software_version, json_mapping_model):

        sw_dict = {software_version: json_mapping_model}
        dev_dict = {sys_type: sw_dict}
        vendor_dict = {vendor: dev_dict}

        if (vendor not in self.json_mapping_model):
            self.json_mapping_model[vendor] = dev_dict
        elif (sys_type not in self.json_mapping_model[vendor]):
            self.json_mapping_model[vendor][sys_type] = sw_dict
        elif (software_version not in self.json_mapping_model[vendor][sys_type]):
            self.json_mapping_model[vendor][sys_type][software_version] = json_mapping_model

    @login_decorator
    def get_entity_xpaths(self, external_system_info):

        entity_xpaths = []
        if not self.mapping_exists(external_system_info):
            return entity_xpaths

        vendor = external_system_info.sys_vendor
        sys_type = external_system_info.sys_type
        software_version = external_system_info.software_version

        if 'Properties' not in self.json_mapping_model[vendor][sys_type][software_version]:
            return entity_xpaths

        for key in self.properties_json:
            entity_xpath = {}
            if key not in self.json_mapping_model[vendor][sys_type][software_version]['Properties']:
                continue
            property_definition = self.json_mapping_model[vendor][sys_type][software_version]['Properties'][key]
            if 'xpathNamespace' in property_definition and 'xpathSelect' in property_definition:
                param_namespace = property_definition['xpathNamespace']
                param_select = property_definition['xpathSelect']
                if (param_namespace == '') or (param_select == ''):
                    continue
            else:
                continue
            entity_xpath = {"xpathNamespace": param_namespace, "xpathSelect": param_select}
            if entity_xpath not in entity_xpaths:
                entity_xpaths.append(entity_xpath)

        return entity_xpaths

    @login_decorator
    def get_generated_file(self, external_system_info: ExternalSystemInfo):
        generated_file = None
        vendor = external_system_info.sys_vendor
        sys_type = external_system_info.sys_type
        software_version = external_system_info.software_version
        if self.mapping_exists(external_system_info) and 'Generated_File' in self.json_mapping_model[vendor][sys_type][software_version]:
            generated_file = self.json_mapping_model[vendor][sys_type][software_version]['Generated_File']
        return generated_file

    @login_decorator
    def get_generated_file_config(self, external_system_info: ExternalSystemInfo):
        generated_file_config = None
        generated_file_config_scope = None
        vendor = external_system_info.sys_vendor
        sys_type = external_system_info.sys_type
        software_version = external_system_info.software_version
        if self.mapping_exists(external_system_info) and 'Generated_File_Config' in self.json_mapping_model[vendor][sys_type][software_version]:
            generated_file_config = self.json_mapping_model[vendor][sys_type][software_version]['Generated_File_Config'][0]
            generated_file_config_scope = self.json_mapping_model[vendor][sys_type][software_version]['Generated_File_Config'][1].split(",")

        return generated_file_config, generated_file_config_scope

    @login_decorator
    def get_input_external_files(self, external_system_info: ExternalSystemInfo):
        input_file_list = []
        input_files = ""

        vendor = external_system_info.sys_vendor
        sys_type = external_system_info.sys_type
        software_version = external_system_info.software_version
        if self.mapping_exists(external_system_info) and 'Input_External_Files' in self.json_mapping_model[vendor][sys_type][software_version]:
            input_files = self.json_mapping_model[vendor][sys_type][software_version]['Input_External_Files']
            input_file_list = input_files.split(",")

        return input_file_list

    @login_decorator
    def get_input_internal_files(self, external_system_info: ExternalSystemInfo):
        input_file_list = []
        input_files = ""

        vendor = external_system_info.sys_vendor
        sys_type = external_system_info.sys_type
        software_version = external_system_info.software_version
        if self.mapping_exists(external_system_info) and 'Input_Internal_Files' in self.json_mapping_model[vendor][sys_type][software_version]:
            input_files = self.json_mapping_model[vendor][sys_type][software_version]['Input_Internal_Files']
            input_file_list = input_files.split(",")

        return input_file_list

    @login_decorator
    def get_build_method(self, external_system_info: ExternalSystemInfo):
        build_method = None
        vendor = external_system_info.sys_vendor
        sys_type = external_system_info.sys_type
        software_version = external_system_info.software_version
        if self.mapping_exists(external_system_info) and 'Build_Method' in self.json_mapping_model[vendor][sys_type][software_version]:
            build_method = self.json_mapping_model[vendor][sys_type][software_version]['Build_Method']
        return build_method

    @login_decorator
    def get_python_code(self, external_system_info: ExternalSystemInfo):
        vendor = external_system_info.sys_vendor
        sys_type = external_system_info.sys_type
        software_version = external_system_info.software_version

        python_file_name =""
        python_code = ""
        if 'Python_File' in self.json_mapping_model[vendor][sys_type][software_version]:
            python_file_name =  self.json_mapping_model[vendor][sys_type][software_version]['Python_File']
            python_file_path = "data/knowledge/mapping/" + vendor + "/" + sys_type + "/" + software_version + "/" + python_file_name
            python_code = open(python_file_path)

        return python_file_name, python_code

    @login_decorator
    def mapping_exists(self, external_system_info: ExternalSystemInfo):
        mapping_exists = False

        vendor = external_system_info.sys_vendor
        sys_type = external_system_info.sys_type
        software_version = external_system_info.software_version

        if vendor in self.json_mapping_model:
            if sys_type in self.json_mapping_model[vendor]:
                if software_version in self.json_mapping_model[vendor][sys_type]:
                    return True

    @login_decorator
    def generate_instances_system(self, external_system_info: ExternalSystemInfo, system_path,
                                    json_conf_data, json_status_data,
                                    input_files_json_data, json_entities_path):

        generated_instances = []
        build_method = self.get_build_method(external_system_info)

        if build_method == None:
            return []
        if build_method != 'json' and build_method!= 'python':
            logger.error("The build method not implemented yet ", build_method)
            return []

        # TODO: not implemented yet
        # support list of methods, python after json or json after python, with instances forwarded between them

        if build_method == 'json':
            generated_instances = self.generate_instances_system_json(external_system_info, system_path,
                                       json_conf_data, json_status_data, input_files_json_data, json_entities_path)

        if build_method == 'python':
            generated_instances = self.generate_instances_system_python(external_system_info, system_path,
                                       json_conf_data, json_status_data, input_files_json_data, json_entities_path)

        return generated_instances

    # Generate instances from json, Build_Method is 'json'
    @login_decorator
    def generate_instances_system_json(self, external_system_info: ExternalSystemInfo, system_path,
                                       json_conf_data, json_status_data,
                                       input_files_json_data, json_entities_path):

        vendor = external_system_info.sys_vendor
        sys_type = external_system_info.sys_type
        software_version = external_system_info.software_version

        if not self.json_mapping_model:
            return []
        if 'Properties' not in self.json_mapping_model[vendor][sys_type][software_version]:
            return []

        mapping_properties_json = self.json_mapping_model[vendor][sys_type][software_version]['Properties']

        # Currently supports one key only, TODO: composite key
        unique_key = self.json_mapping_model[vendor][sys_type][software_version]['Key'][0]
        record = mapping_properties_json[unique_key]
        if 'jsonPath' not in record:
            logger.error("json path is not present in the key for entity {} ".format(self.type))
            return

        try:
            jsonpath_expr = parse(record['jsonPath'])

            # Support cases where we have key in generated_file_json_data and input_files_json_data
            # or in the external file which name is specified in the Properties
            json_source_data = ""
            if json_conf_data:
                json_source_data = json_conf_data
            elif json_status_data:
                json_source_data = json_status_data
            elif input_files_json_data:
                if ('jsonFileExternalSystem' in record) and (record['jsonFileExternalSystem'] is not ""):
                    external_file = record['jsonFileExternalSystem']
                    json_source_data = input_files_json_data[external_file]
                else:
                    for k in input_files_json_data:
                        json_source_data += input_files_json_data[k]
            else:
                if ('jsonFileExternalSystem' in record) and (record['jsonFileExternalSystem'] is not ""):
                    external_file_path = system_path + "/json/" + record['jsonFileExternalSystem']
                    with open(external_file_path) as json_file:
                        json_source_data = json.load(json_file)

            if json_source_data == "":
                return []

            generated_instances = []
            index = 0
            matches = jsonpath_expr.find(json_source_data)
            no_of_matches = len(matches)

        except Exception as e:
            logger.error("ERROR: generate_instances_system_json ", e)
            logger.error("ERROR for entity: {}".format(self.type))
            return []

        for match in matches:

            generated_instance = {}
            for property_key in mapping_properties_json:
                record = mapping_properties_json[property_key]
                if 'value' in mapping_properties_json[property_key]:
                    generated_instance[property_key] = mapping_properties_json[property_key]['value']
                    continue
                if 'jsonPath' in record:
                    new_jsonpath = record['jsonPath']
                else:
                    continue

                new_index = "[" + str(index) + "]"
                if "[*]" in new_jsonpath:
                    if no_of_matches > 1:
                        new_jsonpath = new_jsonpath.replace("[*]", new_index)
                    else:
                        new_jsonpath = new_jsonpath.replace("[*].", ".")
                jsonpath_expr = parse(new_jsonpath)
                # TODO: check all xpaths for present and empty string
                if ('xpathNamespace' not in record) or (record['xpathNamespace'] is ""):
                    json_file_name = ""
                    json_file_path = ""
                    if ('jsonFileExternalSystem' in record) and (record['jsonFileExternalSystem'] is not ""):
                        logger.debug("Device File used for mapping for {0}:{1}".format(self.type, property_key))
                        json_file_name = record['jsonFileExternalSystem']
                        json_file_path = system_path + "/json/" + json_file_name
                        with open(json_file_path) as json_file:
                            json_data = json.load(json_file)
                    elif ('jsonFileLocal' in record) and (record['jsonFileLocal'] is not ""):
                        # access the file on data/knowledge/entities dir
                        logger.debug("Local File used for mapping for {0}:{1}".format(self.type, property_key))
                        json_file_name = record['jsonFileLocal']
                        json_file_path = json_entities_path + "/" + json_file_name
                        with open(json_file_path) as json_file:
                            json_data = json.load(json_file)
                    elif ('jsonPath' in record) and (record['jsonPath'] is not ""):
                        json_data = json_source_data
                    else:
                        continue

                    expression_output = jsonpath_expr.find(json_data)
                    if (len(expression_output) > 0):
                        expression_output_value = expression_output[0].value
                        generated_instance[property_key] = expression_output_value
                    else:
                        generated_instance[property_key] = ""
                else:
                    # access the generated file
                    logger.debug("Generated File used for mapping for {0}:{1}".format(self.type, property_key))
                    expression_output = jsonpath_expr.find(json_source_data)
                    if expression_output:
                        expression_output_value = expression_output[0].value
                    else:
                        expression_output_value = "N/A"
                    generated_instance[property_key] = expression_output_value

            for property_key in mapping_properties_json:
                record = mapping_properties_json[property_key]
                if 'compute' in mapping_properties_json[property_key]:
                    generated_instance[property_key] = \
                        self.compute_property(generated_instance, property_key,
                                              mapping_properties_json[property_key]['compute'])
                else:
                    continue
            index += 1
            generated_instances.append(generated_instance)

        return generated_instances


    # Generate instances from json, Build_Method is 'python'
    @login_decorator
    def generate_instances_system_python(self, external_system_info: ExternalSystemInfo, device_path,
                                         json_conf_data, json_status_data,
                                         input_files_json_data, json_entities_path):

        if self.get_build_method(external_system_info) != 'python':
            logger.error("Build Method is not python")

        # get python code from the mappings
        vendor = external_system_info.sys_vendor
        sys_type = external_system_info.sys_type
        software_version = external_system_info.software_version

        if not self.json_mapping_model:
            return []

        relative_path = "./data/knowledge/mapping/" + vendor + "/" + sys_type + "/" + software_version
        python_package = "data.knowledge.mapping." + vendor + "." + sys_type + "." + software_version + "." + self.type

        try:
            m = import_code(relative_path, python_package)
            generated_instances = m.generate_instances(json_conf_data, json_status_data,
                                                        input_files_json_data)
        except Exception as e:
            logger.error("ERROR: generate_instances_system_python ", e)
            logger.error("ERROR for script: {}".format(python_package))
            return []

        return generated_instances


    # generate aggregation instance from aggregation rules and src and dst nodes
    @login_decorator
    def generate_instance_aggregated(self, src_type, src_node, dst_type, dst_node):

        generated_instance = {}
        aggregation_properties_json = self.json_aggregation_model[self.type]['Properties']
        for property_key in aggregation_properties_json:
            record = aggregation_properties_json[property_key]
            if 'value' in aggregation_properties_json[property_key]:
                generated_instance[property_key] = aggregation_properties_json[property_key]['value']
            elif 'src_entity_attr' in record:
                attr = record['src_entity_attr']
                generated_instance[property_key] = src_node[attr]
            elif 'dst_entity_attr' in record:
                attr = record['dst_entity_attr']
                generated_instance[property_key] = dst_node[attr]

        for property_key in aggregation_properties_json:
            record = aggregation_properties_json[property_key]
            if 'compute' in aggregation_properties_json[property_key]:
                generated_instance[property_key] = \
                    self.compute_property(generated_instance, property_key,
                                          aggregation_properties_json[property_key]['compute'])
            else:
                continue

        entityID = self.generate_entity_id(self.type, generated_instance)
        if ("compute" in self.layer):
            layer = self.compute_layer(generated_instance, self.layer['compute'])
            generated_instance["layer"] = layer
        else:
            generated_instance["layer"] = self.layer
        generated_instance["sublayer"] = self.sublayer
        generated_instance["topologyRole"] = self.topology_role
        generated_instance["entityType"] = self.type
        generated_instance["entityID"] = entityID
        return generated_instance

    # compute property using some basic computation from other properties
    @login_decorator
    def compute_property(self, generated_instance, property_key, compute_string):
        computed_property = "";

        # replace $[name] in the compute string with generated_instance[name]
        compute_string_processed = compute_string.replace("$", 'generated_instance')
        try:
            computed_property = eval(compute_string_processed)
        except Exception as e:
            logger.error("ERROR: Failed to compute property", e)
            logger.error("Computing property failed")
            logger.error("    for property " + self.type + ":" + property_key)
            logger.error("    for compute string " + compute_string)
            logger.error("    for processed string " + compute_string_processed)
        return computed_property

    # compute property using some basic computation from other properties
    @login_decorator
    def compute_layer(self, generated_instance, compute_string):
        computed_layer = "";

        # replace $[name] in the compute string with generated_instance[name]
        compute_string_processed = compute_string.replace("$", 'generated_instance')
        try:
            computed_layer = eval(compute_string_processed)
        except Exception as e:
            logger.error("ERROR: Failed to compute layer", e)
            logger.error("Computing layer failed")
            logger.error("    for compute string " + compute_string)
            logger.error("    for processed string " + compute_string_processed)
        return computed_layer

    # return colums for the entities
    @login_decorator
    def get_columns(self):

        columns = ['entityID', 'entityType', 'layer', 'sublayer', 'topologyRole']
        columns.extend(self.properties)
        return columns

    # generates entityID from key properties key1:key2:key3 .... based on the number of key properties
    @login_decorator
    def generate_entity_id(self, entity_type, entity_instance):
        entity_id = entity_type + ":"
        key_len = len(self.key)
        i = 1
        for key_part in self.key:
            entity_id += entity_instance[key_part]
            if ( i < key_len):
                entity_id += ":"
            i += 1

        return entity_id
