from flask import Flask, Blueprint
from flask_restful import reqparse, abort, Api, Resource
from data import db_session
from config.secret_key import secret_key

blueprint = Blueprint(
    'arts_api',
    __name__,
    template_folder='templates'
)

app = Flask(__name__)
app.config['SECRET_KEY'] = secret_key
api = Api(app)


def main():
    db_session.global_init('db/artifacts.db')
    app.register_blueprint(arts_api.blueprint)
    app.run()


if __name__ == '__main__':
    main()
