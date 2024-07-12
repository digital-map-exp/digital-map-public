from util.database import DatabaseInfo

dm_directories = {
    'input': {
        'data': {
            'entities': {
                'entities': 'data/entities',
                'csv': 'data/entities/csv',
                'json': 'data/entities/json'
            }
        },
        'knowledge': {
            'knowledge': 'data/knowledge',
            'entities': 'data/knowledge/entities',
            'entities_inheritance': 'data/knowledge/entities_inheritance',
            'aggregations': 'data/knowledge/aggregations',
            'relations': 'data/knowledge/relations',
            'mapping': 'data/knowledge/mapping',
            'iag': 'data/knowledge/iag'
        }
    },
    # results with date and time stamp
    'results': {
        'results': 'results',
        'netconf': 'netconf',
        'entities': 'entities',
        'aggregations': 'aggregations',
        'relations': 'relations',
    },
    # generated files, coped from results to allow step by step execution without the timestamps
    'generated': {
        'results': 'data_generated',
        'netconf': 'data_generated/netconf',
        'entities': 'data_generated/entities',
        'aggregations': 'data_generated/aggregations',
        'relations': 'data_generated/relations',
        'yang' : 'data_generated/yang'
    }
}

# Demo digital map generation
digital_map_scenarios_configured = []
external_systems =[]

#output db for generate_db_from_files
generated_database = DatabaseInfo (
    name="default",
    uri="bolt://0.0.0.0:7687",
    user="neo4j",
    password="12345678"
)

dm_kb_entity_topology_roles = {
    "IETFNetwork": "network",
    "IETFNode": "node",
    "IETFLink": "link",
    "IETFTerminationPoint": "tp"
}

