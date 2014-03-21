from flask import Flask
from flask import jsonify
import os

import config
import snmp_fetch

app = Flask(__name__)
MIB_DIRECTORY = os.environ.get('MIB_DIRECTORY')

@app.route("/all")
def fetch_all_data():
    nodes = snmp_fetch.query(config.hosts, MIB_DIRECTORY)
    return jsonify(results=[node.serialize() for node in nodes])


if __name__ == '__main__':
    app.run(debug=True)
