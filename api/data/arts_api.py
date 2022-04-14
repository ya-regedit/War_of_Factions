from flask import Blueprint, jsonify

from .db_session import create_session
from .artifacts import Art

blueprint = Blueprint(
    'arts_api',
    __name__,
    template_folder='templates'
)


@blueprint.route('/arts')
def get_art():
    db_sess = create_session()
    arts = db_sess.query(Art).all()
    db_sess.close()
    if not arts:
        return jsonify({'error': 'Not found'})
    return jsonify(
        {'arts': [item.to_dict(only=('id', 'name', 'path', 'description', 'chance')) for item in arts]})
