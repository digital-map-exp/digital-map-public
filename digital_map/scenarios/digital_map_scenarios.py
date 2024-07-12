

from config.config import dm_directories, external_systems, generated_database
from config.config_netconf import netconf_scenarios_configured, netconf_devices
from util.app_logger import get_my_logger, login_decorator

from digital_map.scenarios.generate_device_entities import generate_device_entities
from digital_map.scenarios.generate_flat_entity_types import generate_flat_entity_types
from digital_map.scenarios.generate_dm_entities import generate_dm_entities
from digital_map.scenarios.generate_dm_aggregated_entities import generate_dm_aggregated_entities
from digital_map.scenarios.generate_dm_relations import generate_dm_relations
from digital_map.scenarios.generate_db_entities import generate_db_entities
from digital_map.scenarios.generate_db_relations import generate_db_relations

logger = get_my_logger(__name__)

class DigitalMapScenarios (object):

    def __init__(self, datatime_path):
        self.__datetime_path = datatime_path

    @login_decorator
    def generate_device_entities(self):
        generate_device_entities(self.__datetime_path, dm_directories, netconf_scenarios_configured, netconf_devices)

    @login_decorator
    def generate_flat_entity_types(self):
        generate_flat_entity_types(dm_directories)

    @login_decorator
    def generate_dm_entities(self):
        generate_dm_entities(self.__datetime_path, dm_directories, netconf_devices, external_systems)

    @login_decorator
    def generate_dm_aggregated_entities(self):
        generate_dm_aggregated_entities(self.__datetime_path, dm_directories)

    @login_decorator
    def generate_dm_relations(self):
        generate_dm_relations(self.__datetime_path, dm_directories)

    @login_decorator
    def generate_db_entities(self):
        generate_db_entities(generated_database, dm_directories['generated']['entities'])

    @login_decorator
    def generate_db_relations(self):
        generate_db_relations(generated_database, dm_directories['generated']['relations'])

