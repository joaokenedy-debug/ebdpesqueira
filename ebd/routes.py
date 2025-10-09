from flask import render_template, url_for, redirect, session, request,  send_file, flash,send_from_directory
from ebd import app, database, bcrypt
from ebd.models import Usuario, Pedido, ItemPedido
from flask_login import login_required,login_user, logout_user, current_user
from ebd.forms import FormLogin, FormCriarConta
import os
from datetime import datetime
from werkzeug.utils import secure_filename
import pandas as pd
from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import Spacer
from reportlab.lib.styles import getSampleStyleSheet



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

    # --- SALVAR NO BANCO ---
    novo_pedido = Pedido(
        id_usuario=current_user.id,
        congregacao=current_user.congregacao,
        total=total
    )
    database.session.add(novo_pedido)
    database.session.flush()  # garante o id_pedido disponível

    for item in itens_excel:
        item_db = ItemPedido(
            id_pedido=novo_pedido.id,
            produto=item["Produto"],
            codigo=item["ID"],
            quantidade=item["Quantidade"],
            preco_unitario=item["Preço Unitário"],
            subtotal=item["Subtotal"]
        )
        database.session.add(item_db)

    database.session.commit()

    # --- GERA PDF (mantém igual) ---
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
    elements.append(Spacer(1, 24))
    elements.append(Paragraph(
        f"Pedido da EBD - {current_user.congregacao.upper()} - {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}",
        style["Title"]
    ))
    elements.append(Spacer(1, 12))
    elements.append(Paragraph(f"Usuário: {current_user.usarname.upper()}", style["Title"]))

    doc.build(elements)
    pdf_output.seek(0)

    # Limpa carrinho
    session["carrinho"] = {}

    # Envia PDF para download
    return send_file(
        pdf_output,
        download_name=f"pedido_{novo_pedido.id}.pdf",
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
    return redirect(url_for("listar_usuarios"))


@app.route("/adm/<id_usuario>", methods=["GET", "POST"])
@login_required
def adm (id_usuario):
        if int(id_usuario) == int(current_user.id):
        
          return render_template("adm.html", id_usuario=current_user.id, produtos=produtos, 
                                 congregacao=current_user.congregacao, usuario=current_user.usarname)




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

@app.route("/deletar_usuario/<int:user_id>", methods=["POST"])
@login_required
def deletar_usuario(user_id):
    

    usuario = Usuario.query.get(user_id)
    if usuario:
        # Evita excluir a si mesmo
        if usuario.id == current_user.id:
            flash("Você não pode excluir a si mesmo.", "warning")
            return redirect(url_for("lista_usuarios"))
        database.session.delete(usuario)
        database.session.commit()
        flash("Usuário excluído com sucesso!", "success")
    else:
        flash("Usuário não encontrado.", "danger")
    
    return redirect(url_for("lista_usuarios"))
    
@app.route('/gerenciar_pdfs')
def gerenciar_pdfs():
    arquivos = []
    for nome_arquivo in os.listdir(PDF_FOLDER):
        if nome_arquivo.lower().endswith('.pdf'):
            caminho = os.path.join(PDF_FOLDER, nome_arquivo)
            tamanho_kb = round(os.path.getsize(caminho) / 1024, 2)
            arquivos.append({'nome': nome_arquivo, 'tamanho': tamanho_kb})
    return render_template('gerenciar_pdfs.html', arquivos=arquivos)

@app.route('/download_pdf/<path:filename>')
def download_pdf(filename):
    return send_from_directory(PDF_FOLDER, filename, as_attachment=True)


@app.route("/meus_pedidos")
@login_required
def meus_pedidos():
    pedidos = Pedido.query.filter_by(id_usuario=current_user.id).order_by(Pedido.data.desc()).all()
    return render_template("meus_pedidos.html", pedidos=pedidos)


@app.route("/exportar_pedidos_excel")
@login_required
def exportar_pedidos_excel():
    pedidos = Pedido.query.filter_by(id_usuario=current_user.id).all()

    dados = []
    for pedido in pedidos:
        for item in pedido.itens:
            dados.append({
                "ID Pedido": pedido.id,
                "Data": pedido.data.strftime("%d/%m/%Y %H:%M"),
                "Produto": item.produto,
                "Código": item.codigo,
                "Quantidade": item.quantidade,
                "Preço Unitário": item.preco_unitario,
                "Subtotal": item.subtotal,
                "Total Pedido": pedido.total,
            })

    df = pd.DataFrame(dados)
    output = BytesIO()
    df.to_excel(output, index=False)
    output.seek(0)
    return send_file(output, as_attachment=True, download_name="meus_pedidos.xlsx")





