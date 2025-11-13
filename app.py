# -*- coding: utf-8 -*-
"""
📚 SISTEMA DE REGISTRO DE LIVROS - SIMPLIFICADO
"""

import os
from flask import Flask, render_template_string, request, redirect, url_for, flash, session, jsonify, get_flashed_messages
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import secrets

# =============================================
# CONFIGURAÇÃO
# =============================================

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'minha-chave-secreta-padrao')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///livros.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# =============================================
# MODELOS
# =============================================

class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    senha = db.Column(db.String(200), nullable=False)
    nome = db.Column(db.String(100), nullable=False)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)

class Livro(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(200), nullable=False)
    autor = db.Column(db.String(100), nullable=False)
    genero = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), nullable=False)
    paginas = db.Column(db.Integer, default=0)
    paginas_lidas = db.Column(db.Integer, default=0)
    nota = db.Column(db.Integer)
    tags = db.Column(db.String(300))
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)

# =============================================
# FUNÇÕES AUXILIARES
# =============================================

def get_flashed_messages_html():
    messages_html = []
    for category, message in get_flashed_messages(with_categories=True):
        alert_class = 'alert-success' if category == 'success' else 'alert-danger'
        messages_html.append(f'<div class="alert {alert_class}">{message}</div>')
    return ''.join(messages_html)

# =============================================
# TEMPLATES SIMPLIFICADOS
# =============================================

BASE_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Sistema de Livros</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { font-family: Arial, sans-serif; background: #f8f9fa; }
        .sidebar { background: #2c3e50; min-height: 100vh; color: white; }
        .sidebar .nav-link { color: white; }
        .sidebar .nav-link:hover { background: #34495e; }
    </style>
</head>
<body>
    {{ content|safe }}
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
'''

LOGIN_TEMPLATE = '''
<div class="container mt-5">
    <div class="row justify-content-center">
        <div class="col-md-4">
            <div class="card">
                <div class="card-body">
                    <h3 class="text-center">📚 Login</h3>
                    {{ messages|safe }}
                    <form method="POST">
                        <div class="mb-3">
                            <label>Email</label>
                            <input type="email" class="form-control" name="email" required>
                        </div>
                        <div class="mb-3">
                            <label>Senha</label>
                            <input type="password" class="form-control" name="senha" required>
                        </div>
                        <button type="submit" class="btn btn-primary w-100">Entrar</button>
                    </form>
                    <p class="text-center mt-3">
                        <a href="/cadastro">Criar conta</a>
                    </p>
                </div>
            </div>
        </div>
    </div>
</div>
'''

# =============================================
# ROTAS PRINCIPAIS
# =============================================

@app.route('/')
def index():
    if 'usuario_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']
        
        usuario = Usuario.query.filter_by(email=email).first()
        
        if usuario and check_password_hash(usuario.senha, senha):
            session['usuario_id'] = usuario.id
            session['usuario_nome'] = usuario.nome
            flash('Login realizado com sucesso!')
            return redirect(url_for('dashboard'))
        else:
            flash('Email ou senha incorretos!')
    
    return render_template_string(BASE_TEMPLATE.replace('{{ content|safe }}', LOGIN_TEMPLATE), messages=get_flashed_messages_html())

@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        senha = request.form['senha']
        confirmar_senha = request.form['confirmar_senha']
        
        if senha != confirmar_senha:
            flash('Senhas não coincidem!')
            return redirect(url_for('cadastro'))
        
        if Usuario.query.filter_by(email=email).first():
            flash('Email já cadastrado!')
            return redirect(url_for('cadastro'))
        
        usuario = Usuario(
            nome=nome,
            email=email,
            senha=generate_password_hash(senha)
        )
        
        db.session.add(usuario)
        db.session.commit()
        
        flash('Conta criada com sucesso! Faça login.')
        return redirect(url_for('login'))
    
    cadastro_html = '''
    <div class="container mt-5">
        <div class="row justify-content-center">
            <div class="col-md-4">
                <div class="card">
                    <div class="card-body">
                        <h3 class="text-center">📝 Cadastro</h3>
                        {{ messages|safe }}
                        <form method="POST">
                            <div class="mb-3">
                                <label>Nome</label>
                                <input type="text" class="form-control" name="nome" required>
                            </div>
                            <div class="mb-3">
                                <label>Email</label>
                                <input type="email" class="form-control" name="email" required>
                            </div>
                            <div class="mb-3">
                                <label>Senha</label>
                                <input type="password" class="form-control" name="senha" required>
                            </div>
                            <div class="mb-3">
                                <label>Confirmar Senha</label>
                                <input type="password" class="form-control" name="confirmar_senha" required>
                            </div>
                            <button type="submit" class="btn btn-primary w-100">Criar Conta</button>
                        </form>
                        <p class="text-center mt-3">
                            <a href="/login">Já tem conta? Faça login</a>
                        </p>
                    </div>
                </div>
            </div>
        </div>
    </div>
    '''
    
    return render_template_string(BASE_TEMPLATE.replace('{{ content|safe }}', cadastro_html), messages=get_flashed_messages_html())

@app.route('/dashboard')
def dashboard():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
    
    usuario = Usuario.query.get(session['usuario_id'])
    
    # Cálculos simples
    total_livros = Livro.query.filter_by(usuario_id=usuario.id).count()
    livros_lidos = Livro.query.filter_by(usuario_id=usuario.id, status='lido').count()
    livros_lendo = Livro.query.filter_by(usuario_id=usuario.id, status='lendo').count()
    
    dashboard_html = f'''
    <div class="container-fluid">
        <div class="row">
            <nav class="col-md-3 col-lg-2 sidebar p-3">
                <h5>👤 {session["usuario_nome"]}</h5>
                <ul class="nav flex-column">
                    <li class="nav-item"><a class="nav-link active" href="/dashboard">Dashboard</a></li>
                    <li class="nav-item"><a class="nav-link" href="/livros">Meus Livros</a></li>
                    <li class="nav-item"><a class="nav-link" href="/novo_livro">Adicionar Livro</a></li>
                    <li class="nav-item"><a class="nav-link" href="/logout">Sair</a></li>
                </ul>
            </nav>

            <main class="col-md-9 ms-sm-auto col-lg-10 p-4">
                <h2>Dashboard</h2>
                {get_flashed_messages_html()}
                
                <div class="row mt-4">
                    <div class="col-md-4">
                        <div class="card text-white bg-primary">
                            <div class="card-body">
                                <h2>{total_livros}</h2>
                                <p>Total de Livros</p>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="card text-white bg-success">
                            <div class="card-body">
                                <h2>{livros_lidos}</h2>
                                <p>Livros Lidos</p>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="card text-white bg-warning">
                            <div class="card-body">
                                <h2>{livros_lendo}</h2>
                                <p>Lendo Agora</p>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="card mt-4">
                    <div class="card-body">
                        <h5>Bem-vindo ao seu sistema de livros!</h5>
                        <p>Comece adicionando seus livros.</p>
                        <a href="/novo_livro" class="btn btn-primary">Adicionar Primeiro Livro</a>
                    </div>
                </div>
            </main>
        </div>
    </div>
    '''
    
    return render_template_string(BASE_TEMPLATE.replace('{{ content|safe }}', dashboard_html))

@app.route('/livros')
def livros():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
    
    usuario = Usuario.query.get(session['usuario_id'])
    livros = Livro.query.filter_by(usuario_id=usuario.id).all()
    
    livros_html = ''
    for livro in livros:
        livros_html += f'''
        <div class='col-md-4 mb-3'>
            <div class='card'>
                <div class='card-body'>
                    <h5>{livro.titulo}</h5>
                    <p><strong>Autor:</strong> {livro.autor}</p>
                    <p><strong>Status:</strong> {livro.status}</p>
                    <a href='/editar_livro/{livro.id}' class='btn btn-warning btn-sm'>Editar</a>
                </div>
            </div>
        </div>'''
    
    livros_content = f'''
    <div class="container-fluid">
        <div class="row">
            <nav class="col-md-3 col-lg-2 sidebar p-3">
                <h5>👤 {session["usuario_nome"]}</h5>
                <ul class="nav flex-column">
                    <li class="nav-item"><a class="nav-link" href="/dashboard">Dashboard</a></li>
                    <li class="nav-item"><a class="nav-link active" href="/livros">Meus Livros</a></li>
                    <li class="nav-item"><a class="nav-link" href="/novo_livro">Adicionar Livro</a></li>
                    <li class="nav-item"><a class="nav-link" href="/logout">Sair</a></li>
                </ul>
            </nav>

            <main class="col-md-9 ms-sm-auto col-lg-10 p-4">
                <div class="d-flex justify-content-between align-items-center mb-4">
                    <h2>Meus Livros</h2>
                    <a href="/novo_livro" class="btn btn-primary">Adicionar Livro</a>
                </div>
                
                {get_flashed_messages_html()}
                
                <div class="row">
                    {livros_html if livros else '<div class="col-12"><div class="alert alert-info">Nenhum livro cadastrado.</div></div>'}
                </div>
            </main>
        </div>
    </div>
    '''
    
    return render_template_string(BASE_TEMPLATE.replace('{{ content|safe }}', livros_content))

@app.route('/novo_livro', methods=['GET', 'POST'])
def novo_livro():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        livro = Livro(
            titulo=request.form['titulo'],
            autor=request.form['autor'],
            genero=request.form['genero'],
            status=request.form['status'],
            usuario_id=session['usuario_id']
        )
        
        db.session.add(livro)
        db.session.commit()
        
        flash('Livro adicionado com sucesso!')
        return redirect(url_for('livros'))
    
    form_html = '''
    <div class="container-fluid">
        <div class="row">
            <nav class="col-md-3 col-lg-2 sidebar p-3">
                <h5>👤 ''' + session["usuario_nome"] + '''</h5>
                <ul class="nav flex-column">
                    <li class="nav-item"><a class="nav-link" href="/dashboard">Dashboard</a></li>
                    <li class="nav-item"><a class="nav-link" href="/livros">Meus Livros</a></li>
                    <li class="nav-item"><a class="nav-link active" href="/novo_livro">Adicionar Livro</a></li>
                    <li class="nav-item"><a class="nav-link" href="/logout">Sair</a></li>
                </ul>
            </nav>

            <main class="col-md-9 ms-sm-auto col-lg-10 p-4">
                <h2>Adicionar Livro</h2>
                ''' + get_flashed_messages_html() + '''
                
                <div class="card">
                    <div class="card-body">
                        <form method="POST">
                            <div class="mb-3">
                                <label>Título *</label>
                                <input type="text" class="form-control" name="titulo" required>
                            </div>
                            <div class="mb-3">
                                <label>Autor *</label>
                                <input type="text" class="form-control" name="autor" required>
                            </div>
                            <div class="mb-3">
                                <label>Gênero *</label>
                                <input type="text" class="form-control" name="genero" required>
                            </div>
                            <div class="mb-3">
                                <label>Status *</label>
                                <select class="form-control" name="status" required>
                                    <option value="quero_ler">Quero Ler</option>
                                    <option value="lendo">Lendo</option>
                                    <option value="lido">Lido</option>
                                </select>
                            </div>
                            <button type="submit" class="btn btn-primary">Adicionar Livro</button>
                            <a href="/livros" class="btn btn-secondary">Cancelar</a>
                        </form>
                    </div>
                </div>
            </main>
        </div>
    </div>
    '''
    
    return render_template_string(BASE_TEMPLATE.replace('{{ content|safe }}', form_html))

@app.route('/logout')
def logout():
    session.clear()
    flash('Logout realizado com sucesso!')
    return redirect(url_for('login'))

# =============================================
# INICIALIZAÇÃO
# =============================================

def init_db():
    with app.app_context():
        db.create_all()
        print("✅ Banco de dados pronto!")

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
