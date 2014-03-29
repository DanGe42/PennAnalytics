from flask import Flask
from flask import jsonify
from flask import Response
from flask import request
import os

import config

app = Flask(__name__)
MIB_DIRECTORY = os.path.join(os.path.dirname(
    os.path.realpath(__file__)), '..', 'snmp')

RUNFILE = 'runtask'

@app.route("/all", methods=['GET'])
def fetch_all_data():
    with open("output.json", 'r') as f:
        data = f.read()
    return Response(data, mimetype="application/json")


# This is meant to be a convenience method for me, since the RPi is firewalled off.
# FIXME: REMOVE THIS FUNCTION IN PRODUCTION CODE
@app.route("/manage", methods=['POST'])
def manage():
    passkey = request.form['passkey']
    if passkey == config.creds['passkey']:
        # The "background" task will check for the presence of the 'runtask' file.
        action = request.form['action']
        if action == 'stop':
            if not os.path.isfile(RUNFILE):
                message = "Failure (not running already)"
            else:
                os.remove(RUNFILE)
                message = "Success" if not os.path.isfile(RUNFILE) else "Failure"

        elif action == 'run':
            if os.path.isfile(RUNFILE):
                message = "Failure (already running)"
            else:
                open(RUNFILE, 'a').close()
                message = "Success" if os.path.isfile(RUNFILE) else "Failure"

        else:
            message = "Invalid action"
    else:
        message = "Invalid passkey"

    return jsonify(message=message)


if __name__ == '__main__':
    app.run(debug=True)
