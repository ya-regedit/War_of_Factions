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
    art = db_sess.query(Art).all()
    if not art:
        return jsonify({'error': 'Not found'})
    return jsonify(
        {'arts': [item.to_dict(only=('name', 'path', 'description')) for item in art]})
