from __future__ import print_function

import os
import subprocess
import sys

import config
import lldp_parser

MIB_DIRECTORY = os.environ.get('MIB_DIRECTORY')
if MIB_DIRECTORY is None:
    print('Must specify MIB_DIRECTORY environmental variable')
    sys.exit(1)

snmp_walk_variables = [
    'IF-MIB::ifInOctets',
    'IF-MIB::ifOutOctets',
    'IF-MIB::ifSpeed',
    'LLDP-MIB::lldpRemPortId',
    'LLDP-MIB::lldpRemPortDesc',
    'LLDP-MIB::lldpRemSysName',
]
snmp_get_variables = [
    'LLDP-MIB::lldpLocSysName.0',
    'LLDP-MIB::lldpLocChassisId.0',
]


def parse_output(snmpwalk_output, snmpget_output):
    pass


for host in config.hosts:
    hostname = host['hostname']
    community = host['community']

    for var in snmp_walk_variables:
        # TODO: this raises a subprocess.CalledProcessError
        # TODO: use a better vers
        snmpwalk_output = subprocess.check_output([
            'snmpwalk',
            '-v2c',
            '-c', community,
            '-m', MIB_DIRECTORY + "/LLDP-MIB.my",
            hostname,
            var,
        ])

        snmpget_output = subprocess.check_output([
            'snmpget',
            '-v2c',
            '-c', community,
            '-m', MIB_DIRECTORY + "/LLDP-MIB.my",
            hostname,
        ] + snmp_get_variables)

        parse_output(snmpwalk_output, snmpget_output)
