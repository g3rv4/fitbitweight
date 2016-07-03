from flask import Flask, request, abort
from werkzeug.contrib.fixers import ProxyFix
from config import settings
import utils
import tasks

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app)

app.logger.addHandler(utils.handler)


@app.route('/', methods=['POST', 'GET'])
def callback():
    return 'ok'


@app.route('/fitbit-subscriber', methods=['POST', 'GET'])
def subscriber():
    if request.args.get('verify'):
        if request.args.get('verify') != settings['fitbit']['subscriber_endpoint_verify']:
            abort(404)
        return '', 204

    tasks.process_subscription.delay(request.data)
    return '', 204


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0")
