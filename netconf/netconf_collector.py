from ncclient import manager
import lxml
from lxml.builder import ElementMaker
from util.external_system import ExternalSystemInfo


def server_connect(device: ExternalSystemInfo):
    netconf = manager.connect(host=device.host, port=device.port, username=device.username, password=device.password,
                              device_params={'name': device.device_handler},
                              allow_agent=False,
                              look_for_keys=False,
                              hostkey_verify=False,
                              unknown_host_cb=True,
                              manager_params={"timeout": 300})
    return netconf


def server_disconnect(netconf: manager):
    netconf.close_session()


def server_capabilities(device: ExternalSystemInfo):
    with manager.connect(host=device.host, port=device.port, username=device.username, password=device.password,
                         device_params={'name': device.device_handler},
                         allow_agent=False,
                         look_for_keys=False,
                         hostkey_verify=False,
                         unknown_host_cb=True,
                         manager_params={"timeout": 300}
                         ) as netconf:
        res = netconf.server_capabilities
        return res


def manager_server_capabilities(netconf: manager):
    res = netconf.server_capabilities
    return res


def get_schema(device: ExternalSystemInfo, schemafile: str):
    with manager.connect(host=device.host, port=device.port, username=device.username, password=device.password,
                         device_params={'name': device.device_handler},
                         allow_agent=False,
                         look_for_keys=False,
                         hostkey_verify=False,
                         unknown_host_cb=True,
                         manager_params={"timeout": 300}
                         ) as netconf:
        res = netconf.get_schema(schemafile)
        return res

def manager_get_schema(netconf: manager, schemafile: str):
        res = netconf.get_schema(schemafile)
        return res

def get_any(device: ExternalSystemInfo, namespaceA, filterA):
    with manager.connect(host=device.host, port=device.port, username=device.username, password=device.password,
                         device_params={'name': device.device_handler},
                         allow_agent=False,
                         look_for_keys=False,
                         hostkey_verify=False,
                         unknown_host_cb=True,
                         manager_params={"timeout": 300}
                         ) as netconf:
        hwdbuilder = ElementMaker(namespace=namespaceA)
        interface_filter = hwdbuilder(filterA)
        #print(lxml.etree.tostring(interface_filter, pretty_print=True).decode())
        res = netconf.get(filter=('subtree', interface_filter))
        return res


def get_path(device: ExternalSystemInfo, xml: str):
    with manager.connect(
            device_params={"name": device.device_handler},
            host=device.host,
            port=device.port,
            username=device.username,
            password=device.password,
            allow_agent=False,
            look_for_keys=False,
            hostkey_verify=False,
            unknown_host_cb=True,
            manager_params={"timeout": 300}
    ) as netconf:
        get_data = netconf.get(filter=("subtree", xml))
        return get_data

def manager_get_path(netconf: manager, xml: str):
    get_data = netconf.get(filter=("subtree", xml))
    return get_data

def manager_get_xpath(netconf: manager, xpath_prefix, xpath_namespace, xpath_select):
    get_data = netconf.get(filter=("xpath", ({xpath_prefix:  xpath_namespace}, xpath_select)))
    return get_data

def manager_get_xpath_multi(netconf: manager, xpath_value):
    get_data = netconf.get(filter=("xpath", xpath_value))
    return get_data

def get_config_path(device: ExternalSystemInfo, xml: str):
    with manager.connect(
            device_params={"name": device.device_handler},
            host=device.host,
            port=device.port,
            username=device.username,
            password=device.password,
            allow_agent=False,
            look_for_keys=False,
            hostkey_verify=False,
            unknown_host_cb=True,
            manager_params={"timeout": 300}
    ) as netconf:
        config = netconf.get_config(filter=("subtree", xml))
        return config


def get_config(router: ExternalSystemInfo):
    with manager.connect(
            device_params={"name": router.device_handler},
            host=router.host,
            port=router.port,
            username=router.username,
            password=router.password,
            allow_agent=False,
            look_for_keys=False,
            hostkey_verify=False,
            unknown_host_cb=True,
            manager_params={"timeout": 300}
    ) as netconf:
        config = netconf.get_config(source="running")
        return config


def get_any(router: ExternalSystemInfo, namespaceA, filterA):
    with manager.connect(host=router.host, port=router.port, username=router.username, password=router.password,
                         device_params={'name': router.device_handler},
                         allow_agent=False,
                         look_for_keys=False,
                         hostkey_verify=False,
                         unknown_host_cb=True,
                         manager_params={"timeout": 300}
                         ) as netconf:
        hwdbuilder = ElementMaker(namespace=namespaceA)
        interface_filter = hwdbuilder(filterA)
        #print(lxml.etree.tostring(interface_filter, pretty_print=True).decode())
        res = netconf.get(filter=('subtree', interface_filter))
        #    print(lxml.etree.tostring(res.data, pretty_print=True).decode())

        return res
