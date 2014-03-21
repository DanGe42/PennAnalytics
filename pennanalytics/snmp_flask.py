from flask import Flask
from flask import Response
import os

import config
import snmp_fetch

app = Flask(__name__)
MIB_DIRECTORY = os.environ.get('MIB_DIRECTORY')

@app.route("/all")
def fetch_all_data():
    with open("output.json", 'r') as f:
        data = f.read()
    return Response(data, mimetype="application/json")


if __name__ == '__main__':
    app.run(debug=True)
