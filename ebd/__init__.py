from flask import Flask, render_template, request, redirect, url_for, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from flask_migrate import Migrate
import os
from dotenv import load_dotenv


load_dotenv()  # Garante que o .env é carregado
app = Flask(__name__)
DATABASE_URL = "postgresql://ebd_pesqueira:8Qyd9NhFX7aCf0deinskEuJdJyH8Enbx@dpg-d4493te3jp1c739egngg-a/bd_ebdpesqueira_1eie"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config["SECRET_KEY"] = "193c5a16"
app.config["UPLOAD_FOLDER"] = "static/pedidos"

database = SQLAlchemy(app)
migrate = Migrate(app, database)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = "home"

# === Cria as tabelas se não existirem ===
with app.app_context():
    database.create_all()
    print("Tabelas criadas (se ainda não existiam)")

# Importa as rotas após inicializar o banco
from ebd import routes







