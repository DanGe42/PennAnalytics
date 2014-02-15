from __future__ import print_function

import os
import re
import subprocess

from common import NetworkNode
from common import NetworkStats
from snmp_oids import IF_MIB
from snmp_oids import LLDP_MIB


snmp_walk_variables = [
    IF_MIB.ifInOctets,
    IF_MIB.ifOutOctets,
    IF_MIB.ifSpeed,
    LLDP_MIB.lldpRemPortId,
    LLDP_MIB.lldpRemPortDesc,
    LLDP_MIB.lldpRemSysName,
]
snmp_get_variables = [
    LLDP_MIB.lldpLocSysName_0,
    LLDP_MIB.lldpLocChassisId_0,
]


OID_VALUE_PATTERN = re.compile(r'(.+) = (.+?):\s*(.+)?')
LLDP_OID_SPLIT = re.compile(r'([a-zA-Z0-9:\-]+)\.\d+\.(\d+)\.\d+')
IF_MIB_SPLIT = re.compile(r'([a-zA-Z0-9:\-]+)\.(\d+)')


def parse_snmp_line(line):
    match_data = OID_VALUE_PATTERN.match(line.rstrip())
    if not match_data:
        return None

    return match_data.groups()


def parse_oid_port(regex, oid):
    match_data = regex.match(oid.rstrip())
    if not match_data:
        return None
    return match_data.groups()


def parse_output(snmpwalk_output, snmpget_output):
    sys_name = None
    for line in snmpget_output.split('\n'):
        parsed = parse_snmp_line(line)
        if parsed is None:
            continue
        oid, typ, value = parsed

        if oid == LLDP_MIB.lldpLocSysName_0:
            sys_name = value

    node = NetworkNode(sys_name)

    remote_sys_names = {}
    link_bytes_recv = {}
    link_bytes_sent = {}
    link_speed = {}

    for line in snmpwalk_output.split('\n'):
        parsed = parse_snmp_line(line)
        if parsed is None:
            continue
        oid, typ, value = parsed

        if oid.startswith('LLDP-MIB'):
            oid_prefix, port = parse_oid_port(LLDP_OID_SPLIT, oid)
            if oid_prefix == LLDP_MIB.lldpRemSysName:
                remote_sys_names[port] = value
        elif oid.startswith('IF-MIB'):
            oid_prefix, port = parse_oid_port(IF_MIB_SPLIT, oid)
            if oid_prefix == IF_MIB.ifOutOctets:
                link_bytes_sent[port] = int(value)
            elif oid_prefix == IF_MIB.ifInOctets:
                link_bytes_recv[port] = int(value)
            elif oid_prefix == IF_MIB.ifSpeed:
                link_speed[port] = int(value)

    for port in remote_sys_names:
        rem_sys_name = remote_sys_names[port]
        capacity = link_speed[port]
        stats = NetworkStats(
            bytes_recv=link_bytes_recv[port],
            bytes_sent=link_bytes_sent[port],
        )
        node.add_remote(port, rem_sys_name, capacity, stats=stats)

    return node


def query(hosts, mib_directory):
    for host in hosts:
        hostname = host['hostname']
        community = host['community']

        snmpwalk_output = ''.join(subprocess.check_output([
            'snmpwalk',
            '-v2c',
            '-c', community,
            '-m', mib_directory + "/LLDP-MIB.my",
            hostname,
            var,
        ]) for var in snmp_walk_variables)

        snmpget_output = subprocess.check_output([
            'snmpget',
            '-v2c',
            '-c', community,
            '-m', mib_directory + "/LLDP-MIB.my",
            hostname,
        ] + snmp_get_variables)

        node = parse_output(snmpwalk_output, snmpget_output)
        print(node)


if __name__ == '__main__':
    import config
    import sys

    MIB_DIRECTORY = os.environ.get('MIB_DIRECTORY')
    if MIB_DIRECTORY is None:
        print('Must specify MIB_DIRECTORY environmental variable')
        sys.exit(1)

    query(config.hosts, MIB_DIRECTORY)
