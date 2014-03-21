from __future__ import print_function

import json
import os
import time

import config
import snmp_fetch

interval = 10
print("Starting SNMP interval task; interval set to %d seconds" % interval)
filename = "output.json"
print("Using output file %s." % filename)
mib_directory = os.environ.get("MIB_DIRECTORY")
print("MIB_DIRECTORY=%s" % mib_directory)


while True:
    with open(filename, 'w') as f:
        nodes = snmp_fetch.query_threaded(config.hosts, mib_directory)
        f.write(json.dumps([node.serialize() for node in nodes]))
        print("Wrote to %s" % filename)

    time.sleep(interval)
