import os

import yaml


# Get the directory path of this file
def _path_with_filename(filename):
    base_path = os.path.dirname(os.path.realpath(__file__))
    return os.path.join(base_path, filename)


# Expose SNMP hosts information
with open(_path_with_filename('hosts.yaml'), 'r') as f:
    hosts = yaml.safe_load(f)['hosts']


# Expose SNMP variables that we'd like to access
with open(_path_with_filename('snmp_vars.yaml'), 'r') as f:
    _vars = yaml.safe_load(f)
    snmp_walk_vars = _vars['walk']
    snmp_get_vars = _vars['get']
