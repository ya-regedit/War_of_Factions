from flask import Flask
from flask_restful import Api
from data import db_session
from config.secret_key import secret_key
import data.arts_api as arts_api

app = Flask(__name__)
app.config['SECRET_KEY'] = secret_key
api = Api(app)


def main():
    db_session.global_init('db/artifacts.db')
    app.register_blueprint(arts_api.blueprint)
    app.run()


if __name__ == '__main__':
    main()
