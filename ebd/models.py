from datetime import datetime
from flask_login import UserMixin
from sqlalchemy import Identity
from ebd import database, login_manager


# =========================
# LOGIN
# =========================
@login_manager.user_loader
def load_usuario(id_usuario):
    return Usuario.query.get(int(id_usuario))


# =========================
# USUARIO
# =========================
class Usuario(database.Model, UserMixin):
    __tablename__ = "usuario"

    id = database.Column(
        database.Integer,
        Identity(),
        primary_key=True
    )

    usarname = database.Column(database.String, nullable=False)
    email = database.Column(database.String, nullable=False)
    congregacao = database.Column(database.String, nullable=False)
    senha = database.Column(database.String, nullable=False)
    is_admin = database.Column(database.Boolean, default=False)

    pedidos = database.relationship("Pedido", back_populates="usuario")


# =========================
# PEDIDO
# =========================
class Pedido(database.Model):
    __tablename__ = "pedido"

    id = database.Column(
        database.Integer,
        Identity(),
        primary_key=True
    )

    id_usuario = database.Column(
        database.Integer,
        database.ForeignKey("usuario.id"),
        nullable=False
    )

    congregacao = database.Column(database.String, nullable=False)
    data = database.Column(database.DateTime, default=datetime.utcnow)
    total = database.Column(database.Float, nullable=False)

    usuario = database.relationship("Usuario", back_populates="pedidos")

    itens = database.relationship(
        "ItemPedido",
        back_populates="pedido",
        cascade="all, delete-orphan"
    )

    pagamentos = database.relationship(
        "Pagamento",
        back_populates="pedido",
        cascade="all, delete-orphan"
    )

    @property
    def total_pago(self):
        return sum(p.valor_pago for p in self.pagamentos)

    @property
    def saldo_restante(self):
        return self.total - self.total_pago

    @property
    def quitado(self):
        return self.saldo_restante <= 0


# =========================
# ITEM_PEDIDO
# =========================
class ItemPedido(database.Model):
    __tablename__ = "item_pedido"

    id = database.Column(
        database.Integer,
        Identity(),
        primary_key=True
    )

    id_pedido = database.Column(
        database.Integer,
        database.ForeignKey("pedido.id"),
        nullable=False
    )

    produto = database.Column(database.String, nullable=False)
    codigo = database.Column(database.Integer, nullable=False)
    quantidade = database.Column(database.Integer, nullable=False)
    preco_unitario = database.Column(database.Float, nullable=False)
    subtotal = database.Column(database.Float, nullable=False)

    pedido = database.relationship("Pedido", back_populates="itens")


# =========================
# CAIXA
# =========================
class Caixa(database.Model):
    __tablename__ = "caixa"

    id = database.Column(
        database.Integer,
        Identity(),
        primary_key=True
    )

    descricao = database.Column(database.String(200), nullable=False)
    valor = database.Column(database.Float, nullable=False)
    data = database.Column(database.DateTime, default=datetime.utcnow)

    # 👇 CAMPO NOVO (opcional, só para pagamentos)
    id_pedido = database.Column(
        database.Integer,
        database.ForeignKey("pedido.id"),
        nullable=True
    )


# =========================
# PAGAMENTO
# =========================
class Pagamento(database.Model):
    __tablename__ = "pagamento"

    id = database.Column(
        database.Integer,
        Identity(),
        primary_key=True
    )

    id_pedido = database.Column(
        database.Integer,
        database.ForeignKey("pedido.id"),
        nullable=False
    )

    valor_pago = database.Column(database.Float, nullable=False)
    data = database.Column(database.DateTime, default=datetime.utcnow)

    pedido = database.relationship("Pedido", back_populates="pagamentos")

