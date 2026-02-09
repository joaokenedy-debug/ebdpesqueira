from flask import render_template, url_for, redirect, session, request,  send_file, flash,send_from_directory
from ebd import app, database, bcrypt
from ebd.models import Usuario, Pedido, ItemPedido, Caixa, Pagamento
from flask_login import login_required,login_user, logout_user, current_user
from ebd.forms import FormLogin, FormCriarConta, FormRecuperarSenha, FormRedefinirSenha
import os
from datetime import datetime,timedelta
from werkzeug.utils import secure_filename
import pandas as pd
from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import Spacer
from reportlab.lib.styles import getSampleStyleSheet
from sqlalchemy import func, or_




app.secret_key = "123a41bc23"  # Necessário para usar session

# Lista de produtos
df = pd.read_excel("ebd/static/lista de revistas.xlsx") 
produtos = df.to_dict(orient="records")
#print (produtos)
PDF_FOLDER = os.path.join(app.root_path, 'static', 'pdf')



@app.route("/")
def home():
    return render_template("home.html", produtos=produtos)

@app.route("/adicionar", methods=["GET","POST"])
def adicionar():
    produto_id = int(request.form["produto_id"])
    quantidade = int(request.form["quantidade"])

    # Pega o carrinho da sessão, ou cria um novo
    carrinho = session.get("carrinho", {})

    # Se já existe o produto no carrinho, soma a quantidade
    if str(produto_id) in carrinho:
        carrinho[str(produto_id)] = quantidade
    else:
        carrinho[str(produto_id)] = quantidade

    # Salva o carrinho na sessão
    session["carrinho"] = carrinho

    return redirect(url_for("perfil", id_usuario=current_user.id))

@app.route("/carrinho")
def ver_carrinho():
    carrinho = session.get("carrinho", {})
    itens = []
    total = 0

    for produto in produtos:
        pid = str(produto["id"])
        if pid in carrinho:
            qtd = carrinho[pid]
            subtotal = produto["preco"] * qtd
            total += subtotal
            itens.append({"nome": produto["nome"], "quantidade": qtd, "subtotal": subtotal})

    return render_template("carrinho.html", itens=itens, total=total)
from datetime import datetime, timedelta

@app.route("/finalizar", methods=["POST"])
@login_required
def finalizar():
    carrinho = session.get("carrinho", {})
    if not carrinho:
        return redirect(url_for("ver_carrinho"))

    itens_excel = []
    total = 0

    for produto in produtos:
        pid = str(produto["id"])
        if pid in carrinho:
            qtd = carrinho[pid]
            subtotal = produto["preco"] * qtd
            total += subtotal
            itens_excel.append({
                "Produto": produto["nome"],
                "ID": produto["id"],
                "Quantidade": qtd,
                "Preço Unitário": produto["preco"],
                "Subtotal": subtotal
            })

    # --- SALVAR PEDIDO ---
    novo_pedido = Pedido(
        usuario=current_user,   # 👈 RELACIONAMENTO
        congregacao=current_user.congregacao,
        total=total
    )

    # --- ITENS ---
    for item in itens_excel:
        novo_pedido.itens.append(
            ItemPedido(
                produto=item["Produto"],
                codigo=item["ID"],
                quantidade=item["Quantidade"],
                preco_unitario=item["Preço Unitário"],
                subtotal=item["Subtotal"]
            )
        )

    database.session.add(novo_pedido)
    database.session.commit()   # 👈 AQUI o ID É GERADO

    # AGORA SIM o ID EXISTE
    pedido_id = novo_pedido.id

    # --- GERA PDF ---
    pdf_output = BytesIO()
    doc = SimpleDocTemplate(pdf_output, pagesize=A4)
    elements = []

    style = getSampleStyleSheet()
    elements.append(Paragraph("Total do Pedido", style['Title']))

    table_data = [["Produto", "Quantidade", "Preço Unitário", "Subtotal"]]
    for item in itens_excel:
        table_data.append([
            item["Produto"],
            str(item["Quantidade"]),
            f'R$ {item["Preço Unitário"]:.2f}',
            f'R$ {item["Subtotal"]:.2f}'
        ])

    table_data.append(["TOTAL", "", "", f'R$ {total:.2f}'])
    t = Table(table_data)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.gray),
        ('TEXTCOLOR',(0,0),(-1,0),colors.whitesmoke),
        ('GRID', (0,0), (-1,-1), 1, colors.black),
        ('ALIGN',(1,1),(-1,-1),'CENTER')
    ]))

    elements.append(t)

    agora_brasilia = datetime.now() - timedelta(hours=3)
    elements.append(Paragraph(
        f"Pedido da EBD - {current_user.congregacao.upper()} - {agora_brasilia.strftime('%d/%m/%Y %H:%M:%S')}",
        style["Title"]
    ))

    doc.build(elements)
    pdf_output.seek(0)

    session["carrinho"] = {}

    return send_file(
        pdf_output,
        download_name=f"pedido_{pedido_id}.pdf",
        as_attachment=True,
        mimetype="application/pdf"
    )


    
@app.route("/cadastro", methods = ["GET", "POST"])
def cadastro ():
        formcriarconta = FormCriarConta()
        if formcriarconta.validate_on_submit():
                senha = bcrypt.generate_password_hash(formcriarconta.senha.data).decode('utf-8')
                usuario = Usuario(usarname=formcriarconta.username.data,
                                   senha=senha, 
                                   congregacao=formcriarconta.congregacao.data,
                                  email=formcriarconta.email.data
                                  )
                database.session.add(usuario)
                database.session.commit()
                login_user(usuario, remember=True)
                return redirect(url_for("perfil", id_usuario=current_user.id))
        return render_template("cadastro.html", form=formcriarconta)
@app.route("/login", methods=["GET", "POST"])
def login():
    form = FormLogin()
    if form.validate_on_submit():
        usuario = Usuario.query.filter_by(
            email=form.email.data,
            congregacao=form.congregacao.data
        ).first()

        if usuario and bcrypt.check_password_hash(usuario.senha, form.senha.data):
            login_user(usuario, remember=True)

            # Redirecionar de acordo com tipo de usuário
            if usuario.is_admin:
                return redirect(url_for("adm", id_usuario=usuario.id))        # Rota do painel admin
            else:
                return redirect(url_for("perfil", id_usuario=usuario.id))  # Rota normal

        else:
            flash("Email, congregação ou senha inválidos.", "danger")

    return render_template("login.html", form=form)

@app.route("/perfil/<id_usuario>", methods=["GET", "POST"])
@login_required
def perfil (id_usuario):
        if int(id_usuario) == int(current_user.id):
        
          return render_template("perfil.html", id_usuario=current_user.id, produtos=produtos, 
                                 congregacao=current_user.congregacao, usuario=current_user.usarname)
        
@app.route("/logout")
@login_required
def logout():
       logout_user()
       return redirect(url_for("home"))        
       

@app.route("/usuarios")
def listar_usuarios():
    if not current_user.is_admin:   # só admins podem acessar
        abort(403)  # acesso negado
    usuarios = Usuario.query.all()
    return render_template("usuarios.html", usuarios=usuarios)       



@app.route("/tornar_admin/<int:user_id>", methods=["POST"])
@login_required
def tornar_admin(user_id):
    usuario = Usuario.query.get_or_404(user_id)
    usuario.is_admin = True
    database.session.commit()  # Corrigido para db.session
    flash(f"{usuario.usarname} agora é administrador!", "success")
    return redirect(url_for("painel_banco"))


@app.route("/adm/<id_usuario>", methods=["GET", "POST"])
@login_required
def adm (id_usuario):
        if int(id_usuario) == int(current_user.id):
        
          return render_template("adm.html", id_usuario=current_user.id, produtos=produtos, 
                                 congregacao=current_user.congregacao, usuario=current_user.usarname)



@app.route("/todos_pedidos")
@login_required
def todos_pedidos():
    if not current_user.is_admin:
        return "Acesso negado", 403

    pedidos = Pedido.query.order_by(Pedido.data.desc()).all()

    # Ajusta para horário de Brasília
    for pedido in pedidos:
        pedido.data = pedido.data - timedelta(hours=3)

    return render_template("todos_pedidos.html", pedidos=pedidos)
@app.route("/gerenciar_pedidos")
@login_required
def gerenciar_pedidos():
    if not current_user.is_admin:   # só admins podem acessar
        abort(403)  # acesso negado
    pedidos_dir = os.path.join("ebd", "static", "pedidos")
    arquivos = []

    if os.path.exists(pedidos_dir):
        for nome in os.listdir(pedidos_dir):
            caminho = os.path.join(pedidos_dir, nome)
            if os.path.isfile(caminho):
                arquivos.append({
                    "nome": nome,
                    "tamanho": round(os.path.getsize(caminho) / 1024, 2),  # em KB
                    "data": os.path.getmtime(caminho)  # timestamp
                })

    # Ordenar por data mais recente
    arquivos.sort(key=lambda x: x["data"], reverse=True)

    return render_template("gerenciar_pedidos.html", arquivos=arquivos)

@app.route("/download_pedido/<path:filename>")
@login_required
def download_pedido(filename):
    # Caminho absoluto é mais seguro
    pedidos_dir = os.path.join(app.root_path, "static", "pedidos")
    # Verifica se o arquivo existe
    file_path = os.path.join(pedidos_dir, filename)
    if not os.path.isfile(file_path):
        return "Arquivo não encontrado", 404
    return send_from_directory(pedidos_dir, filename, as_attachment=True)

# Rota para deletar arquivo
@app.route("/delete_pedido/<path:filename>", methods=["POST"])
@login_required
def delete_pedido(filename):
    pedidos_dir = os.path.join("ebd", "static", "pedidos")
    caminho = os.path.join(pedidos_dir, filename)
    if os.path.exists(caminho):
        os.remove(caminho)
        flash(f"Arquivo {filename} removido com sucesso!", "success")
    else:
        flash(f"Arquivo {filename} não encontrado.", "danger")
    return redirect(url_for("gerenciar_pedidos"))



@app.route("/meuspedidos")
@login_required
def meuspedidos():
    pedidos_dir = os.path.join("ebd", "static", "pedidos")
    arquivos = []

    if os.path.exists(pedidos_dir):
        for nome in os.listdir(pedidos_dir):
            caminho = os.path.join(pedidos_dir, nome)
            if os.path.isfile(caminho):
                # Dividir o nome do arquivo
                partes = nome.split("_")
                if len(partes) >= 3:
                    nome_usuario_arquivo = partes[2]  # depois de congregacao
                    if nome_usuario_arquivo.lower() == current_user.usarname.lower():
                        arquivos.append({
                            "nome": nome,
                            "tamanho": round(os.path.getsize(caminho) / 1024, 2),  # KB
                            "data": datetime.fromtimestamp(os.path.getmtime(caminho))
                        })

    # Ordenar por data mais recente
    arquivos.sort(key=lambda x: x["data"], reverse=True)


    return render_template("meuspedidos.html", arquivos=arquivos)


    
@app.route('/gerenciar_pdfs')
@app.route('/gerenciar_pdfs/<path:subpasta>')
def gerenciar_pdfs(subpasta=None):
    pastas = []
    arquivos = []

    caminho_base = PDF_FOLDER
    caminho_atual = PDF_FOLDER

    if subpasta:
        caminho_atual = os.path.join(PDF_FOLDER, subpasta)

    for nome in os.listdir(caminho_atual):
        caminho = os.path.join(caminho_atual, nome)

        if os.path.isdir(caminho):
            pastas.append(nome)

        elif nome.lower().endswith('.pdf'):
            tamanho_kb = round(os.path.getsize(caminho) / 1024, 2)
            arquivos.append({
                'nome': nome,
                'tamanho': tamanho_kb
            })

    pastas.sort()
    arquivos.sort(key=lambda x: x["nome"])

    return render_template(
        'gerenciar_pdfs.html',
        pastas=pastas,
        arquivos=arquivos,
        subpasta=subpasta
    )

@app.route('/download_pdf/<path:subpasta>/<filename>')
def download_pdf(subpasta, filename):
    caminho = os.path.join(PDF_FOLDER, subpasta)
    return send_from_directory(caminho, filename, as_attachment=True)


@app.route("/meus_pedidos")
@login_required
def meus_pedidos():
    pedidos = Pedido.query.filter_by(id_usuario=current_user.id).order_by(Pedido.data.desc()).all()
    return render_template("meus_pedidos.html", pedidos=pedidos)


@app.route("/exportar_pedidos_excel")
@login_required
def exportar_pedidos_excel():
    pedidos = Pedido.query.order_by(Pedido.data.desc()).all()

    dados = []
    for pedido in pedidos:
        for item in pedido.itens:
            dados.append({
                "Código": item.codigo,
                "Produto": item.produto,
                "Quantidade": item.quantidade,
                "Preço Unitário": item.preco_unitario,
                "Subtotal": item.subtotal,
            })

    df = pd.DataFrame(dados)

    # Agrupar apenas pelo Código do produto
    df_agrupado = df.groupby(['Código', 'Produto'], as_index=False).agg({
        'Quantidade': 'sum',
        'Subtotal': 'sum',
        'Preço Unitário': 'first'
    })

    output = BytesIO()
    df_agrupado.to_excel(output, index=False)
    output.seek(0)

    return send_file(output, as_attachment=True, download_name="todos_pedidos.xlsx")




@app.route('/painel_banco')
@login_required
def painel_banco():
    # Apenas administradores podem acessar
    if not current_user.is_admin:
        return "Acesso negado", 403

    # Buscar dados
    usuarios = Usuario.query.order_by(Usuario.usarname).all()
    pedidos = Pedido.query.order_by(Pedido.data.desc()).all()
    itens = ItemPedido.query.all()  # para simplificar, traz todos os itens

    return render_template('painel_banco.html',
                           usuarios=usuarios,
                           pedidos=pedidos,
                           itens=itens)
from flask import redirect, url_for, flash

# Deletar usuário
@app.route('/deletar_usuario/<int:id_usuario>', methods=['POST'])
@login_required
def deletar_usuario(id_usuario):
    if not current_user.is_admin:
        return "Acesso negado", 403
    usuario = Usuario.query.get_or_404(id_usuario)
    database.session.delete(usuario)
    database.session.commit()
    flash(f'Usuário {usuario.usarname} deletado com sucesso!', 'success')
    return redirect(url_for('painel_banco'))

# Deletar pedido
@app.route('/deletar_pedido/<int:id_pedido>', methods=['POST'])
@login_required
def deletar_pedido(id_pedido):
    if not current_user.is_admin:
        return "Acesso negado", 403
    pedido = Pedido.query.get_or_404(id_pedido)
    database.session.delete(pedido)
    database.session.commit()
    flash(f'Pedido {pedido.id} deletado com sucesso!', 'success')
    return redirect(url_for('painel_banco'))

# Deletar item do pedido
@app.route('/deletar_item/<int:id_item>', methods=['POST'])
@login_required
def deletar_item(id_item):
    if not current_user.is_admin:
        return "Acesso negado", 403
    item = ItemPedido.query.get_or_404(id_item)
    database.session.delete(item)
    database.session.commit()
    flash(f'Item {item.produto} deletado com sucesso!', 'success')
    return redirect(url_for('painel_banco'))

@app.route("/imprimir_pedido/<int:id_pedido>")
@login_required
def imprimir_pedido(id_pedido):
    if not current_user.is_admin:
        return "Acesso negado", 403

    pedido = Pedido.query.get_or_404(id_pedido)
    itens_excel = []
    total = pedido.total

    for item in pedido.itens:
        itens_excel.append({
            "Produto": item.produto,
            "Quantidade": item.quantidade,
            "Preço Unitário": item.preco_unitario,
            "Subtotal": item.subtotal
        })

    # --- GERA PDF ---
    # Ajuste de horário para Brasília (-3h UTC)
    agora_brasilia = datetime.now() - timedelta(hours=3)
    pdf_output = BytesIO()
    doc = SimpleDocTemplate(pdf_output, pagesize=A4)
    elements = []
    style = getSampleStyleSheet()
    elements.append(Paragraph(f"Pedido ID: {pedido.id}", style['Title']))

    table_data = [["Produto", "Quantidade", "Preço Unitário", "Subtotal"]]
    for item in itens_excel:
        table_data.append([
            item["Produto"],
            str(item["Quantidade"]),
            f'R$ {item["Preço Unitário"]:.2f}',
            f'R$ {item["Subtotal"]:.2f}'
        ])
    table_data.append(["TOTAL", "", "", f'R$ {total:.2f}'])
    t = Table(table_data)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.gray),
        ('TEXTCOLOR',(0,0),(-1,0),colors.whitesmoke),
        ('GRID', (0,0), (-1,-1), 1, colors.black),
        ('ALIGN',(1,1),(-1,-1),'CENTER')
    ]))
    elements.append(t)
    elements.append(Spacer(1, 24))
    elements.append(Paragraph(f"Usuário: {pedido.usuario.usarname.upper()}", style["Title"]))
    elements.append(Paragraph(f"Congregação: {pedido.congregacao.upper()}", style["Title"]))
    elements.append(Paragraph(f"Data: {pedido.data.strftime('%d/%m/%Y %H:%M:%S')}", style["Title"]))

    doc.build(elements)
    pdf_output.seek(0)

    return send_file(
        pdf_output,
        download_name=f"pedido_{pedido.id}.pdf",
        as_attachment=True,
        mimetype="application/pdf"
    )

@app.route("/redefinir_senha/<int:id_usuario>", methods=["GET", "POST"])
def redefinir_senha(id_usuario):
    usuario = Usuario.query.get_or_404(id_usuario)
    form = FormRedefinirSenha()

    if form.validate_on_submit():
        nova_senha_hash = bcrypt.generate_password_hash(form.senha.data).decode("utf-8")
        usuario.senha = nova_senha_hash

        try:
            database.session.commit()
            flash(f"✅ Senha do usuário {usuario.usarname} redefinida com sucesso!", "success")
            return redirect(url_for("login"))
        except Exception as e:
            database.session.rollback()
            flash(f"❌ Erro ao salvar nova senha: {e}", "danger")

    return render_template("redefinir_senha.html", form=form, usuario=usuario)
@app.route("/recuperar_senha", methods=["GET", "POST"])
def recuperar_senha():
    form = FormRecuperarSenha()

    if form.validate_on_submit():
        email = form.email.data.strip()
        congregacao = form.congregacao.data.strip()

        usuario = Usuario.query.filter(
            func.lower(Usuario.email) == func.lower(email),
            func.lower(Usuario.congregacao) == func.lower(congregacao)
        ).first()

        if usuario:
            flash(f"✅ Usuário encontrado: {usuario.usarname}. Agora redefina sua senha.", "success")
            return redirect(url_for("redefinir_senha", id_usuario=usuario.id))
        else:
            flash("❌ Nenhum usuário encontrado com esse email e congregação.", "danger")

    return render_template("recuperar_senha.html", form=form)

@app.route("/caixa")
@login_required
def caixa():
    if not current_user.is_admin:
        return "Acesso negado", 403

    pedidos = Pedido.query.order_by(Pedido.data.desc()).all()
    caixa = Caixa.query.order_by(Caixa.data.desc()).all()

    # somatórios importantes
    saldo_caixa = sum(c.valor for c in caixa)
    total_receber = sum(p.saldo_restante for p in pedidos if p.saldo_restante > 0)

    return render_template(
        "caixa.html",
        pedidos=pedidos,
        caixa=caixa,
        saldo_caixa=saldo_caixa,
        total_receber=total_receber
    )

@app.route("/caixa/trimestre")
@login_required
def caixa_trimestre():
    if not current_user.is_admin:
        return "Acesso negado", 403

    # 🔹 Buscar trimestres existentes a partir dos pedidos
    resultados = database.session.query(
        func.extract('year', Pedido.data).label('ano'),
        func.ceil(func.extract('month', Pedido.data) / 3).label('trimestre')
    ).distinct().order_by(
        func.extract('year', Pedido.data).desc(),
        func.ceil(func.extract('month', Pedido.data) / 3).desc()
    ).all()

    trimestres_disponiveis = [
        f"{int(r.ano)}-{int(r.trimestre)}" for r in resultados
    ]

    tri_param = request.args.get("tri")

    if tri_param and tri_param in trimestres_disponiveis:
        ano, trimestre = map(int, tri_param.split("-"))
    else:
        ano, trimestre = map(int, trimestres_disponiveis[0].split("-"))

    # 🔹 Intervalo do trimestre
    inicio = date(ano, (trimestre - 1) * 3 + 1, 1)
    if trimestre == 4:
        fim = date(ano, 12, 31)
    else:
        fim = date(ano, trimestre * 3 + 1, 1) - timedelta(days=1)

    # 🔹 Pedidos (SEM ALTERAÇÃO)
    pedidos = Pedido.query.filter(
        Pedido.data.between(inicio, fim)
    ).order_by(Pedido.data.desc()).all()

    # 🔹 Caixa (AJUSTE AQUI)
    caixa = (
    database.session.query(Caixa)
    .outerjoin(Pedido, Caixa.id_pedido == Pedido.id)
    .filter(
        or_(
            and_(
                Caixa.pedido_id.isnot(None),
                Pedido.data.between(inicio, fim)
            ),
            and_(
                Caixa.pedido_id.is_(None),
                Caixa.data.between(inicio, fim)
            )
        )
    )
    .order_by(Caixa.data.desc())
    .all()
)


    # 🔹 Saldo do caixa do trimestre
    saldo_caixa = sum(c.valor for c in caixa)

    # 🔹 Total a receber (já correto)
    total_receber = sum(p.saldo_restante for p in pedidos if not p.quitado)

    return render_template(
        "caixa_trimestre.html",
        pedidos=pedidos,
        caixa=caixa,
        saldo_caixa=saldo_caixa,
        total_receber=total_receber,
        trimestres=trimestres_disponiveis,
        ano=ano,
        trimestre=trimestre
    )


    

    

@app.route("/adicionar_verba", methods=["POST"])
@login_required
def adicionar_verba():
    if not current_user.is_admin:
        return "Acesso negado", 403

    valor = float(request.form["valor"])
    descricao = request.form["descricao"]

    # 🔹 dados do trimestre vindo do form
    ano = int(request.form.get("ano"))
    trimestre = int(request.form.get("trimestre"))

    if trimestre == 1:
        data_caixa = date(ano, 1, 1)
    elif trimestre == 2:
        data_caixa = date(ano, 4, 1)
    elif trimestre == 3:
        data_caixa = date(ano, 7, 1)
    elif trimestre == 4:
        data_caixa = date(ano, 10, 1)
    else:
        return "Trimestre inválido", 400

    novo = Caixa(
        descricao=descricao,
        valor=valor,
        data=data_caixa
    )

    database.session.add(novo)
    database.session.commit()

    flash("Verba adicionada com sucesso!", "success")

    return redirect(request.referrer or url_for("caixa"))

@app.route("/excluir_verba/<int:id_verba>", methods=["POST"])
@login_required
def excluir_verba(id_verba):
    if not current_user.is_admin:
        return "Acesso negado", 403

    verba = Caixa.query.get_or_404(id_verba)
    database.session.delete(verba)
    database.session.commit()

    flash("Verba removida!", "success")
    return redirect(url_for("caixa"))

@app.route("/registrar_pagamento/<int:id_pedido>", methods=["POST"])
@login_required
def registrar_pagamento(id_pedido):
    if not current_user.is_admin:
        return "Acesso negado", 403

    pedido = Pedido.query.get_or_404(id_pedido)
    valor = float(request.form["valor_pago"])

    if valor <= 0:
        flash("Valor inválido!", "danger")
        return redirect(url_for("caixa"))

    if valor > pedido.saldo_restante:
        flash("Valor maior que o saldo restante!", "danger")
        return redirect(url_for("caixa"))

    # 1️⃣ pagamento
    pagamento = Pagamento(
        id_pedido=pedido.id,
        valor_pago=valor
    )
    database.session.add(pagamento)

    # 2️⃣ caixa (🔥 VINCULADO AO PEDIDO 🔥)
    caixa = Caixa(
        descricao=f"Pagamento pedido #{pedido.id}",
        valor=valor,
        id_pedido=pedido.id   # ✅ LINHA QUE FALTAVA
    )
    database.session.add(caixa)

    database.session.commit()

    flash("Pagamento registrado com sucesso!", "success")
    return redirect(url_for("caixa"))






@app.route("/adicionar_despesa", methods=["POST"])
@login_required
def adicionar_despesa():
    if not current_user.is_admin:
        return "Acesso negado", 403

    try:
        valor = float(request.form["valor"])
        descricao = request.form["descricao"].strip()

        # 🔴 despesa sempre negativa
        valor = -abs(valor)

        # 🔹 dados do trimestre (se existirem)
        ano = request.form.get("ano")
        trimestre = request.form.get("trimestre")

        if ano and trimestre:
            ano = int(ano)
            trimestre = int(trimestre)

            if trimestre == 1:
                data_caixa = date(ano, 1, 1)
            elif trimestre == 2:
                data_caixa = date(ano, 4, 1)
            elif trimestre == 3:
                data_caixa = date(ano, 7, 1)
            elif trimestre == 4:
                data_caixa = date(ano, 10, 1)
            else:
                return "Trimestre inválido", 400
        else:
            # fallback: data atual
            data_caixa = date.today()

        nova_despesa = Caixa(
            descricao=descricao,
            valor=valor,
            data=data_caixa
        )

        database.session.add(nova_despesa)
        database.session.commit()

        flash("Despesa adicionada com sucesso!", "danger")

    except Exception as e:
        database.session.rollback()
        flash(f"Erro ao adicionar despesa: {e}", "danger")

    # 🔁 volta para caixa OU caixa_trimestre
    return redirect(request.referrer or url_for("caixa"))


TOTAL_VISITAS = 0
usuarios_online = {}
@app.before_request
def contar_visitas_e_online():
    global TOTAL_VISITAS

    TOTAL_VISITAS += 1

    ip = request.remote_addr
    agora = datetime.now()

    usuarios_online[ip] = agora

    limite = agora - timedelta(minutes=2)
    ativos = {ip: t for ip, t in usuarios_online.items() if t >= limite}

    usuarios_online.clear()
    usuarios_online.update(ativos)

@app.context_processor
def injetar_stats():
    return dict(
        total_visitas=TOTAL_VISITAS,
        online=len(usuarios_online)
    )


from datetime import date

























