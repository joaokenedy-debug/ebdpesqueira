from ebd import database, app
from ebd.models import Usuario, Foto

with app.app_context():
    database.create_all()