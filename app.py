# -*- coding: utf-8 -*-
"""
📚 SISTEMA DE REGISTRO DE LIVROS - BIBLIOTECA PESSOAL ACADÊMICA
Versão Completa e Corrigida
"""

import os
import json
import csv
from io import StringIO
from flask import Flask, render_template_string, request, redirect, url_for, flash, session, jsonify, get_flashed_messages, Response
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import secrets

# =============================================
# CONFIGURAÇÃO DA APLICAÇÃO
# =============================================

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', secrets.token_hex(16))
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///livros.db').replace('postgres://', 'postgresql://')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# =============================================
# MODELOS DO BANCO DE DADOS
# =============================================

class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    senha = db.Column(db.String(200), nullable=False)
    nome = db.Column(db.String(100), nullable=False)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    livros = db.relationship('Livro', backref='usuario', lazy=True)

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
    imagem_url = db.Column(db.String(500))
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)

# =============================================
# FUNÇÕES AUXILIARES
# =============================================

def get_flashed_messages_html():
    messages_html = []
    for category, message in get_flashed_messages(with_categories=True):
        alert_class = {
            'success': 'alert-success',
            'error': 'alert-danger', 
            'warning': 'alert-warning',
            'info': 'alert-info'
        }.get(category, 'alert-info')
        
        messages_html.append(f'''
            <div class="alert {alert_class} alert-dismissible fade show" role="alert">
                <i class="fas fa-{"check-circle" if category == "success" else "exclamation-triangle" if category == "warning" else "info-circle"} me-2"></i>
                {message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        ''')
    return ''.join(messages_html)

def calcular_estatisticas(usuario_id):
    """Calcula estatísticas completas do usuário"""
    livros = Livro.query.filter_by(usuario_id=usuario_id).all()
    total_livros = len(livros)
    livros_lidos = len([l for l in livros if l.status == 'lido'])
    livros_lendo = len([l for l in livros if l.status == 'lendo'])
    livros_quero_ler = len([l for l in livros if l.status == 'quero_ler'])
    
    total_paginas = sum(l.paginas for l in livros)
    paginas_lidas = sum(l.paginas_lidas for l in livros)
    progresso_leitura = (paginas_lidas / total_paginas * 100) if total_paginas > 0 else 0
    
    generos = {}
    for livro in livros:
        if livro.status == 'lido':
            generos[livro.genero] = generos.get(livro.genero, 0) + 1
    
    genero_mais_lido = max(generos, key=generos.get) if generos else "Nenhum"
    
    return {
        'total_livros': total_livros,
        'livros_lidos': livros_lidos,
        'livros_lendo': livros_lendo,
        'livros_quero_ler': livros_quero_ler,
        'total_paginas': total_paginas,
        'paginas_lidas': paginas_lidas,
        'progresso_leitura': round(progresso_leitura, 1),
        'genero_mais_lido': genero_mais_lido
    }

# =============================================
# TEMPLATES HTML
# =============================================

BASE_TEMPLATE = '''
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>📚 Sistema de Livros</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f8f9fa; }
        .sidebar { 
            background: linear-gradient(135deg, #2c3e50 0%, #3498db 100%);
            min-height: 100vh;
            color: white;
        }
        .sidebar .nav-link { 
            color: #ecf0f1; 
            border-radius: 5px;
            margin: 2px 0;
        }
        .sidebar .nav-link:hover { background: rgba(255,255,255,0.1); }
        .sidebar .nav-link.active { background: rgba(255,255,255,0.2); }
        .stat-card, .book-card { 
            border-radius: 15px; 
            transition: transform 0.3s, box-shadow 0.3s;
            border: none;
        }
        .stat-card:hover, .book-card:hover { 
            transform: translateY(-5px); 
            box-shadow: 0 10px 25px rgba(0,0,0,0.2);
        }
        .book-cover {
            height: 200px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 3rem;
        }
        .book-cover-large {
            height: 300px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 4rem;
        }
        .login-bg {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
            height: 100vh;
        }
        .login-card {
            border: none; 
            border-radius: 15px; 
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            background: rgba(255,255,255,0.95);
        }
    </style>
</head>
<body>
    {{ content|safe }}
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
'''

LOGIN_TEMPLATE = '''
<div class="login-bg">
    <div class="container">
        <div class="login-container mx-auto" style="max-width: 400px; margin-top: 100px;">
            <div class="login-card">
                <div class="card-body p-5">
                    <div class="text-center mb-4">
                        <i class="fas fa-book fa-3x text-primary mb-3"></i>
                        <h3>📚 Meu LivroTracker</h3>
                        <p class="text-muted">Faça login para continuar</p>
                    </div>
                    
                    {{ messages|safe }}
                    
                    <form method="POST">
                        <div class="mb-3">
                            <label class="form-label"><i class="fas fa-envelope"></i> Email</label>
                            <input type="email" class="form-control" name="email" required placeholder="seu@email.com">
                        </div>
                        <div class="mb-3">
                            <label class="form-label"><i class="fas fa-lock"></i> Senha</label>
                            <input type="password" class="form-control" name="senha" required placeholder="Sua senha">
                        </div>
                        <button type="submit" class="btn btn-primary w-100 py-2">
                            <i class="fas fa-sign-in-alt"></i> Entrar
                        </button>
                    </form>
                    <hr>
                    <p class="text-center mb-0">
                        Não tem uma conta? <a href="/cadastro" class="text-decoration-none">Cadastre-se</a>
                    </p>
                </div>
            </div>
        </div>
    </div>
</div>
'''

CADASTRO_TEMPLATE = '''
<div class="login-bg">
    <div class="container">
        <div class="login-container mx-auto" style="max-width: 450px; margin-top: 50px;">
            <div class="login-card">
                <div class="card-body p-5">
                    <div class="text-center mb-4">
                        <i class="fas fa-user-plus fa-3x text-primary mb-3"></i>
                        <h3>📝 Criar Conta</h3>
                        <p class="text-muted">Preencha os dados para se cadastrar</p>
                    </div>
                    
                    {{ messages|safe }}
                    
                    <form method="POST">
                        <div class="mb-3">
                            <label class="form-label"><i class="fas fa-user"></i> Nome Completo</label>
                            <input type="text" class="form-control" name="nome" required placeholder="Seu nome completo">
                        </div>
                        <div class="mb-3">
                            <label class="form-label"><i class="fas fa-envelope"></i> Email</label>
                            <input type="email" class="form-control" name="email" required placeholder="seu@email.com">
                        </div>
                        <div class="mb-3">
                            <label class="form-label"><i class="fas fa-lock"></i> Senha</label>
                            <input type="password" class="form-control" name="senha" required placeholder="Crie uma senha">
                        </div>
                        <div class="mb-3">
                            <label class="form-label"><i class="fas fa-lock"></i> Confirmar Senha</label>
                            <input type="password" class="form-control" name="confirmar_senha" required placeholder="Repita a senha">
                        </div>
                        <button type="submit" class="btn btn-primary w-100 py-2">
                            <i class="fas fa-user-plus"></i> Criar Conta
                        </button>
                    </form>
                    <hr>
                    <p class="text-center mb-0">
                        Já tem uma conta? <a href="/login" class="text-decoration-none">Faça login</a>
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
            flash('Login realizado com sucesso!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Email ou senha incorretos!', 'error')
    
    return render_template_string(BASE_TEMPLATE.replace('{{ content|safe }}', LOGIN_TEMPLATE), messages=get_flashed_messages_html())

@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        senha = request.form['senha']
        confirmar_senha = request.form['confirmar_senha']
        
        if senha != confirmar_senha:
            flash('Senhas não coincidem!', 'error')
            return redirect(url_for('cadastro'))
        
        if Usuario.query.filter_by(email=email).first():
            flash('Email já cadastrado!', 'error')
            return redirect(url_for('cadastro'))
        
        usuario = Usuario(
            nome=nome,
            email=email,
            senha=generate_password_hash(senha)
        )
        
        db.session.add(usuario)
        db.session.commit()
        
        flash('Conta criada com sucesso! Faça login.', 'success')
        return redirect(url_for('login'))
    
    return render_template_string(BASE_TEMPLATE.replace('{{ content|safe }}', CADASTRO_TEMPLATE), messages=get_flashed_messages_html())

@app.route('/dashboard')
def dashboard():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
    
    usuario = Usuario.query.get(session['usuario_id'])
    
    livros_lendo = Livro.query.filter_by(usuario_id=usuario.id, status='lendo').count()
    livros_lidos = Livro.query.filter_by(usuario_id=usuario.id, status='lido').count()
    livros_quero_ler = Livro.query.filter_by(usuario_id=usuario.id, status='quero_ler').count()
    total_livros = livros_lendo + livros_lidos + livros_quero_ler
    
    livros_recentes = Livro.query.filter_by(usuario_id=usuario.id).order_by(Livro.data_criacao.desc()).limit(5).all()
    
    livros_html = ''
    if not livros_recentes:
        livros_html = '<div class="alert alert-info text-center"><i class="fas fa-info-circle"></i> Nenhum livro cadastrado ainda. <a href="/novo_livro" class="alert-link">Adicione seu primeiro livro!</a></div>'
    else:
        livros_html = '<div class="row">'
        for livro in livros_recentes:
            capa_html = f'<img src="{livro.imagem_url}" class="img-fluid h-100 w-100" style="object-fit: cover;">' if livro.imagem_url else '<i class="fas fa-book"></i>'
            tags_html = f'<div class="mt-2">{"".join([f"<span class=\"badge bg-secondary me-1\">{tag.strip()}</span>" for tag in livro.tags.split(",") if livro.tags and tag.strip()])}</div>' if livro.tags else ''
            
            livros_html += f'''
            <div class='col-md-4 mb-3'>
                <div class='card book-card h-100'>
                    <div class='book-cover'>
                        {capa_html}
                    </div>
                    <div class='card-body'>
                        <h6 class='card-title'>{livro.titulo}</h6>
                        <p class='card-text mb-1'><small class='text-muted'>{livro.autor}</small></p>
                        <span class='badge bg-{"warning" if livro.status == "lendo" else "success" if livro.status == "lido" else "info"}'>
                            {livro.status.replace("_", " ").title()}
                        </span>
                        {tags_html}
                    </div>
                    <div class='card-footer bg-transparent'>
                        <a href='/detalhes_livro/{livro.id}' class='btn btn-primary btn-sm'><i class="fas fa-eye"></i> Ver</a>
                    </div>
                </div>
            </div>'''
        livros_html += '</div>'
    
    dashboard_content = f'''
    <div class="container-fluid">
        <div class="row">
            <nav class="col-md-3 col-lg-2 d-md-block sidebar">
                <div class="position-sticky pt-3">
                    <div class="text-center mb-4">
                        <i class="fas fa-user-circle fa-3x mb-3"></i>
                        <h5>👤 {session["usuario_nome"]}</h5>
                        <small class="text-light">Leitor</small>
                    </div>
                    <ul class="nav flex-column">
                        <li class="nav-item"><a class="nav-link active" href="/dashboard"><i class="fas fa-tachometer-alt"></i> Dashboard</a></li>
                        <li class="nav-item"><a class="nav-link" href="/livros"><i class="fas fa-book"></i> Meus Livros</a></li>
                        <li class="nav-item"><a class="nav-link" href="/novo_livro"><i class="fas fa-plus-circle"></i> Adicionar Livro</a></li>
                        <li class="nav-item"><a class="nav-link" href="/exportar"><i class="fas fa-download"></i> Exportar</a></li>
                        <li class="nav-item"><a class="nav-link" href="/logout"><i class="fas fa-sign-out-alt"></i> Sair</a></li>
                    </ul>
                </div>
            </nav>

            <main class="col-md-9 ms-sm-auto col-lg-10 px-md-4 py-4">
                <div class="d-flex justify-content-between align-items-center mb-4">
                    <h2><i class="fas fa-tachometer-alt"></i> Dashboard</h2>
                    <span class="text-muted">Bem-vindo, {session["usuario_nome"]}!</span>
                </div>
                
                {get_flashed_messages_html()}
                
                <div class="row mt-4">
                    <div class="col-md-3 mb-4">
                        <div class="card stat-card text-white bg-primary">
                            <div class="card-body">
                                <div class="d-flex justify-content-between">
                                    <div><h2>{total_livros}</h2><p>Total de Livros</p></div>
                                    <div class="align-self-center"><i class="fas fa-book fa-2x opacity-50"></i></div>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-3 mb-4">
                        <div class="card stat-card text-white bg-success">
                            <div class="card-body">
                                <div class="d-flex justify-content-between">
                                    <div><h2>{livros_lidos}</h2><p>Livros Lidos</p></div>
                                    <div class="align-self-center"><i class="fas fa-check-circle fa-2x opacity-50"></i></div>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-3 mb-4">
                        <div class="card stat-card text-white bg-warning">
                            <div class="card-body">
                                <div class="d-flex justify-content-between">
                                    <div><h2>{livros_lendo}</h2><p>Lendo Agora</p></div>
                                    <div class="align-self-center"><i class="fas fa-book-reader fa-2x opacity-50"></i></div>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-3 mb-4">
                        <div class="card stat-card text-white bg-info">
                            <div class="card-body">
                                <div class="d-flex justify-content-between">
                                    <div><h2>{livros_quero_ler}</h2><p>Quero Ler</p></div>
                                    <div class="align-self-center"><i class="fas fa-bookmark fa-2x opacity-50"></i></div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="row mt-4">
                    <div class="col-12">
                        <div class="card">
                            <div class="card-header d-flex justify-content-between align-items-center">
                                <h5><i class="fas fa-clock"></i> Livros Recentes</h5>
                                <a href="/livros" class="btn btn-primary btn-sm">Ver Todos</a>
                            </div>
                            <div class="card-body">
                                {livros_html}
                            </div>
                        </div>
                    </div>
                </div>
            </main>
        </div>
    </div>
    '''
    
    return render_template_string(BASE_TEMPLATE.replace('{{ content|safe }}', dashboard_content))

@app.route('/novo_livro', methods=['GET', 'POST'])
def novo_livro():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        titulo = request.form['titulo']
        autor = request.form['autor']
        genero = request.form['genero']
        status = request.form['status']
        paginas = request.form.get('paginas', 0) or 0
        paginas_lidas = request.form.get('paginas_lidas', 0) or 0
        nota = request.form.get('nota') or None
        tags = request.form.get('tags', '')
        imagem_url = request.form.get('imagem_url', '')
        
        livro = Livro(
            titulo=titulo,
            autor=autor,
            genero=genero,
            status=status,
            paginas=int(paginas),
            paginas_lidas=int(paginas_lidas),
            nota=int(nota) if nota else None,
            tags=tags,
            imagem_url=imagem_url,
            usuario_id=session['usuario_id']
        )
        
        db.session.add(livro)
        db.session.commit()
        
        flash('Livro adicionado com sucesso!', 'success')
        return redirect(url_for('listar_livros'))
    
    form_template = f'''
    <div class="container-fluid">
        <div class="row">
            <nav class="col-md-3 col-lg-2 d-md-block sidebar">
                <div class="position-sticky pt-3">
                    <div class="text-center mb-4">
                        <i class="fas fa-user-circle fa-3x mb-3"></i>
                        <h5>👤 {session["usuario_nome"]}</h5>
                        <small class="text-light">Leitor</small>
                    </div>
                    <ul class="nav flex-column">
                        <li class="nav-item"><a class="nav-link" href="/dashboard"><i class="fas fa-tachometer-alt"></i> Dashboard</a></li>
                        <li class="nav-item"><a class="nav-link" href="/livros"><i class="fas fa-book"></i> Meus Livros</a></li>
                        <li class="nav-item"><a class="nav-link active" href="/novo_livro"><i class="fas fa-plus-circle"></i> Adicionar Livro</a></li>
                        <li class="nav-item"><a class="nav-link" href="/exportar"><i class="fas fa-download"></i> Exportar</a></li>
                        <li class="nav-item"><a class="nav-link" href="/logout"><i class="fas fa-sign-out-alt"></i> Sair</a></li>
                    </ul>
                </div>
            </nav>

            <main class="col-md-9 ms-sm-auto col-lg-10 px-md-4 py-4">
                <h2><i class="fas fa-plus-circle"></i> Adicionar Novo Livro</h2>
                
                {get_flashed_messages_html()}
                
                <div class="card mt-4">
                    <div class="card-header bg-primary text-white">
                        <h5 class="mb-0"><i class="fas fa-book"></i> Informações do Livro</h5>
                    </div>
                    <div class="card-body">
                        <form method="POST">
                            <div class="row">
                                <div class="col-md-6">
                                    <div class="mb-3">
                                        <label class="form-label"><i class="fas fa-heading"></i> Título do Livro *</label>
                                        <input type="text" class="form-control" name="titulo" required placeholder="Ex: Dom Casmurro">
                                    </div>
                                </div>
                                <div class="col-md-6">
                                    <div class="mb-3">
                                        <label class="form-label"><i class="fas fa-user"></i> Autor *</label>
                                        <input type="text" class="form-control" name="autor" required placeholder="Ex: Machado de Assis">
                                    </div>
                                </div>
                            </div>
                            
                            <div class="row">
                                <div class="col-md-6">
                                    <div class="mb-3">
                                        <label class="form-label"><i class="fas fa-tag"></i> Gênero *</label>
                                        <input type="text" class="form-control" name="genero" required placeholder="Ex: Romance, Ficção, etc.">
                                    </div>
                                </div>
                                <div class="col-md-6">
                                    <div class="mb-3">
                                        <label class="form-label"><i class="fas fa-list"></i> Status *</label>
                                        <select class="form-control" name="status" required>
                                            <option value="quero_ler">Quero Ler</option>
                                            <option value="lendo">Lendo</option>
                                            <option value="lido">Lido</option>
                                        </select>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="row">
                                <div class="col-md-4">
                                    <div class="mb-3">
                                        <label class="form-label"><i class="fas fa-file"></i> Total de Páginas</label>
                                        <input type="number" class="form-control" name="paginas" placeholder="Ex: 256">
                                    </div>
                                </div>
                                <div class="col-md-4">
                                    <div class="mb-3">
                                        <label class="form-label"><i class="fas fa-book-open"></i> Páginas Lidas</label>
                                        <input type="number" class="form-control" name="paginas_lidas" placeholder="Ex: 128">
                                    </div>
                                </div>
                                <div class="col-md-4">
                                    <div class="mb-3">
                                        <label class="form-label"><i class="fas fa-star"></i> Nota (1-5)</label>
                                        <input type="number" class="form-control" name="nota" min="1" max="5" placeholder="Ex: 5">
                                    </div>
                                </div>
                            </div>
                            
                            <div class="mb-3">
                                <label class="form-label"><i class="fas fa-tags"></i> Tags</label>
                                <input type="text" class="form-control" name="tags" placeholder="Ex: literatura brasileira, clássico, romance">
                                <div class="form-text">Separe as tags por vírgula</div>
                            </div>
                            
                            <div class="mb-3">
                                <label class="form-label"><i class="fas fa-image"></i> URL da Imagem</label>
                                <input type="url" class="form-control" name="imagem_url" placeholder="https://exemplo.com/livro.png">
                                <div class="form-text">Cole a URL de uma imagem da capa do livro</div>
                            </div>
                            
                            <div class="d-grid gap-2 d-md-flex justify-content-md-end">
                                <a href="/dashboard" class="btn btn-secondary me-md-2">
                                    <i class="fas fa-times"></i> Cancelar
                                </a>
                                <button type="submit" class="btn btn-primary">
                                    <i class="fas fa-save"></i> Adicionar Livro
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            </main>
        </div>
    </div>
    '''
    
    return render_template_string(BASE_TEMPLATE.replace('{{ content|safe }}', form_template))

@app.route('/livros')
def listar_livros():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
    
    usuario = Usuario.query.get(session['usuario_id'])
    livros = Livro.query.filter_by(usuario_id=usuario.id).order_by(Livro.data_criacao.desc()).all()
    
    livros_html = ''
    if not livros:
        livros_html = '<div class="alert alert-info text-center"><i class="fas fa-info-circle"></i> Nenhum livro cadastrado ainda. <a href="/novo_livro" class="alert-link">Adicione seu primeiro livro!</a></div>'
    else:
        livros_html = '<div class="row">'
        for livro in livros:
            capa_html = f'<img src="{livro.imagem_url}" class="img-fluid h-100 w-100" style="object-fit: cover;">' if livro.imagem_url else '<i class="fas fa-book"></i>'
            tags_html = f'<div class="mt-2">{"".join([f"<span class=\"badge bg-secondary me-1\">{tag.strip()}</span>" for tag in livro.tags.split(",") if livro.tags and tag.strip()])}</div>' if livro.tags else ''
            nota_html = f'<div class="mt-1">{"★" * livro.nota + "☆" * (5 - livro.nota)}</div>' if livro.nota else ''
            
            livros_html += f'''
            <div class='col-md-6 col-lg-4 mb-4'>
                <div class='card book-card h-100'>
                    <div class='book-cover'>
                        {capa_html}
                    </div>
                    <div class='card-body'>
                        <h6 class='card-title'>{livro.titulo}</h6>
                        <p class='card-text'>
                            <strong><i class="fas fa-user"></i> Autor:</strong> {livro.autor}<br>
                            <strong><i class="fas fa-tag"></i> Gênero:</strong> {livro.genero}<br>
                            <strong><i class="fas fa-file"></i> Páginas:</strong> {livro.paginas}
                        </p>
                        <span class='badge bg-{"warning" if livro.status == "lendo" else "success" if livro.status == "lido" else "info"}'>
                            {livro.status.replace("_", " ").title()}
                        </span>
                        {nota_html}
                        {tags_html}
                    </div>
                    <div class='card-footer bg-transparent'>
                        <a href='/detalhes_livro/{livro.id}' class='btn btn-primary btn-sm'><i class="fas fa-eye"></i> Ver</a>
                        <a href='/editar_livro/{livro.id}' class='btn btn-warning btn-sm'><i class="fas fa-edit"></i> Editar</a>
                        <a href='/excluir_livro/{livro.id}' class='btn btn-danger btn-sm' onclick="return confirm('Tem certeza?')"><i class="fas fa-trash"></i> Excluir</a>
                    </div>
                </div>
            </div>'''
        livros_html += '</div>'
    
    livros_content = f'''
    <div class="container-fluid">
        <div class="row">
            <nav class="col-md-3 col-lg-2 d-md-block sidebar">
                <div class="position-sticky pt-3">
                    <div class="text-center mb-4">
                        <i class="fas fa-user-circle fa-3x mb-3"></i>
                        <h5>👤 {session["usuario_nome"]}</h5>
                        <small class="text-light">Leitor</small>
                    </div>
                    <ul class="nav flex-column">
                        <li class="nav-item"><a class="nav-link" href="/dashboard"><i class="fas fa-tachometer-alt"></i> Dashboard</a></li>
                        <li class="nav-item"><a class="nav-link active" href="/livros"><i class="fas fa-book"></i> Meus Livros</a></li>
                        <li class="nav-item"><a class="nav-link" href="/novo_livro"><i class="fas fa-plus-circle"></i> Adicionar Livro</a></li>
                        <li class="nav-item"><a class="nav-link" href="/exportar"><i class="fas fa-download"></i> Exportar</a></li>
                        <li class="nav-item"><a class="nav-link" href="/logout"><i class="fas fa-sign-out-alt"></i> Sair</a></li>
                    </ul>
                </div>
            </nav>

            <main class="col-md-9 ms-sm-auto col-lg-10 px-md-4 py-4">
                <div class="d-flex justify-content-between align-items-center mb-4">
                    <h2><i class="fas fa-book"></i> Meus Livros</h2>
                    <a href="/novo_livro" class="btn btn-primary">
                        <i class="fas fa-plus-circle"></i> Adicionar Livro
                    </a>
                </div>
                
                {get_flashed_messages_html()}
                
                <div class="row">
                    {livros_html}
                </div>
            </main>
        </div>
    </div>
    '''
    
    return render_template_string(BASE_TEMPLATE.replace('{{ content|safe }}', livros_content))

@app.route('/detalhes_livro/<int:livro_id>')
def detalhes_livro(livro_id):
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
    
    livro = Livro.query.get_or_404(livro_id)
    
    if livro.usuario_id != session['usuario_id']:
        flash('Acesso negado!', 'error')
        return redirect(url_for('dashboard'))
    
    progresso = (livro.paginas_lidas / livro.paginas * 100) if livro.paginas and livro.paginas_lidas else 0
    nota_html = "★" * livro.nota + "☆" * (5 - livro.nota) if livro.nota else "Não avaliado"
    tags_html = "".join([f'<span class="badge bg-secondary me-1">{tag.strip()}</span>' for tag in livro.tags.split(",")]) if livro.tags else "Nenhuma tag"
    
    detalhes_content = f'''
    <div class="container-fluid">
        <div class="row">
            <nav class="col-md-3 col-lg-2 d-md-block sidebar">
                <div class="position-sticky pt-3">
                    <div class="text-center mb-4">
                        <i class="fas fa-user-circle fa-3x mb-3"></i>
                        <h5>👤 {session["usuario_nome"]}</h5>
                        <small class="text-light">Leitor</small>
                    </div>
                    <ul class="nav flex-column">
                        <li class="nav-item"><a class="nav-link" href="/dashboard"><i class="fas fa-tachometer-alt"></i> Dashboard</a></li>
                        <li class="nav-item"><a class="nav-link" href="/livros"><i class="fas fa-book"></i> Meus Livros</a></li>
                        <li class="nav-item"><a class="nav-link" href="/novo_livro"><i class="fas fa-plus-circle"></i> Adicionar Livro</a></li>
                        <li class="nav-item"><a class="nav-link active" href="#"><i class="fas fa-eye"></i> Detalhes</a></li>
                        <li class="nav-item"><a class="nav-link" href="/logout"><i class="fas fa-sign-out-alt"></i> Sair</a></li>
                    </ul>
                </div>
            </nav>

            <main class="col-md-9 ms-sm-auto col-lg-10 px-md-4 py-4">
                <div class="d-flex justify-content-between align-items-center mb-4">
                    <h2><i class="fas fa-book"></i> {livro.titulo}</h2>
                    <div>
                        <a href="/editar_livro/{livro.id}" class="btn btn-warning">
                            <i class="fas fa-edit"></i> Editar
                        </a>
                        <a href="/livros" class="btn btn-secondary">
                            <i class="fas fa-arrow-left"></i> Voltar
                        </a>
                    </div>
                </div>
                
                {get_flashed_messages_html()}
                
                <div class="row mt-4">
                    <div class="col-md-4">
                        <div class="card">
                            <div class="book-cover-large">
                                {'<img src="' + livro.imagem_url + '" class="img-fluid h-100 w-100" style="object-fit: cover;">' if livro.imagem_url else '<i class="fas fa-book"></i>'}
                            </div>
                        </div>
                    </div>
                    <div class="col-md-8">
                        <div class="card">
                            <div class="card-header bg-primary text-white">
                                <h5 class="mb-0"><i class="fas fa-info-circle"></i> Informações do Livro</h5>
                            </div>
                            <div class="card-body">
                                <table class="table">
                                    <tr><th width="30%"><i class="fas fa-heading"></i> Título:</th><td>{livro.titulo}</td></tr>
                                    <tr><th><i class="fas fa-user"></i> Autor:</th><td>{livro.autor}</td></tr>
                                    <tr><th><i class="fas fa-tag"></i> Gênero:</th><td>{livro.genero}</td></tr>
                                    <tr><th><i class="fas fa-list"></i> Status:</th><td><span class="badge bg-{"warning" if livro.status == "lendo" else "success" if livro.status == "lido" else "info"}">{livro.status.replace("_", " ").title()}</span></td></tr>
                                    <tr><th><i class="fas fa-file"></i> Páginas:</th><td>{livro.paginas}</td></tr>
                                    <tr><th><i class="fas fa-book-open"></i> Páginas Lidas:</th><td>{livro.paginas_lidas}</td></tr>
                                    <tr><th><i class="fas fa-star"></i> Nota:</th><td>{nota_html}</td></tr>
                                    <tr><th><i class="fas fa-tags"></i> Tags:</th><td>{tags_html}</td></tr>
                                    <tr><th><i class="fas fa-calendar"></i> Adicionado em:</th><td>{livro.data_criacao.strftime('%d/%m/%Y às %H:%M')}</td></tr>
                                </table>
                                
                                {'<div class="mt-4"><h6><i class="fas fa-chart-bar"></i> Progresso de Leitura</h6><div class="progress" style="height: 25px;"><div class="progress-bar" role="progressbar" style="width: ' + str(progresso) + '%;" aria-valuenow="' + str(progresso) + '" aria-valuemin="0" aria-valuemax="100">' + str(round(progresso, 1)) + '%</div></div><small class="text-muted">' + str(livro.paginas_lidas) + ' de ' + str(livro.paginas) + ' páginas lidas</small></div>' if livro.paginas and livro.paginas_lidas else ''}
                            </div>
                        </div>
                    </div>
                </div>
            </main>
        </div>
    </div>
    '''
    
    return render_template_string(BASE_TEMPLATE.replace('{{ content|safe }}', detalhes_content))

@app.route('/editar_livro/<int:livro_id>', methods=['GET', 'POST'])
def editar_livro(livro_id):
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
    
    livro = Livro.query.get_or_404(livro_id)
    
    if livro.usuario_id != session['usuario_id']:
        flash('Acesso negado!', 'error')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        livro.titulo = request.form['titulo']
        livro.autor = request.form['autor']
        livro.genero = request.form['genero']
        livro.status = request.form['status']
        livro.paginas = int(request.form.get('paginas', 0) or 0)
        livro.paginas_lidas = int(request.form.get('paginas_lidas', 0) or 0)
        livro.nota = int(request.form['nota']) if request.form.get('nota') else None
        livro.tags = request.form.get('tags', '')
        livro.imagem_url = request.form.get('imagem_url', '')
        
        db.session.commit()
        flash('Livro atualizado com sucesso!', 'success')
        return redirect(url_for('detalhes_livro', livro_id=livro.id))
    
    form_template = f'''
    <div class="container-fluid">
        <div class="row">
            <nav class="col-md-3 col-lg-2 d-md-block sidebar">
                <div class="position-sticky pt-3">
                    <div class="text-center mb-4">
                        <i class="fas fa-user-circle fa-3x mb-3"></i>
                        <h5>👤 {session["usuario_nome"]}</h5>
                        <small class="text-light">Leitor</small>
                    </div>
                    <ul class="nav flex-column">
                        <li class="nav-item"><a class="nav-link" href="/dashboard"><i class="fas fa-tachometer-alt"></i> Dashboard</a></li>
                        <li class="nav-item"><a class="nav-link" href="/livros"><i class="fas fa-book"></i> Meus Livros</a></li>
                        <li class="nav-item"><a class="nav-link" href="/novo_livro"><i class="fas fa-plus-circle"></i> Adicionar Livro</a></li>
                        <li class="nav-item"><a class="nav-link active" href="#"><i class="fas fa-edit"></i> Editar</a></li>
                        <li class="nav-item"><a class="nav-link" href="/logout"><i class="fas fa-sign-out-alt"></i> Sair</a></li>
                    </ul>
                </div>
            </nav>

            <main class="col-md-9 ms-sm-auto col-lg-10 px-md-4 py-4">
                <h2><i class="fas fa-edit"></i> Editar Livro</h2>
                
                {get_flashed_messages_html()}
                
                <div class="card mt-4">
                    <div class="card-header bg-warning text-white">
                        <h5 class="mb-0"><i class="fas fa-book"></i> Editar Informações do Livro</h5>
                    </div>
                    <div class="card-body">
                        <form method="POST">
                            <div class="row">
                                <div class="col-md-6">
                                    <div class="mb-3">
                                        <label class="form-label"><i class="fas fa-heading"></i> Título do Livro *</label>
                                        <input type="text" class="form-control" name="titulo" required value="{livro.titulo}">
                                    </div>
                                </div>
                                <div class="col-md-6">
                                    <div class="mb-3">
                                        <label class="form-label"><i class="fas fa-user"></i> Autor *</label>
                                        <input type="text" class="form-control" name="autor" required value="{livro.autor}">
                                    </div>
                                </div>
                            </div>
                            
                            <div class="row">
                                <div class="col-md-6">
                                    <div class="mb-3">
                                        <label class="form-label"><i class="fas fa-tag"></i> Gênero *</label>
                                        <input type="text" class="form-control" name="genero" required value="{livro.genero}">
                                    </div>
                                </div>
                                <div class="col-md-6">
                                    <div class="mb-3">
                                        <label class="form-label"><i class="fas fa-list"></i> Status *</label>
                                        <select class="form-control" name="status" required>
                                            <option value="quero_ler" {"selected" if livro.status == "quero_ler" else ""}>Quero Ler</option>
                                            <option value="lendo" {"selected" if livro.status == "lendo" else ""}>Lendo</option>
                                            <option value="lido" {"selected" if livro.status == "lido" else ""}>Lido</option>
                                        </select>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="row">
                                <div class="col-md-4">
                                    <div class="mb-3">
                                        <label class="form-label"><i class="fas fa-file"></i> Total de Páginas</label>
                                        <input type="number" class="form-control" name="paginas" value="{livro.paginas or 0}">
                                    </div>
                                </div>
                                <div class="col-md-4">
                                    <div class="mb-3">
                                        <label class="form-label"><i class="fas fa-book-open"></i> Páginas Lidas</label>
                                        <input type="number" class="form-control" name="paginas_lidas" value="{livro.paginas_lidas or 0}">
                                    </div>
                                </div>
                                <div class="col-md-4">
                                    <div class="mb-3">
                                        <label class="form-label"><i class="fas fa-star"></i> Nota (1-5)</label>
                                        <input type="number" class="form-control" name="nota" min="1" max="5" value="{livro.nota or ""}">
                                    </div>
                                </div>
                            </div>
                            
                            <div class="mb-3">
                                <label class="form-label"><i class="fas fa-tags"></i> Tags</label>
                                <input type="text" class="form-control" name="tags" value="{livro.tags or ""}">
                                <div class="form-text">Separe as tags por vírgula</div>
                            </div>
                            
                            <div class="mb-3">
                                <label class="form-label"><i class="fas fa-image"></i> URL da Imagem</label>
                                <input type="url" class="form-control" name="imagem_url" value="{livro.imagem_url or ""}">
                                <div class="form-text">Cole a URL de uma imagem da capa do livro</div>
                            </div>
                            
                            <div class="d-grid gap-2 d-md-flex justify-content-md-end">
                                <a href="/detalhes_livro/{livro.id}" class="btn btn-secondary me-md-2">
                                    <i class="fas fa-times"></i> Cancelar
                                </a>
                                <button type="submit" class="btn btn-warning">
                                    <i class="fas fa-save"></i> Atualizar Livro
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            </main>
        </div>
    </div>
    '''
    
    return render_template_string(BASE_TEMPLATE.replace('{{ content|safe }}', form_template))

@app.route('/excluir_livro/<int:livro_id>')
def excluir_livro(livro_id):
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
    
    livro = Livro.query.get_or_404(livro_id)
    
    if livro.usuario_id != session['usuario_id']:
        flash('Acesso negado!', 'error')
        return redirect(url_for('dashboard'))
    
    db.session.delete(livro)
    db.session.commit()
    flash('Livro excluído com sucesso!', 'success')
    return redirect(url_for('listar_livros'))

@app.route('/exportar')
def exportar_dados():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
    
    usuario = Usuario.query.get(session['usuario_id'])
    estatisticas = calcular_estatisticas(usuario.id)
    
    export_content = f'''
    <div class="container-fluid">
        <div class="row">
            <nav class="col-md-3 col-lg-2 d-md-block sidebar">
                <div class="position-sticky pt-3">
                    <div class="text-center mb-4">
                        <i class="fas fa-user-circle fa-3x mb-3"></i>
                        <h5>👤 {session["usuario_nome"]}</h5>
                        <small class="text-light">Leitor</small>
                    </div>
                    <ul class="nav flex-column">
                        <li class="nav-item"><a class="nav-link" href="/dashboard"><i class="fas fa-tachometer-alt"></i> Dashboard</a></li>
                        <li class="nav-item"><a class="nav-link" href="/livros"><i class="fas fa-book"></i> Meus Livros</a></li>
                        <li class="nav-item"><a class="nav-link" href="/novo_livro"><i class="fas fa-plus-circle"></i> Adicionar Livro</a></li>
                        <li class="nav-item"><a class="nav-link active" href="/exportar"><i class="fas fa-download"></i> Exportar</a></li>
                        <li class="nav-item"><a class="nav-link" href="/logout"><i class="fas fa-sign-out-alt"></i> Sair</a></li>
                    </ul>
                </div>
            </nav>

            <main class="col-md-9 ms-sm-auto col-lg-10 px-md-4 py-4">
                <div class="d-flex justify-content-between align-items-center mb-4">
                    <h2><i class="fas fa-download"></i> Exportar Dados</h2>
                </div>
                
                {get_flashed_messages_html()}
                
                <div class="row mt-4">
                    <div class="col-md-6 mb-4">
                        <div class="card export-card h-100">
                            <div class="card-body text-center p-5">
                                <i class="fas fa-file-code fa-4x text-primary mb-3"></i>
                                <h4>Exportar JSON</h4>
                                <p class="text-muted mb-4">Exporte todos os seus dados em formato JSON</p>
                                <a href="/exportar_json" class="btn btn-primary btn-lg">
                                    <i class="fas fa-download"></i> Baixar JSON
                                </a>
                            </div>
                        </div>
                    </div>
                    
                    <div class="col-md-6 mb-4">
                        <div class="card export-card h-100">
                            <div class="card-body text-center p-5">
                                <i class="fas fa-file-csv fa-4x text-success mb-3"></i>
                                <h4>Exportar CSV</h4>
                                <p class="text-muted mb-4">Formato ideal para planilhas Excel</p>
                                <a href="/exportar_csv" class="btn btn-success btn-lg">
                                    <i class="fas fa-download"></i> Baixar CSV
                                </a>
                            </div>
                        </div>
                    </div>
                </div>
            </main>
        </div>
    </div>
    '''
    
    return render_template_string(BASE_TEMPLATE.replace('{{ content|safe }}', export_content))

@app.route('/exportar_json')
def exportar_json():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
    
    usuario = Usuario.query.get(session['usuario_id'])
    livros = Livro.query.filter_by(usuario_id=usuario.id).all()
    estatisticas = calcular_estatisticas(usuario.id)
    
    dados = {
        'metadata': {
            'sistema': 'LivroTracker',
            'data_exportacao': datetime.now().isoformat(),
            'usuario': usuario.nome,
            'total_registros': len(livros)
        },
        'estatisticas': estatisticas,
        'livros': [
            {
                'titulo': livro.titulo,
                'autor': livro.autor,
                'genero': livro.genero,
                'status': livro.status,
                'paginas': livro.paginas,
                'paginas_lidas': livro.paginas_lidas,
                'nota': livro.nota,
                'tags': livro.tags,
                'imagem_url': livro.imagem_url,
                'data_cadastro': livro.data_criacao.strftime('%d/%m/%Y')
            }
            for livro in livros
        ]
    }
    
    return jsonify(dados)

@app.route('/exportar_csv')
def exportar_csv():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
    
    usuario = Usuario.query.get(session['usuario_id'])
    livros = Livro.query.filter_by(usuario_id=usuario.id).all()
    
    output = StringIO()
    writer = csv.writer(output)
    
    writer.writerow(['Título', 'Autor', 'Gênero', 'Status', 'Páginas', 'Páginas Lidas', 'Nota', 'Tags', 'Data Cadastro'])
    
    for livro in livros:
        writer.writerow([
            livro.titulo,
            livro.autor,
            livro.genero,
            livro.status,
            livro.paginas,
            livro.paginas_lidas,
            livro.nota or '',
            livro.tags or '',
            livro.data_criacao.strftime('%d/%m/%Y')
        ])
    
    response = Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={
            'Content-Disposition': f'attachment; filename=livros_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        }
    )
    
    return response

# =============================================
# REDIRECIONAMENTOS PARA COMPATIBILIDADE
# =============================================

@app.route('/exportar_livros')
def exportar_livros_redirect():
    return redirect(url_for('exportar_dados'))

@app.route('/logout')
def logout():
    session.clear()
    flash('Logout realizado com sucesso!', 'success')
    return redirect(url_for('login'))

# =============================================
# INICIALIZAÇÃO
# =============================================

def init_database():
    with app.app_context():
        db.create_all()
        print("✅ Banco de dados inicializado!")

if __name__ == '__main__':
    init_database()
    port = int(os.environ.get('PORT', 10000))
    print("🚀 Sistema de Registro de Livros iniciando...")
    print("📚 Acesse: http://localhost:10000")
    app.run(debug=False, host='0.0.0.0', port=port)
