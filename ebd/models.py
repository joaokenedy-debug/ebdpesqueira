from ebd import database, login_manager
from datetime import datetime
from flask_login import UserMixin

@login_manager.user_loader
def load_usuario(id_usuario):
    return Usuario.query.get(int(id_usuario))


class Usuario(database.Model, UserMixin):
    __tablename__ = "usuario"
    id = database.Column(database.Integer , primary_key = True)
    usarname = database.Column(database.String, nullable=False)
    email = database.Column(database.String, nullable=False)
    congregacao = database.Column(database.String, nullable=False)
    senha = database.Column(database.String, nullable=False)
    is_admin = database.Column(database.Boolean, default=False) 

class Pedido(database.Model):
    __tablename__ = "pedido"
    id = database.Column(database.Integer, primary_key=True)
    id_usuario = database.Column(database.Integer, database.ForeignKey("usuario.id"), nullable=False)
    congregacao = database.Column(database.String, nullable=False)
    data = database.Column(database.DateTime, default=datetime.utcnow)
    total = database.Column(database.Float, nullable=False)

    itens = database.relationship("ItemPedido", backref="pedido", cascade="all, delete-orphan", lazy=True)
    usuario = database.relationship("Usuario", backref="pedidos")
    @property
    def total_pago(self):
        return sum(p.valor_pago for p in self.pagamentos)

    @property
    def saldo_restante(self):
        return self.total - self.total_pago

    @property
    def quitado(self):
        return self.saldo_restante <= 0

class ItemPedido(database.Model):
    __tablename__ = "item_pedido"
    id = database.Column(database.Integer, primary_key=True)
    id_pedido = database.Column(database.Integer, database.ForeignKey("pedido.id"), nullable=False)
    produto = database.Column(database.String, nullable=False)
    codigo = database.Column(database.Integer, nullable=False)
    quantidade = database.Column(database.Integer, nullable=False)
    preco_unitario = database.Column(database.Float, nullable=False)
    subtotal = database.Column(database.Float, nullable=False)
class Caixa(database.Model):
    __tablename__ = "caixa"
    id = database.Column(database.Integer, primary_key=True)
    descricao = database.Column(database.String(200), nullable=False)
    valor = database.Column(database.Float, nullable=False)
    data = database.Column(database.DateTime, default=datetime.utcnow)
class Pagamento(database.Model):
    id = database.Column(database.Integer, primary_key=True)
    id_pedido = database.Column(database.Integer, database.ForeignKey("pedido.id"), nullable=False)
    valor_pago = database.Column(database.Float, nullable=False)
    data = database.Column(database.DateTime, default=datetime.utcnow)

    pedido = database.relationship("Pedido", backref="pagamentos")



