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
            ('Alagoinha', 'Alagoinha'),
            ('Barreiras', 'Barreiras'),
            ('Caixa_dagua', 'Caixa D`Agua'),
            ('Carrapicho', 'Carrapicho'),
            ('Central', 'Central'),
            ('Lage_grande', 'Lage Grande'),
            ('Mage', 'Mage'),
            ('Matriz', 'Matriz'),
            ('Mutuca', 'Mutuca'),
            ('Pindoba', 'Pindoba'),
            ('Prado', 'Prado'),
            ('Sete_baraunas', 'Sete Baraunas'),
            ('Socorro', 'Socorro'),
            ('Vila_anapolis', 'Vila Anapolis'),
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
            ('Alagoinha', 'Alagoinha'),
            ('Barreiras', 'Barreiras'),
            ('Caixa_dagua', 'Caixa D`Agua'),
            ('Carrapicho', 'Carrapicho'),
            ('Central', 'Central'),
            ('Lage_grande', 'Lage Grande'),
            ('Mage', 'Mage'),
            ('Matriz', 'Matriz'),
            ('Mutuca', 'Mutuca'),
            ('Pindoba', 'Pindoba'),
            ('Prado', 'Prado'),
            ('Sete_baraunas', 'Sete Baraunas'),
            ('Socorro', 'Socorro'),
            ('Vila_anapolis', 'Vila Anapolis'),
        ],
    
                               validators= [DataRequired()])
    senha = PasswordField ("Senha", validators=[DataRequired(),  Length(6,20)])
    confirma_senha = PasswordField ("Confirmação de Senha", validators=[DataRequired(), EqualTo("senha")])
    botao_criar = SubmitField("Criar Conta")
     
    def validate_email(self, email):
        usuario = Usuario.query.filter_by(email=email.data).first()
        if usuario :
           return ValidationError ("E-mail já cadastrado")





