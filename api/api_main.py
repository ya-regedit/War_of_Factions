import os

from flask import Flask
from flask_restful import Api
from data import db_session
import data.arts_api as arts_api

app = Flask(__name__)
api = Api(app)


def main():
    db_session.global_init('db/artifacts.db')
    app.register_blueprint(arts_api.blueprint)


if __name__ == '__main__':
    main()
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
