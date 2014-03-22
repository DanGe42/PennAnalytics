from __future__ import print_function

import os
import re
import subprocess
import sys
import threading

from common import NetworkNode
from config import snmp_get_vars
from config import snmp_walk_vars
from snmp_oids import IF_MIB
from snmp_oids import LLDP_MIB

OID_VALUE_PATTERN = re.compile(r'(.+) = (.+?):\s*(.+)?')
LLDP_OID_SPLIT = re.compile(r'([a-zA-Z0-9:\-]+)\.\d+\.(\d+)\.\d+')
IF_MIB_SPLIT = re.compile(r'([a-zA-Z0-9:\-]+)\.(\d+)')


def parse_snmp_line(line):
    """ Parse an Net-SNMP command output line into a OID-type-value tuple.

    :param line: A Net-SNMP output line
    :return: A tuple (oid, type, value) for each Net-SNMP line
    """
    match_data = OID_VALUE_PATTERN.match(line.rstrip())
    if not match_data:
        return None

    return match_data.groups()


def parse_oid_port(regex, oid):
    """ Parse an OID into an OID-port tuple using a specified regex. The LLDP_OID_SPLIT regex
    is useful for LLDP-MIB OIDs, and the IF_MIB_SPLIT regex is useful for IF-MIB OIDs.

    :param regex: An OID-port splitting regex
    :param oid: The OID to parse
    :return: A tuple (base oid, port)
    """
    match_data = regex.match(oid.rstrip())
    if not match_data:
        return None
    return match_data.groups()


def parse_output(snmpwalk_output, snmpget_output):
    """ Parse the output of the snmpwalk and snmpget commands on a single network node into
    a NetworkNode object.

    :param snmpwalk_output: The output of the snmpwalk command on all desired variables.
    :param snmpget_output: The output of the snmpget command on all desired variables.
    :return: A NetworkNode object
    """
    sys_name = None
    physical_addr = None

    # Parse the snmpget output
    for line in snmpget_output.split('\n'):
        parsed = parse_snmp_line(line)
        if parsed is None:
            continue
        oid, typ, value = parsed

        if oid == LLDP_MIB.lldpLocSysName_0:
            sys_name = value
        if oid == LLDP_MIB.lldpLocChassisId_0:
            physical_addr = value

    node = NetworkNode(sys_name, physical_addr)

    remote_sys_names = {}
    link_bytes_recv = {}
    link_bytes_sent = {}
    link_speed = {}

    # Parse the snmpwalk output (which is probably the output of all snmpwalk commands
    # joined into one string)
    for line in snmpwalk_output.split('\n'):
        parsed = parse_snmp_line(line)
        if parsed is None:
            continue
        oid, typ, value = parsed

        # LLDP values
        if oid.startswith('LLDP-MIB'):
            oid_prefix, port = parse_oid_port(LLDP_OID_SPLIT, oid)
            if oid_prefix == LLDP_MIB.lldpRemSysName:
                remote_sys_names[port] = value

        # IF values
        elif oid.startswith('IF-MIB'):
            oid_prefix, port = parse_oid_port(IF_MIB_SPLIT, oid)
            if oid_prefix == IF_MIB.ifOutOctets:
                link_bytes_sent[port] = int(value)
            elif oid_prefix == IF_MIB.ifInOctets:
                link_bytes_recv[port] = int(value)
            elif oid_prefix == IF_MIB.ifSpeed:
                link_speed[port] = int(value)

    # Aggregate all remote data stored in the dictionaries
    for port in remote_sys_names:
        rem_sys_name = remote_sys_names.get(port, None)
        capacity = link_speed.get(port, -1)
        node.add_remote(port, rem_sys_name, capacity)

        bytes_recv = link_bytes_recv.get(port, 0)
        bytes_sent = link_bytes_sent.get(port, 0)
        link = node[port]
        link.update(bytes_recv, bytes_sent)

    return node


def _fetch_node_info(host, mib_directory):
    hostname = host['hostname']
    community = host['community']

    snmpwalk_output = ''
    for var in snmp_walk_vars:
        try:
            snmpwalk_output += subprocess.check_output([
                'snmpwalk',
                '-v2c',
                '-c', community,
                '-m', mib_directory + "/LLDP-MIB.my",
                hostname,
                var,
            ])
        except subprocess.CalledProcessError as e:
            print(e.message, file=sys.stderr)

    snmpget_output = subprocess.check_output([
        'snmpget',
        '-v2c',
        '-c', community,
        '-m', mib_directory + "/LLDP-MIB.my",
        hostname,
    ] + snmp_get_vars)

    return parse_output(snmpwalk_output, snmpget_output)


class SnmpTask(threading.Thread):

    _nodelist_lock = threading.Lock()

    def __init__(self, host, mib_directory, node_dict):
        super(SnmpTask, self).__init__()
        self.host = host
        self.mib_directory = mib_directory
        self.node_dict = node_dict

    def run(self):
        node = _fetch_node_info(self.host, self.mib_directory)
        with self.__class__._nodelist_lock:
            physical_addr = node.physical_addr
            if physical_addr not in self.node_dict:
                self.node_dict[physical_addr] = node
            else:
                for port, link in self.node_dict[physical_addr].iteritems():
                    # TODO: what happens if port no longer exists
                    if port in node:
                        new_link = node[port]
                        link.update(new_link.bytes_recv, new_link.bytes_sent)


def query_threaded(hosts, mib_directory, node_dict=None):
    node_dict = node_dict or {}
    threads = [SnmpTask(host, mib_directory, node_dict) for host in hosts]
    for th in threads:
        th.start()
    for th in threads:
        th.join()

    return node_dict


if __name__ == '__main__':
    import config

    MIB_DIRECTORY = os.environ.get('MIB_DIRECTORY')
    if MIB_DIRECTORY is None:
        print('Must specify MIB_DIRECTORY environmental variable')
        sys.exit(1)

    print(query(config.hosts, MIB_DIRECTORY))
