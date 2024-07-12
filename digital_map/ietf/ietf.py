__author__ = "Adriana"

from datetime import datetime
from jinja2 import Environment, FileSystemLoader
import json
import os
from pathlib import Path
import glob
# import config.lab_databases
from config.config import generated_database
from config.config import dm_directories
from digital_map.database.digital_map_db_neo4j import DigitalMapDB_neo4j
from digital_map.database.digital_map_db_py2neo import DigitalMapDB_py2neo
from util.app_logger import get_my_logger
logger = get_my_logger(__name__)
from util.dir_util import copy_dir, del_dir
# import libyang


def gen_instance_based_on_jinja(datetimepath, results, template, type):
    # template = "huawei-template.j2"
    template = template
    scenario_type = type
    output_dir = "data_generated/yang/knowledge/entities"
    yang_instance_file_name = "dm-{}-instance.json".format(type)

    name = "nametest"
    revision = "revisiontest"

    JINJA_ENV = Environment(
        loader=FileSystemLoader(os.path.dirname(__file__)))

    node_element = {}
    node_results = []
    network_results = []
    link_results = []
    tp_results = []

    results = json.loads(results)
    for result in results:

        if (result["sublayer"]!="ISIS"):
            print (result["entityID"])

        topologyRole = result["topologyRole"]

        if topologyRole == "network":
            network_results.append(result)

        if topologyRole == "node":
            node_results.append((result))

        if topologyRole == "link":
            link_results.append (result)

        if topologyRole == "termination-point":
            tp_results.append (result)

    results_path = datetimepath + "/" + "data_yang/sample"
    output_yang_file = os.path.join(results_path, yang_instance_file_name)

    Path(results_path).mkdir(parents=True, exist_ok=True)

    with open(output_yang_file, "w") as yang_file:
        template = JINJA_ENV.get_template(template)
        yang_template_rendered = template.render(
            name=name,
            revision=revision,
            node_props=node_results,
            network_props = network_results,
            link_props=link_results,
            tp_props=tp_results
        )
        yang_file.write(yang_template_rendered)

    logger.info("YANG Instance file for {} generated".format(type))

    del_dir(dm_directories['generated']['yang'])
    copy_dir(datetimepath + "/" + "data_yang/",
             dm_directories['generated']['yang'])

    return yang_template_rendered

def generate_yang (type_name: str):
    name = type_name
    template = "dm-concrete.yang"
    output_dir = "data/data_yang/knowledge/entities"
    dm_kb_entities_path = "data/knowledge/entities_inheritance"
    # concrete_dm_kb_sub_dirs = [
    #     "/Protocol/OSPF",
    #     "/Protocol/BGP",
    #     "/Protocol/ISIS",
    #     "/Tunnel/LDP",
    #     "/Tunnel/MPLS",
    #     "/Tunnel/SRv6",
    #     "/Tunnel/TE",
    #     "/VPN/VPN",
    #     "/IETF/ietf-l2-topology",
    #     "/IETF/ietf-l3-unicast-topology"
    # ]

    concrete_dm_kb_sub_dirs = {
        "OSPF" : "/Protocol/OSPF",
        "BGP" : "/Protocol/BGP",
        "ISIS" : "/Protocol/ISIS",
        "LDP" : "/Tunnel/LDP",
        "MPLS" : "/Tunnel/MPLS",
        "SRv6": "/Tunnel/SRv6",
        "TE" : "/Tunnel/TE",
        "VPN" : "/VPN/VPN",
        "L2Topo" : "/IETF/ietf-l2-topology",
        "L3Topo" : "/IETF/ietf-l3-unicast-topology"
    }
    JINJA_ENV = Environment(
        loader=FileSystemLoader(os.path.join(os.path.dirname(__file__), "data/data_yang/config/template")))

    input_dict = read_dm_kb_from_metadata(dm_kb_entities_path + concrete_dm_kb_sub_dirs[type_name] + "/**/*.json")

    revision = today()
    yang_file_name = f"dm-{name}@{revision}.yang"
    output_yang_file = os.path.join(output_dir, yang_file_name)
    node_props = {}
    link_props = {}
    tp_props = {}
    nw_props = {}
    cs_dict = {}

    node_key = ""
    link_key = ""
    tp_key = ""
    nw_key = ""
    cs_key = ""

    for key, value in input_dict.items():
        key_comp_str = ""
        if "parent" in value:
            key_comp_str = value["parent"]
        else:
            key_comp_str = key

        if any(map(key_comp_str.__contains__, ["node", "Node"])):
            node_key = key
        elif any(map(key_comp_str.__contains__, ["link", "Link"])) or key_comp_str.endswith("Tunnel"):
            link_key = key
        elif any(map(key_comp_str.__contains__, ["termination-point", "TerminationPoint"])):
            tp_key = key
        elif any(map(key_comp_str.__contains__, ["network", "Network"])):
            nw_key = key
        else:
            cs_key = key

    if node_key in input_dict and "properties" in input_dict[node_key]:
        node_props = input_dict[node_key]["properties"]
    if link_key in input_dict and "properties" in input_dict[link_key]:
        link_props = input_dict[link_key]["properties"]
    if tp_key in input_dict and "properties" in input_dict[tp_key]:
        tp_props = input_dict[tp_key]["properties"]
    if nw_key in input_dict and "properties" in input_dict[nw_key]:
        nw_props = input_dict[nw_key]["properties"]
    if cs_key in input_dict and "properties" in input_dict[cs_key]:
        cs_dict = input_dict

    Path(output_dir).mkdir(parents=True, exist_ok=True)

    with open(output_yang_file, "w") as yang_file:
        template = JINJA_ENV.get_template(template)
        yang_template_rendered = template.render(
            name=name,
            revision=revision,
            node_props=node_props,
            link_props=link_props,
            tp_props=tp_props,
            nw_props=nw_props,
            cs_dict=cs_dict,
            cs_key=cs_key
        )
        yang_file.write(yang_template_rendered)

    return yang_template_rendered


def generate_yang_instance_file(results_path, ns_qualified_json_files, dm_module_name):
    Path(results_path).mkdir(parents=True, exist_ok=True)
    f = open(results_path + "/" + "{}-sample.json".format(dm_module_name), "w")
    f.write(json.dumps(ns_qualified_json_files))
    f.close()


def today() -> str:
    return datetime.now().date().isoformat()


def get_dm_db():
    # generated_database = config.lab_databases.LAB_NEO4J_DB_GZ_remote
    generated_database.name = os.getenv("DB_NAME", generated_database.name)
    generated_database.uri = os.getenv("DB_URI", generated_database.uri)
    generated_database.user = os.getenv("DB_USER", generated_database.user)
    generated_database.password = os.getenv("DB_PASS", generated_database.password)
    input_db = DigitalMapDB_neo4j(generated_database)
    output_db = DigitalMapDB_py2neo(generated_database)
    return input_db, output_db


def read_dm_kb_from_metadata(json_input_path):
    result_dict = {}
    json_input_files = glob.glob(json_input_path, recursive=True)

    for file in json_input_files:
        with open(file, "r") as json_file:
            json_context = json.load(json_file)
            for key, value in json_context.items():
                result_dict[key] = value

    return result_dict


def get_entity_by_type(e_attr, e_type):
    query = (
        "MATCH (n) where n.`" + e_attr + "` =~ \".*" + e_type + ".*\" RETURN n;"
    )

    return get_dm_db()[0].execute_query(query)
