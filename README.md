PennAnalytics SNMP Fetcher
==========================

Setup
-----
Full setup instructions:

    $ pip install virtualenv
    $ cd path/to/this/repo
    $ virtualenv .
    $ source bin/activate
    $ pip install -r requirements.txt

Usage
-----
The main Python script looks for a specific MIB file (LLDP-MIB.my). To specify
the location of this file, set the `MIB_DIRECTORY` environmental variable, or
run the snmp\_fetch.py as follows:

    $ MIB_DIRECTORY=path/to/mibs python snmp_fetch.py

The script also requires that the config.yaml file be properly created. See
pennanalytics/config.yaml.template for an example.
