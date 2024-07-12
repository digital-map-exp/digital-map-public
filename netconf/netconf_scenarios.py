
from netconf.netconf_collector import server_connect, server_disconnect, \
    get_config, get_path, get_any, server_capabilities, get_schema, manager_server_capabilities, \
    manager_get_path, manager_get_schema, manager_get_xpath, manager_get_xpath_multi
from config.config_netconf import get_any_namespace, get_any_filter, get_any_file, get_netconf_path_scenarios

from util.dir_util import create_dirs, create_dir
from util.external_system import ExternalSystemInfo
from util.dict_manipulation import delete_dict_elements
import sys
import re
import html
from lxml import etree
from datetime import datetime
import json
import xmltodict

from util.app_logger import get_my_logger, login_decorator
logger = get_my_logger(__name__)


class netconf_scenarios (object):

    @login_decorator
    def __init__(self, device_path, netconf_device: ExternalSystemInfo):
        self.path = device_path
        self.device_info = netconf_device

    @login_decorator
    def server_capabilities(self):
        n_capabilities = 1
        netconf_capabilities = server_capabilities(self.device_info)
        file = open(self.path + '/' + "all_server_capabilities.xml", 'wt', encoding='utf-8')
        for c in netconf_capabilities:
            file.write('CAPABILITY ' + str(n_capabilities) + ':' + '\n' + c + '\n\n')
            n_capabilities = n_capabilities + 1
        file.close()

    @login_decorator
    def get_yang_modules_summary(self):
        n_modules = 1
        netconf_capabilities = server_capabilities(self.device_info)
        file1 = open(self.path + '/' + "all_yang_modules.xml", 'wt', encoding='utf-8')
        file2 = open(self.path + '/' + "all_telemetry_modules.xml", 'wt', encoding='utf-8')
        for c in netconf_capabilities:
            #   model = re.search('module=([^&]*[^&]*)&', c)
            model = re.search('module=(.+?)&revision', c)
            if model is not None:
                file1.write('MODULE ' + str(n_modules) + ':' + ' ' + str(model.group(1)) + '\n')
                n_modules = n_modules + 1

            model = re.search('module=([^&]*telemetry[^&]*)&', c)
            if model is not None:
                file2.write(str(model.group(1)) + '\n')
        file1.close()
        file2.close()

    @login_decorator
    def get_yang_modules(self):
        file_path = self.path + "/yang-modules"
        create_dir(file_path)
        schemas = []

        xr = server_connect(self.device_info)
        netconf_capabilities = manager_server_capabilities(xr)

        for c in netconf_capabilities:
            model = re.search('module=(.+?)&revision', c)
            if model is not None:
                schemas.append(model.group(1))

        for schemafile in schemas:
            schema = manager_get_schema(xr, schemafile)
            file_name = schemafile + '.yang'
            logger.debug('    YANG File: ' + file_name)
            file = open(file_path + '/' + file_name, 'wt', encoding='utf-8')
            file.write(str(html.unescape(str(schema))))
            file.close()

        server_disconnect(xr)

    @login_decorator
    def get_yang_modules_and_submodules(self):
        file_path = self.path + "/yang-modules-submodules"
        create_dir(file_path)
        xr = server_connect(self.device_info)
        schemas = []
        path1 = """<ns0:modules-state xmlns:ns0="urn:ietf:params:xml:ns:yang:ietf-yang-library"/>"""
        path2 = """
            <ns0:modules-state xmlns:ns0="urn:ietf:params:xml:ns:yang:ietf-yang-library">
                <ns0:module>
                    <ns0:name/>
                </ns0:module>
            </ns0:modules-state>
            """

        # Retrieve the ietf-yang-library instances: all modules, deviations and submodules
        try:
            get_data = manager_get_path(xr, path1)
            file = open(self.path + '/' + "ietf-yang-library.xml", 'w')
            file.write(str(html.unescape(str(get_data))))
            file.close()
        except:
            error = str(sys.exc_info())
            file = open(self.path + '/' + "ERROR-ietf-yang-library.txt", 'w')
            file.write("ERROR: " + error)
            file.close()

        # Retrieve modules (including deviations) and submodules
        try:
            ns = {"ns" : "urn:ietf:params:xml:ns:yang:ietf-yang-library"}
            response = manager_get_path(xr, path1)

            file = open(self.path + '/' + "all_yang_modules_submodules.txt", 'w')

            for module in response.data.xpath("ns:modules-state/ns:module", namespaces=ns):
                moduleName = module.find("ns:name", ns).text
                schemas.append(moduleName)
                file.write("MODULE: " + moduleName + "\n")
            for submodule in response.data.xpath("ns:modules-state/ns:module/ns:submodule", namespaces=ns):
                submoduleName = submodule.find("ns:name", ns).text
                schemas.append(submoduleName)
                file.write("SUBMODULE: " + submoduleName + "\n")

            file.close()
        except:
            error = str(sys.exc_info())
            logger.error('ERROR while getting modules and submodules: ' + error)

        for schemafile in schemas:
            schema = manager_get_schema(xr, schemafile)
            file_name = schemafile + '.yang'
            logger.debug('    YANG File: ' + file_name)
            file = open(file_path + '/' + file_name, 'wt', encoding='utf-8')
            file.write(str(html.unescape(str(schema))))
            file.close()

        server_disconnect(xr)

    @login_decorator
    def get_running_config(self):
        now = datetime.today()
        start_time = now.strftime("%d-%m-%Y-%H-%M-%S")
        create_dirs(self.path + '/xml')
        create_dirs(self.path + '/json')
        create_dir(self.path + '/xml')
        create_dir(self.path + '/json')
        logger.info("Get running configuration for device {0} : {1} started: {2}".format(
            self.device_info.sys_type, self.device_info.host, start_time))

        try:
            config_data = get_config(self.device_info)
            file = open(self.path + '/xml/' + "running_config.xml", 'w')
            file.write(config_data.data_xml)
            file.close()
            data_dict = xmltodict.parse(config_data.data_xml)
            delete_dict_elements('@xmlns', data_dict)
            json_data = json.dumps(data_dict['data'])
            json_file = open(self.path + "/json/" + "running_config.json", 'w')
            json_file.write(json_data)
            json_file.close()

        except:
            error = str(sys.exc_info())
            file = open(self.path + '/' + "ERROR-running_config.txt", 'w')
            file.write("ERROR: " + error)
            file.close()
            logger.error("Get running configuration for device {0} ERROR: {1}".
                         format(self.device_info.host, error))

        now = datetime.today()
        end_time = now.strftime("%d-%m-%Y-%H-%M-%S")

        logger.info("Get running configuration for device {0} : {1} started: {2} ended: {3}".format(
            self.device_info.sys_type, self.device_info.host, start_time, end_time))

    @login_decorator
    def get_any_path(self):
        now = datetime.today()
        start_time = now.strftime("%d-%m-%Y-%H-%M-%S")
        create_dir(self.path + '/xml')
        create_dir(self.path + '/json')
        logger.info("Get any path for device {0} : {1} started: {2}".format(
            self.device_info.sys_type, self.device_info.host, start_time))
        try:
            get_data = get_any(self.device_info, get_any_namespace, get_any_filter)
            file = open(self.path + '/xml/' + get_any_file +".xml", 'w')
            file.write(get_data.data_xml)
            file.close()
            data_dict = xmltodict.parse(get_data.data_xml)
            json_data = json.dumps(data_dict)
            json_file = open(self.path + '/json/' + get_any_file +".json", 'w')
            json_file.write(json_data)
            json_file.close()
        except:
            error = str(sys.exc_info())
            file = open(self.path + '/' + "ERROR-" + get_any_file + ".txt", 'w')
            file.write("ERROR: " + error)
        now = datetime.today()
        end_time = now.strftime("%d-%m-%Y-%H-%M-%S")

        logger.info("Get any path for device {0} : {1} started: {2} ended: {3}".format(
            self.device_info.sys_type, self.device_info.host, start_time, end_time))

    @login_decorator
    def get_path_list(self):
        now = datetime.today()
        start_time = now.strftime("%d-%m-%Y-%H-%M-%S")

        create_dir(self.path + '/xml')
        create_dir(self.path + '/json')

        logger.info("Get path list for device {0} : {1} started: {2}".format(
            self.device_info.sys_type, self.device_info.host, start_time))

        scenario_str = "Scenarios for " + self.device_info.host + " : "
        for scenario in get_netconf_path_scenarios:
            scenario_str = scenario_str + scenario.file + " "
        logger.info(scenario_str)

        for scenario in get_netconf_path_scenarios:
            if scenario.vendor != 'ietf' and scenario.vendor != 'openconfig' and \
                    scenario.vendor != self.device_info.sys_vendor: continue

            logger.info("    Scenario: {0} for device: {1}".
                        format(scenario.file, self.device_info.host))
            try:
                get_data = get_path(self.device_info, scenario.path)
                file = open(self.path + '/xml/' + scenario.file +".xml", 'w')
                file.write(get_data.data_xml)
                file.close()
                data_dict = xmltodict.parse(get_data.data_xml)
                delete_dict_elements('@xmlns', data_dict)
                json_data = json.dumps(data_dict['data'])
                json_file = open(self.path + '/json/' + scenario.file +".json", 'w')
                json_file.write(json_data)
                json_file.close()

            except:
                error = str(sys.exc_info())
                file = open(self.path + '/' + "ERROR-" + scenario.file + ".txt", 'w')
                file.write("ERROR: " + error)
                logger.error("Get path list error, Scenario: {0} for device{1} ERROR {2}:".
                             format(scenario.file, self.device_info.host, error))

        now = datetime.today()
        end_time = now.strftime("%d-%m-%Y-%H-%M-%S")

        logger.info("Get path list for device {0} : {1} started: {2} ended: {3}".format(
            self.device_info.sys_type, self.device_info.host, start_time, end_time))




