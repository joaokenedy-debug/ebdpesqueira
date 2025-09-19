from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, FileField
from flask_wtf.file import FileRequired, FileAllowed
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError
from ebd.models import Usuario, Foto


class FormLogin(FlaskForm):
    email = StringField( "Email", validators= [DataRequired(),Email() ])
    congregacao = StringField ( "Congregação", validators= [DataRequired()])
    senha = PasswordField("Senha", validators= [DataRequired()])
    botao_login = SubmitField ("Fazer Login")


class FormCriarConta(FlaskForm):
    email = StringField ( "Email", validators= [DataRequired(),Email() ])
    username = StringField ( "Nome do Usuario", validators= [DataRequired()])
    congregacao = StringField ( "Congregação", validators= [DataRequired()])
    senha = PasswordField ("Senha", validators=[DataRequired(),  Length(6,20)])
    confirma_senha = PasswordField ("Confirmação de Senha", validators=[DataRequired(), EqualTo("senha")])
    botao_criar = SubmitField("Criar Conta")
     
    def validate_email(self, email):
        usuario = Usuario.query.filter_by(email=email.data).first()
        if usuario :
           return ValidationError ("E-mail já cadastrado")

class FormFoto(FlaskForm):
    foto= FileField("Foto", validators=[DataRequired(), 
                                        FileRequired(),
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Apenas imagens são permitidas!')])
    botao_enviar=SubmitField("Enviar Fotos")        