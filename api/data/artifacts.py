import sqlalchemy
from .db_session import SqlAlchemyBase
from sqlalchemy_serializer import SerializerMixin


class Art(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'artifacts'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    name = sqlalchemy.Column(sqlalchemy.String)
    chance = sqlalchemy.Column(sqlalchemy.Integer)
    path = sqlalchemy.Column(sqlalchemy.String)
