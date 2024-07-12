from datetime import datetime
from shutil import move

import os
import json
import traceback


from flask import Flask, request

from digital_map.ietf import ietf
from util.app_logger import get_my_logger, loging_shutdown

from config.config import dm_directories, digital_map_scenarios_configured
from config.config_login import login_file
from config.config_netconf import netconf_devices
from config.init_netconf_config import initiate_netconf_devices, initiate_netconf_scenarios
from config.init_knowledge import initiate_knowledge
from config.init_data import initiate_data, initiate_network_simulation_netconf, initiate_network_simulation_csv
from config.init_digital_map import initiate_digital_map_scenarios, initiate_digital_map_db
from netconf.netconf_discovery import network_discovery

from digital_map.scenarios.digital_map_scenarios import DigitalMapScenarios

from util.dir_util import create_dir, del_dir, copy_dir, is_file, exists_path

app = Flask(__name__)

results_path = dm_directories['results']['results']
logger = get_my_logger(__name__)
counter = 0
@app.route('/discover-lab/<path:poc_dir>')
def discover_lab(poc_dir):

    devices_json_file = poc_dir + "/config/netconf_devices.json"
    scenarios_json_file = poc_dir + "/config/netconf_scenarios.json"

    now = datetime.today()
    now_string = now.strftime("%d-%m-%Y-%H-%M-%S")
    now_date = now.strftime("%d-%m-%Y")
    now_time = now.strftime("%H-%M-%S")
    create_dir(results_path)
    date_path = results_path + "/" + now_date
    create_dir(date_path)
    datetime_path = date_path + "/" + now_time
    create_dir(datetime_path)

    logger.info("Discover LAB START at {0}".format(now_string))

    initiate_netconf_devices(devices_json_file)
    initiate_netconf_scenarios(scenarios_json_file)

    device_str = "Devices to be discovered in the LAB: " + poc_dir + "\n"
    device_ips = ""
    for device in netconf_devices:
        device_str = device_str + device.host + "\n"
        device_ips = device_ips + device.host + ", "
    logger.info(device_str)

    netconf_path = datetime_path + "/" + dm_directories['results']['netconf']

    discovery = network_discovery(netconf_devices, netconf_path)

    loging_shutdown()
    move(login_file, datetime_path + "/" + login_file)
    generated_path_netconf = dm_directories['generated']['netconf']
    del_dir(generated_path_netconf)
    copy_dir(netconf_path, generated_path_netconf)

    return ("LAB Discovery Successful for LAB: " + poc_dir + "and for devices " + device_ips)

def initiate_demo(poc_dir):

    devices_json_file = poc_dir + "/config/netconf_devices.json"
    netconf_scenarios_json_file = poc_dir + "/config/netconf_scenarios.json"
    scenarios_json_file = poc_dir + "/config/digital_map_scenarios.json"
    db_json_file = poc_dir + "/config/digital_map_db.json"

    knowledge_dir = poc_dir + "/data/knowledge"
    data_dir = poc_dir + "/data/entities"
    netconf_simulation_dir = poc_dir + '/data_generated/netconf'
    csv_simulation_dir = poc_dir + '/data_generated/entities'

    initiate_netconf_devices(devices_json_file)
    initiate_netconf_scenarios(netconf_scenarios_json_file)
    initiate_digital_map_scenarios(scenarios_json_file)
    initiate_digital_map_db(db_json_file)
    initiate_knowledge(knowledge_dir)
    initiate_data(data_dir)
    initiate_network_simulation_netconf(netconf_simulation_dir)
    initiate_network_simulation_csv(csv_simulation_dir)
    return("DM Scenarios Initiated")

@app.route('/generate-dm/<path:poc_dir>')
def generate_dm(poc_dir):
    try:
        global counter
        counter = counter + 1
        now = datetime.today()
        now_string = now.strftime("%d-%m-%Y-%H-%M-%S")
        now_date = now.strftime("%d-%m-%Y")
        now_time = now.strftime("%H-%M-%S")
        create_dir(results_path)
        date_path = results_path + "/" + now_date
        create_dir(date_path)
        datetime_path = date_path + "/" + now_time
        create_dir(datetime_path)

        logger.info("{0}: Digital Map generation started at {1} for PoC {2}".format(counter, now_string, poc_dir))

        initiate_demo(poc_dir)

        for scenario in digital_map_scenarios_configured:
            doSomething = getattr(DigitalMapScenarios, scenario)
            doSomething(DigitalMapScenarios(datetime_path))

        return ("Model Generation Successful for POC {0}".format(poc_dir))

    except Exception as ex:
        traceback.print_exc()
        return ("Model Generation Failed for POC {0} with error: ".format(poc_dir, str(ex)))

# Example of the request
# http://localhost:9210/restconf/v1/data/ietf-network:networks/network?attr=entityType&type=ISIS&template=huawei-template.j2
@app.route('/restconf/v1/data/ietf-network:networks/network', methods=["GET"])
def get_network():
    try:
        now = datetime.today()
        now_string = now.strftime("%d-%m-%Y-%H-%M-%S")
        now_date = now.strftime("%d-%m-%Y")
        now_time = now.strftime("%H-%M-%S")
        create_dir(results_path)
        date_path = results_path + "/" + now_date
        create_dir(date_path)
        datetime_path = date_path + "/" + now_time
        create_dir(datetime_path)

        req_type = str(request.args.get('attr'))
        req_type_name = str(request.args.get('type'))
        template =   str(request.args.get('template'))
        ietf_api_return = json.dumps(ietf.get_entity_by_type(req_type, req_type_name))

        output = ietf.gen_instance_based_on_jinja(datetime_path,ietf_api_return, template, req_type_name)
        return output
    except Exception as ex:
        traceback.print_exc()
        return {'status': 'failed', 'error': str(ex)}

if __name__ == "__main__":
    now = datetime.today()
    now_string = now.strftime("%d-%m-%Y-%H-%M-%S")
    counter = counter + 1
    logger.info("{0}:Digital Map generation started at {1}".format(counter, now_string))
    app.run('0.0.0.0', port=os.getenv("FLASK_PORT", "9210"),)

