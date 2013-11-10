from __future__ import (
    absolute_import,
    print_function,
)

from collections import defaultdict
import json
import re
import sys


# Base fields from the LLDP Management Information Base
MIB_FIELDS = {
    'lldpLocSysName':        'iso.0.8802.1.1.2.1.3.3',
    'lldpLocChassisId':      'iso.0.8802.1.1.2.1.3.2',
    'lldpRemoteSystemsData': 'iso.0.8802.1.1.2.1.4',
}

# Specific fields in the lldpRemoteSystemsData configuration data
# The full field name is
# MIB_FIELDS['lldpRemoteSystemsData'] + '.' + REMOTE_FIELDS[...]
REMOTE_FIELDS = {
    'lldpRemPortID':   '1.1.7',
    'lldpRemPortDesc': '1.1.8',
    'lldpRemSysName':  '1.1.9',
}

# RegExp pattern for matching each SNMP line
ATTR_VALUE_PATTERN = re.compile(r'(.+) = (.+?): (.+)')

# LLDP data types
HEX_STRING_TYPE = 'Hex-STRING'
STRING_TYPE = 'STRING'
INTEGER_TYPE = 'INTEGER'


class SwitchSnmpInfo(object):

    def __init__(self, sys_name):
        self.sys_name = sys_name.strip('"')
        self._chassis_id = None
        self._remote_system_data = defaultdict(dict)

    @property
    def chassis_id(self):
        return self._chassis_id

    @chassis_id.setter
    def chassis_id(self, type_value_tuple):
        typ, value = type_value_tuple
        if typ == HEX_STRING_TYPE:
            self._chassis_id = value.replace(' ', ':')
        elif typ == STRING_TYPE:
            self._chassis_id = value.strip('"')
        else:
            raise ValueError('Invalid type %s' % typ)

    def set_remote_data(self, port, key, typ, value):
        if key in self._remote_system_data[port]:
            print('WARN: Key "%s" already exists with port %d' % (key, port),
                  file=sys.stderr)
            print(self.sys_name, file=sys.stderr)

        if typ == INTEGER_TYPE:
            value = int(value)
        elif typ == STRING_TYPE:
            value = value.strip('"')

        self._remote_system_data[port][key] = (typ, value)

    def get_remote_data(self, port, key):
        if port not in self._remote_system_data:
            raise ValueError('Port %d not found in remote system data' % port)
        return self._remote_system_data[port][key]

    def get_remote_ports(self):
        return self._remote_system_data.keys()

    def get_remote_systems(self):
        return self._remote_system_data.values()

    def get_remote_system_names(self):
        remote_systems = []
        for _, remote_data in self._remote_system_data.iteritems():
            if 'lldpRemSysName' in remote_data:
                _, remote_sys_name = remote_data['lldpRemSysName']
                remote_systems.append(remote_sys_name)
        return remote_systems

    def __str__(self):
        return '%s (%s) => %s' % \
            (self.sys_name, self.chassis_id, self._remote_system_data)

    def as_dict(self):
        info_dict = {
            'sys_name': self.sys_name,
            'chassis_id': self.chassis_id,
        }

        info_dict['remote_system_data'] = None
        if self._remote_system_data:
            remote_dict = defaultdict(dict)
            for port, remote_data in self._remote_system_data.iteritems():
                for sub_field, (typ, value) in remote_data.iteritems():
                    remote_dict[port][sub_field] = {
                        'type': typ,
                        'value': value,
                    }
            info_dict['remote_system_data'] = remote_dict

        return info_dict


def parse_snmp_file(filename):
    switches = []
    with open(filename, 'r') as f:
        # If this parser crashes with a NoneType error, then we can't assume
        # that the data always comes in a name->chassis->configuration order
        switch = None
        for line in f:
            match_data = ATTR_VALUE_PATTERN.match(line.rstrip())
            if not match_data:
                continue

            field_id, typ, value = match_data.groups()
            if field_id.startswith(MIB_FIELDS['lldpLocSysName']):
                switch = SwitchSnmpInfo(value)
                switches.append(switch)
            elif field_id.startswith(MIB_FIELDS['lldpLocChassisId']):
                switch.chassis_id = (typ, value)
            elif field_id.startswith(MIB_FIELDS['lldpRemoteSystemsData']):
                # Add 1 to cut off the leading period.
                sub_start_idx = len(MIB_FIELDS['lldpRemoteSystemsData']) + 1
                subfield = field_id[sub_start_idx:]
                _process_remote_data(switch, subfield, typ, value)
            else:
                print('WARN: Could not match "%s"' % line, file=sys.stderr)

    return switches


def _process_remote_data(switch, subfield, typ, value):
    for readable_name, config_name in REMOTE_FIELDS.iteritems():
        if subfield.startswith(config_name):
            # Add 1 to cut off leading period
            metadata = subfield[len(config_name) + 1:]

            port = int(metadata.split('.')[1])
            switch.set_remote_data(port, readable_name, typ, value)
            return


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: %s file" % sys.argv[0])
        sys.exit(1)

    switches = parse_snmp_file(sys.argv[1])
    print(json.dumps([switch.as_dict() for switch in switches]))
