from netconf.netconf_scenario_definition import netconf_scenario_definition

openconfig_system= netconf_scenario_definition(
    vendor="openconfig",
    path="""<ns0:system xmlns:ns0="http://openconfig.net/yang/system"/>""",
    file="openconfig-system"
)

openconfig_interfaces= netconf_scenario_definition(
    vendor="openconfig",
    path="""<ns0:interfaces xmlns:ns0="http://openconfig.net/yang/interfaces"/>""",
    file="openconfig-interfaces"
)

openconfig_lldp= netconf_scenario_definition(
    vendor="openconfig",
    path="""<ns0:lldp xmlns:ns0="http://openconfig.net/yang/lldp"/>""",
    file="openconfig-lldp"
)

openconfig_network_instance= netconf_scenario_definition(
    vendor="openconfig",
    path="""<ns0:network-instances xmlns:ns0="http://openconfig.net/yang/network-instance"/>""",
    file="openconfig-network-instance"
)

openconfig_routing_policy= netconf_scenario_definition(
    vendor="openconfig",
    path="""<ns0:routing-policy xmlns:ns0="http://openconfig.net/yang/routing-policy"/>""",
    file="openconfig-routing-policy"
)

openconfig_platform= netconf_scenario_definition(
    vendor="openconfig",
    path="""<ns0:components xmlns:ns0="http://openconfig.net/yang/platform"/>""",
    file="openconfig-platform"
)

openconfig_telemetry= netconf_scenario_definition(
    vendor="openconfig",
    path="""<ns0:telemetry-system xmlns:ns0="http://openconfig.net/yang/telemetry"/>""",
    file="openconfig-telemetry"
)


