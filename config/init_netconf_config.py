import json

from util.external_system import ExternalSystemInfo
from config.config_netconf import netconf_devices, netconf_scenarios_configured, get_netconf_path_scenarios
from netconf.netconf_scenario_definition import netconf_scenario_definition
from util.dir_util import is_file, exists_path
def initiate_netconf_devices(json_file):
    global netconf_devices

    if not exists_path(json_file):
        return
    if not is_file(json_file):
        return

    with open(json_file) as data_file:
        data=json.load(data_file)

    for response in data['devices']:
        device = ExternalSystemInfo(response['category'],
                                    response['sys_vendor'],
                                    response['sys_type'],
                                    response['software_version'],
                                    response['host'],
                                    response['port'],
                                    response['username'],
                                    response['password'],
                                    response['device_handler'])
        netconf_devices.append(device)

def initiate_netconf_scenarios(json_file):
    global netconf_scenarios_configured

    if not exists_path(json_file):
        return
    if not is_file(json_file):
        return

    with open(json_file) as data_file:
        data=json.load(data_file)

    for response in data['scenarios']:
        scenario = response['scenario']
        netconf_scenarios_configured.append(scenario)
        if scenario == 'get_path_list':
            for path in response['path_list']:
                path_path = path["path"]
                path_path.replace("'",'"')
                
                path_scenario = netconf_scenario_definition(
                    vendor=path["vendor"],
                    path=path_path,
                    file=path["file"]
                )
                get_netconf_path_scenarios.append(path_scenario)








