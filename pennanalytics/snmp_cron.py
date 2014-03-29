from __future__ import print_function

import json
import os
import time

import config
import snmp_fetch

interval = config.query_interval_seconds
filename = "output.json"
tmp_filename = "output.json.1"
mib_directory = os.path.join(os.path.dirname(
    os.path.realpath(__file__)), '..', 'snmp')
runfile = 'runtask'
print("Starting SNMP interval task; interval set to %d seconds" % interval)
print("Using output file %s." % filename)
print("MIB_DIRECTORY=%s" % mib_directory)


nodes = {}
while True:
    # If we're not supposed to run, check every minute to see if we've been activated
    if not os.path.isfile(runfile):
        time.sleep(60)
        continue

    with open(tmp_filename, 'w') as f:
        nodes = snmp_fetch.query_threaded(config.hosts, mib_directory, node_dict=nodes)
        f.write(json.dumps([node.serialize() for node in nodes.itervalues()]))

    os.rename(tmp_filename, filename)
    print("Wrote to %s" % filename)

    time.sleep(interval)
