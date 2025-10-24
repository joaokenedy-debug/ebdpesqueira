from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, FileField, SelectField
from flask_wtf.file import FileRequired, FileAllowed
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError
from ebd.models import Usuario


class FormLogin(FlaskForm):
    email = StringField( "Email", validators= [DataRequired(),Email() ])
    congregacao = SelectField ( "Congregação",
                               choices=[
            ('', 'Selecione uma congregação'),
            ('alagoinha', 'Alagoinha'),
            ('barreiras', 'Barreiras'),
            ('caixa_dagua', 'Caixa D`Agua'),
            ('carrapicho', 'Carrapicho'),
            ('central', 'Central'),
            ('lage_grande', 'Lage Grande'),
            ('mage', 'Mage'),
            ('matriz', 'Matriz'),
            ('mutuca', 'Mutuca'),
            ('pindoba', 'Pindoba'),
            ('prado', 'Prado'),
            ('sete_baraunas', 'Sete Baraunas'),
            ('socorro', 'Socorro'),
            ('vila_anapolis', 'Vila Anapolis'),
        ],
    
                               validators= [DataRequired()])
    senha = PasswordField("Senha", validators= [DataRequired()])
    botao_login = SubmitField ("Fazer Login")


class FormCriarConta(FlaskForm):
    email = StringField ( "Email", validators= [DataRequired(),Email() ])
    username = StringField ( "Nome do Usuario", validators= [DataRequired()])
    congregacao = SelectField ( "Congregação",
                               choices=[
            ('', 'Selecione uma congregação'),
            ('alagoinha', 'Alagoinha'),
            ('barreiras', 'Barreiras'),
            ('caixa_dagua', 'Caixa D`Agua'),
            ('carrapicho', 'Carrapicho'),
            ('central', 'Central'),
            ('lage_grande', 'Lage Grande'),
            ('mage', 'Mage'),
            ('matriz', 'Matriz'),
            ('mutuca', 'Mutuca'),
            ('pindoba', 'Pindoba'),
            ('prado', 'Prado'),
            ('sete_baraunas', 'Sete Baraunas'),
            ('socorro', 'Socorro'),
            ('vila_anapolis', 'Vila Anapolis'),
        ],
    
                               validators= [DataRequired()])
    senha = PasswordField ("Senha", validators=[DataRequired(),  Length(6,20)])
    confirma_senha = PasswordField ("Confirmação de Senha", validators=[DataRequired(), EqualTo("senha")])
    botao_criar = SubmitField("Criar Conta")
     
    def validate_email(self, email):
        usuario = Usuario.query.filter_by(email=email.data).first()
        if usuario :
           return ValidationError ("E-mail já cadastrado")




