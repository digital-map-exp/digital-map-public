
from concurrent.futures import ThreadPoolExecutor, as_completed
from config.config_netconf import netconf_devices, netconf_scenarios_configured
from netconf.netconf_scenarios import netconf_scenarios
from util.app_logger import get_my_logger, login_decorator
logger = get_my_logger(__name__)

def network_discovery(netconf_devices, netconf_path):
    logger.info("Execution Steps: {0}".format(netconf_scenarios_configured))
    futures = []
    with ThreadPoolExecutor() as ex:
        for device in netconf_devices:
            device_path = netconf_path + '/' + device.sys_type + "-" + device.host
            futures.append(ex.submit(discover_device,device_path,device))

        for future in as_completed(futures):
            logger.info(future.result())

def discover_device(device_path, device):
    for scenario in netconf_scenarios_configured:
        doSomething = getattr(netconf_scenarios, scenario)
        doSomething(netconf_scenarios(device_path, device))
    return ("Discovery finished for the host {0}".format(device.host))
