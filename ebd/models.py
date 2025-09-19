from ebd import database, login_manager
from datetime import datetime
from flask_login import UserMixin

@login_manager.user_loader
def load_usuario(id_usuario):
    return Usuario.query.get(int(id_usuario))


class Usuario(database.Model, UserMixin):
    id = database.Column(database.Integer , primary_key = True)
    usarname = database.Column(database.String, nullable=False)
    email = database.Column(database.String, nullable=False)
    congregacao = database.Column(database.String, nullable=False)
    senha = database.Column(database.String, nullable=False)
    fotos = database.relationship("Foto", backref="usuario", lazy=True, uselist=True)
    is_admin = database.Column(database.Boolean, default=False) 

class Foto(database.Model):
    id = database.Column(database.Integer , primary_key = True)
    imagem = database.Column(database.String, default = "default.png")
    data_criacao = database.Column(database.DateTime, default=datetime.utcnow, nullable=False )
    id_usuario = database.Column(database.Integer, database.ForeignKey('usuario.id') ,nullable=False)