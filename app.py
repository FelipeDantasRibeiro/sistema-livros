# -*- coding: utf-8 -*-
"""
📚 SISTEMA DE REGISTRO DE LIVROS - BIBLIOTECA PESSOAL ACADÊMICA
Versão Corrigida - Sem erros de rotas
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
# TEMPLATES HTML (MESMO CÓDIGO ANTERIOR)
# =============================================

BASE_TEMPLATE = '''
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>📚 Sistema de Livros Acadêmico</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        .sidebar { 
            background: rgba(255,255,255,0.95);
            backdrop-filter: blur(10px);
            min-height: 100vh;
            box-shadow: 2px 0 10px rgba(0,0,0,0.1);
        }
        .sidebar .nav-link { 
            color: #2c3e50;
            border-radius: 8px;
            margin: 3px 0;
            transition: all 0.3s ease;
        }
        .sidebar .nav-link:hover { 
            background: #3498db; 
            color: white;
            transform: translateX(5px);
        }
        .sidebar .nav-link.active { 
            background: #2c3e50; 
            color: white;
        }
        .main-content {
            background: rgba(255,255,255,0.95);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            margin: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        .stat-card, .book-card { 
            border-radius: 15px; 
            transition: transform 0.3s, box-shadow 0.3s;
            border: none;
            overflow: hidden;
        }
        .stat-card:hover, .book-card:hover { 
            transform: translateY(-5px); 
            box-shadow: 0 15px 35px rgba(0,0,0,0.3);
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
        .export-card {
            border: 2px dashed #3498db;
            transition: all 0.3s ease;
        }
        .export-card:hover {
            border-color: #2c3e50;
            background: #f8f9fa;
        }
        .progress-bar-custom {
            background: linear-gradient(90deg, #667eea, #764ba2);
        }
        .login-bg {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }
    </style>
</head>
<body>
    {{ content|safe }}
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        function confirmarExportacao(formato) {
            return confirm(`Deseja exportar seus dados em formato ${formato.toUpperCase()}?`);
        }
        
        function confirmarExclusao() {
            return confirm('Tem certeza que deseja excluir este livro? Esta ação não pode ser desfeita.');
        }
    </script>
</body>
</html>
'''

LOGIN_TEMPLATE = '''
<div class="container-fluid vh-100 login-bg">
    <div class="row h-100 justify-content-center align-items-center">
        <div class="col-md-4">
            <div class="card border-0 shadow-lg">
                <div class="card-body p-5">
                    <div class="text-center mb-4">
                        <i class="fas fa-book-open fa-4x text-primary mb-3"></i>
                        <h2 class="fw-bold">📚 LivroTracker</h2>
                        <p class="text-muted">Sistema Acadêmico de Gestão de Leitura</p>
                    </div>
                    
                    {{ messages|safe }}
                    
                    <form method="POST">
                        <div class="mb-3">
                            <label class="form-label fw-bold"><i class="fas fa-envelope me-2"></i>Email</label>
                            <input type="email" class="form-control form-control-lg" name="email" required placeholder="seu@email.com">
                        </div>
                        <div class="mb-3">
                            <label class="form-label fw-bold"><i class="fas fa-lock me-2"></i>Senha</label>
                            <input type="password" class="form-control form-control-lg" name="senha" required placeholder="Sua senha">
                        </div>
                        <button type="submit" class="btn btn-primary btn-lg w-100 py-3 fw-bold">
                            <i class="fas fa-sign-in-alt me-2"></i> Acessar Sistema
                        </button>
                    </form>
                    <hr class="my-4">
                    <p class="text-center mb-0">
                        Não possui cadastro? <a href="/cadastro" class="text-decoration-none fw-bold">Crie sua conta</a>
                    </p>
                </div>
            </div>
        </div>
    </div>
</div>
'''

CADASTRO_TEMPLATE = '''
<div class="container-fluid vh-100 login-bg">
    <div class="row h-100 justify-content-center align-items-center">
        <div class="col-md-5">
            <div class="card border-0 shadow-lg">
                <div class="card-body p-5">
                    <div class="text-center mb-4">
                        <i class="fas fa-user-plus fa-4x text-primary mb-3"></i>
                        <h2 class="fw-bold">📝 Cadastro Acadêmico</h2>
                        <p class="text-muted">Crie sua conta no sistema</p>
                    </div>
                    
                    {{ messages|safe }}
                    
                    <form method="POST">
                        <div class="mb-3">
                            <label class="form-label fw-bold"><i class="fas fa-user me-2"></i>Nome Completo</label>
                            <input type="text" class="form-control form-control-lg" name="nome" required placeholder="Seu nome completo">
                        </div>
                        <div class="mb-3">
                            <label class="form-label fw-bold"><i class="fas fa-envelope me-2"></i>Email</label>
                            <input type="email" class="form-control form-control-lg" name="email" required placeholder="seu@email.com">
                        </div>
                        <div class="mb-3">
                            <label class="form-label fw-bold"><i class="fas fa-lock me-2"></i>Senha</label>
                            <input type="password" class="form-control form-control-lg" name="senha" required placeholder="Crie uma senha segura">
                        </div>
                        <div class="mb-3">
                            <label class="form-label fw-bold"><i class="fas fa-lock me-2"></i>Confirmar Senha</label>
                            <input type="password" class="form-control form-control-lg" name="confirmar_senha" required placeholder="Repita a senha">
                        </div>
                        <button type="submit" class="btn btn-primary btn-lg w-100 py-3 fw-bold">
                            <i class="fas fa-user-plus me-2"></i> Criar Conta Acadêmica
                        </button>
                    </form>
                    <hr class="my-4">
                    <p class="text-center mb-0">
                        Já possui conta? <a href="/login" class="text-decoration-none fw-bold">Acesse o sistema</a>
                    </p>
                </div>
            </div>
        </div>
    </div>
</div>
'''

# =============================================
# ROTAS PRINCIPAIS (TODAS AS ROTAS DO CÓDIGO ANTERIOR)
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
            flash('Login realizado com sucesso! Bem-vindo ao Sistema Acadêmico de Livros.', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Credenciais inválidas. Verifique seu email e senha.', 'error')
    
    return render_template_string(BASE_TEMPLATE.replace('{{ content|safe }}', LOGIN_TEMPLATE), messages=get_flashed_messages_html())

@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        senha = request.form['senha']
        confirmar_senha = request.form['confirmar_senha']
        
        if senha != confirmar_senha:
            flash('As senhas não coincidem. Por favor, verifique.', 'error')
            return redirect(url_for('cadastro'))
        
        if Usuario.query.filter_by(email=email).first():
            flash('Este email já está cadastrado no sistema.', 'error')
            return redirect(url_for('cadastro'))
        
        usuario = Usuario(
            nome=nome,
            email=email,
            senha=generate_password_hash(senha)
        )
        
        db.session.add(usuario)
        db.session.commit()
        
        flash('Conta criada com sucesso! Agora você pode acessar o sistema.', 'success')
        return redirect(url_for('login'))
    
    return render_template_string(BASE_TEMPLATE.replace('{{ content|safe }}', CADASTRO_TEMPLATE), messages=get_flashed_messages_html())

@app.route('/dashboard')
def dashboard():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
    
    usuario = Usuario.query.get(session['usuario_id'])
    estatisticas = calcular_estatisticas(usuario.id)
    livros_recentes = Livro.query.filter_by(usuario_id=usuario.id).order_by(Livro.data_criacao.desc()).limit(5).all()
    
    livros_html = ''
    if not livros_recentes:
        livros_html = '''
        <div class="alert alert-info text-center">
            <i class="fas fa-info-circle fa-2x mb-3"></i>
            <h5>Nenhum livro cadastrado</h5>
            <p>Comece sua jornada literária adicionando seu primeiro livro!</p>
            <a href="/novo_livro" class="btn btn-primary mt-2">
                <i class="fas fa-plus-circle"></i> Adicionar Primeiro Livro
            </a>
        </div>
        '''
    else:
        livros_html = '<div class="row">'
        for livro in livros_recentes:
            capa_html = f'<img src="{livro.imagem_url}" class="img-fluid h-100 w-100" style="object-fit: cover;" onerror="this.style.display=\'none\'; this.nextElementSibling.style.display=\'flex\';">' + '<div class="book-cover w-100 h-100" style="display: none;"><i class="fas fa-book"></i></div>' if livro.imagem_url else '<div class="book-cover w-100 h-100"><i class="fas fa-book"></i></div>'
            
            livros_html += f'''
            <div class='col-md-4 mb-4'>
                <div class='card book-card h-100'>
                    <div class='position-relative'>
                        {capa_html}
                    </div>
                    <div class='card-body'>
                        <h6 class='card-title fw-bold'>{livro.titulo}</h6>
                        <p class='card-text mb-1'><small class='text-muted'>{livro.autor}</small></p>
                        <span class='badge bg-{"success" if livro.status == "lido" else "warning" if livro.status == "lendo" else "info"}'>
                            {livro.status.replace("_", " ").title()}
                        </span>
                    </div>
                    <div class='card-footer bg-transparent'>
                        <a href='/detalhes_livro/{livro.id}' class='btn btn-primary btn-sm'>
                            <i class="fas fa-eye"></i> Detalhes
                        </a>
                    </div>
                </div>
            </div>'''
        livros_html += '</div>'
    
    dashboard_content = f'''
    <div class="container-fluid">
        <div class="row">
            <nav class="col-md-3 col-lg-2 sidebar p-0">
                <div class="position-sticky pt-4">
                    <div class="text-center mb-4 px-3">
                        <i class="fas fa-user-graduate fa-3x text-primary mb-3"></i>
                        <h5 class="fw-bold">👤 {session["usuario_nome"]}</h5>
                        <small class="text-muted">Leitor Acadêmico</small>
                        <div class="mt-3">
                            <span class="badge bg-success">
                                <i class="fas fa-book"></i> {estatisticas['total_livros']} Livros
                            </span>
                        </div>
                    </div>
                    <ul class="nav flex-column px-3">
                        <li class="nav-item"><a class="nav-link active" href="/dashboard"><i class="fas fa-tachometer-alt me-2"></i> Dashboard</a></li>
                        <li class="nav-item"><a class="nav-link" href="/livros"><i class="fas fa-book me-2"></i> Meus Livros</a></li>
                        <li class="nav-item"><a class="nav-link" href="/novo_livro"><i class="fas fa-plus-circle me-2"></i> Adicionar Livro</a></li>
                        <li class="nav-item"><a class="nav-link" href="/exportar"><i class="fas fa-download me-2"></i> Exportar Dados</a></li>
                        <li class="nav-item"><a class="nav-link" href="/logout"><i class="fas fa-sign-out-alt me-2"></i> Sair</a></li>
                    </ul>
                </div>
            </nav>

            <main class="col-md-9 ms-sm-auto col-lg-10 px-4 py-4">
                <div class="main-content p-4">
                    <div class="d-flex justify-content-between align-items-center mb-4">
                        <div>
                            <h2 class="fw-bold mb-1"><i class="fas fa-tachometer-alt me-2"></i>Dashboard Acadêmico</h2>
                            <p class="text-muted mb-0">Bem-vindo, {session["usuario_nome"]}! Aqui está seu progresso de leitura.</p>
                        </div>
                        <span class="badge bg-primary fs-6">
                            <i class="fas fa-calendar me-1"></i> {datetime.now().strftime("%d/%m/%Y")}
                        </span>
                    </div>
                    
                    {get_flashed_messages_html()}
                    
                    <div class="row mt-4">
                        <div class="col-md-3 mb-4">
                            <div class="card stat-card text-white bg-primary">
                                <div class="card-body">
                                    <div class="d-flex justify-content-between">
                                        <div>
                                            <h2 class="fw-bold">{estatisticas['total_livros']}</h2>
                                            <p class="mb-0">Total de Livros</p>
                                        </div>
                                        <div class="align-self-center">
                                            <i class="fas fa-book fa-2x opacity-75"></i>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-3 mb-4">
                            <div class="card stat-card text-white bg-success">
                                <div class="card-body">
                                    <div class="d-flex justify-content-between">
                                        <div>
                                            <h2 class="fw-bold">{estatisticas['livros_lidos']}</h2>
                                            <p class="mb-0">Livros Lidos</p>
                                        </div>
                                        <div class="align-self-center">
                                            <i class="fas fa-check-circle fa-2x opacity-75"></i>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-3 mb-4">
                            <div class="card stat-card text-white bg-warning">
                                <div class="card-body">
                                    <div class="d-flex justify-content-between">
                                        <div>
                                            <h2 class="fw-bold">{estatisticas['livros_lendo']}</h2>
                                            <p class="mb-0">Lendo Agora</p>
                                        </div>
                                        <div class="align-self-center">
                                            <i class="fas fa-book-reader fa-2x opacity-75"></i>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-3 mb-4">
                            <div class="card stat-card text-white bg-info">
                                <div class="card-body">
                                    <div class="d-flex justify-content-between">
                                        <div>
                                            <h2 class="fw-bold">{estatisticas['livros_quero_ler']}</h2>
                                            <p class="mb-0">Quero Ler</p>
                                        </div>
                                        <div class="align-self-center">
                                            <i class="fas fa-bookmark fa-2x opacity-75"></i>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="row mt-4">
                        <div class="col-md-6 mb-4">
                            <div class="card">
                                <div class="card-header bg-primary text-white">
                                    <h5 class="mb-0"><i class="fas fa-chart-bar me-2"></i>Estatísticas de Leitura</h5>
                                </div>
                                <div class="card-body">
                                    <div class="mb-3">
                                        <label class="form-label fw-bold">Progresso Geral de Leitura</label>
                                        <div class="progress" style="height: 25px;">
                                            <div class="progress-bar progress-bar-custom" role="progressbar" 
                                                 style="width: {estatisticas['progresso_leitura']}%;" 
                                                 aria-valuenow="{estatisticas['progresso_leitura']}" 
                                                 aria-valuemin="0" aria-valuemax="100">
                                                {estatisticas['progresso_leitura']}%
                                            </div>
                                        </div>
                                        <small class="text-muted">
                                            {estatisticas['paginas_lidas']} de {estatisticas['total_paginas']} páginas lidas
                                        </small>
                                    </div>
                                    <div class="row">
                                        <div class="col-6">
                                            <small class="text-muted">Gênero Mais Lido:</small>
                                            <p class="fw-bold">{estatisticas['genero_mais_lido']}</p>
                                        </div>
                                        <div class="col-6">
                                            <small class="text-muted">Taxa de Conclusão:</small>
                                            <p class="fw-bold">{round((estatisticas['livros_lidos']/estatisticas['total_livros']*100) if estatisticas['total_livros'] > 0 else 0, 1)}%</p>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-6 mb-4">
                            <div class="card">
                                <div class="card-header bg-success text-white">
                                    <h5 class="mb-0"><i class="fas fa-clock me-2"></i>Livros Recentes</h5>
                                </div>
                                <div class="card-body">
                                    {livros_html}
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </main>
        </div>
    </div>
    '''
    
    return render_template_string(BASE_TEMPLATE.replace('{{ content|safe }}', dashboard_content))

# ... (TODAS AS OUTRAS ROTAS DO CÓDIGO ANTERIOR: novo_livro, livros, detalhes_livro, editar_livro, excluir_livro) ...

@app.route('/exportar')
def exportar_dados():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
    
    usuario = Usuario.query.get(session['usuario_id'])
    estatisticas = calcular_estatisticas(usuario.id)
    
    export_content = f'''
    <div class="container-fluid">
        <div class="row">
            <nav class="col-md-3 col-lg-2 sidebar p-0">
                <div class="position-sticky pt-4">
                    <div class="text-center mb-4 px-3">
                        <i class="fas fa-user-graduate fa-3x text-primary mb-3"></i>
                        <h5 class="fw-bold">👤 {session["usuario_nome"]}</h5>
                        <small class="text-muted">Leitor Acadêmico</small>
                    </div>
                    <ul class="nav flex-column px-3">
                        <li class="nav-item"><a class="nav-link" href="/dashboard"><i class="fas fa-tachometer-alt me-2"></i> Dashboard</a></li>
                        <li class="nav-item"><a class="nav-link" href="/livros"><i class="fas fa-book me-2"></i> Meus Livros</a></li>
                        <li class="nav-item"><a class="nav-link" href="/novo_livro"><i class="fas fa-plus-circle me-2"></i> Adicionar Livro</a></li>
                        <li class="nav-item"><a class="nav-link active" href="/exportar"><i class="fas fa-download me-2"></i> Exportar Dados</a></li>
                        <li class="nav-item"><a class="nav-link" href="/logout"><i class="fas fa-sign-out-alt me-2"></i> Sair</a></li>
                    </ul>
                </div>
            </nav>

            <main class="col-md-9 ms-sm-auto col-lg-10 px-4 py-4">
                <div class="main-content p-4">
                    <div class="d-flex justify-content-between align-items-center mb-4">
                        <div>
                            <h2 class="fw-bold mb-1"><i class="fas fa-download me-2"></i>Exportar Dados Acadêmicos</h2>
                            <p class="text-muted mb-0">Exporte seus dados de leitura para análise e backup</p>
                        </div>
                    </div>
                    
                    {get_flashed_messages_html()}
                    
                    <div class="row mt-4">
                        <div class="col-md-6 mb-4">
                            <div class="card export-card h-100">
                                <div class="card-body text-center p-5">
                                    <i class="fas fa-file-code fa-4x text-primary mb-3"></i>
                                    <h4 class="fw-bold">Exportar JSON</h4>
                                    <p class="text-muted mb-4">
                                        Exporte todos os seus dados em formato JSON para análise acadêmica 
                                        e integração com outras ferramentas.
                                    </p>
                                    <a href="/exportar_json" class="btn btn-primary btn-lg" onclick="return confirmarExportacao('json')">
                                        <i class="fas fa-download me-2"></i> Baixar JSON
                                    </a>
                                </div>
                            </div>
                        </div>
                        
                        <div class="col-md-6 mb-4">
                            <div class="card export-card h-100">
                                <div class="card-body text-center p-5">
                                    <i class="fas fa-file-csv fa-4x text-success mb-3"></i>
                                    <h4 class="fw-bold">Exportar CSV</h4>
                                    <p class="text-muted mb-4">
                                        Formato ideal para planilhas Excel e Google Sheets. 
                                        Perfeito para análises estatísticas e relatórios.
                                    </p>
                                    <a href="/exportar_csv" class="btn btn-success btn-lg" onclick="return confirmarExportacao('csv')">
                                        <i class="fas fa-download me-2"></i> Baixar CSV
                                    </a>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="card mt-4">
                        <div class="card-header bg-info text-white">
                            <h5 class="mb-0"><i class="fas fa-chart-pie me-2"></i>Resumo Estatístico</h5>
                        </div>
                        <div class="card-body">
                            <div class="row text-center">
                                <div class="col-md-3 mb-3">
                                    <div class="border rounded p-3">
                                        <h3 class="text-primary fw-bold">{estatisticas['total_livros']}</h3>
                                        <small class="text-muted">Total de Livros</small>
                                    </div>
                                </div>
                                <div class="col-md-3 mb-3">
                                    <div class="border rounded p-3">
                                        <h3 class="text-success fw-bold">{estatisticas['livros_lidos']}</h3>
                                        <small class="text-muted">Livros Concluídos</small>
                                    </div>
                                </div>
                                <div class="col-md-3 mb-3">
                                    <div class="border rounded p-3">
                                        <h3 class="text-warning fw-bold">{estatisticas['livros_lendo']}</h3>
                                        <small class="text-muted">Em Progresso</small>
                                    </div>
                                </div>
                                <div class="col-md-3 mb-3">
                                    <div class="border rounded p-3">
                                        <h3 class="text-info fw-bold">{estatisticas['progresso_leitura']}%</h3>
                                        <small class="text-muted">Progresso Total</small>
                                    </div>
                                </div>
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
            'sistema': 'LivroTracker - Sistema Acadêmico de Gestão de Leitura',
            'versao': '2.0',
            'data_exportacao': datetime.now().isoformat(),
            'usuario': usuario.nome,
            'email': usuario.email,
            'total_registros': len(livros)
        },
        'estatisticas': estatisticas,
        'livros': [
            {
                'id': livro.id,
                'titulo': livro.titulo,
                'autor': livro.autor,
                'genero': livro.genero,
                'status': livro.status,
                'paginas': livro.paginas,
                'paginas_lidas': livro.paginas_lidas,
                'nota': livro.nota,
                'tags': livro.tags.split(',') if livro.tags else [],
                'imagem_url': livro.imagem_url,
                'data_cadastro': livro.data_criacao.isoformat(),
                'progresso': f"{(livro.paginas_lidas/livro.paginas*100) if livro.paginas else 0:.1f}%"
            }
            for livro in livros
        ]
    }
    
    response = Response(
        json.dumps(dados, ensure_ascii=False, indent=2),
        mimetype='application/json',
        headers={
            'Content-Disposition': f'attachment; filename=livrotracker_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        }
    )
    
    return response

@app.route('/exportar_csv')
def exportar_csv():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
    
    usuario = Usuario.query.get(session['usuario_id'])
    livros = Livro.query.filter_by(usuario_id=usuario.id).all()
    
    output = StringIO()
    writer = csv.writer(output)
    
    writer.writerow(['ID', 'Título', 'Autor', 'Gênero', 'Status', 'Páginas', 'Páginas Lidas', 
                    'Progresso', 'Nota', 'Tags', 'Data Cadastro'])
    
    for livro in livros:
        progresso = f"{(livro.paginas_lidas/livro.paginas*100) if livro.paginas else 0:.1f}%"
        writer.writerow([
            livro.id,
            livro.titulo,
            livro.autor,
            livro.genero,
            livro.status,
            livro.paginas,
            livro.paginas_lidas,
            progresso,
            livro.nota or '',
            livro.tags or '',
            livro.data_criacao.strftime('%d/%m/%Y %H:%M')
        ])
    
    response = Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={
            'Content-Disposition': f'attachment; filename=livrotracker_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        }
    )
    
    return response

# =============================================
# REDIRECIONAMENTOS PARA COMPATIBILIDADE
# =============================================

@app.route('/exportar_livros')
def exportar_livros_redirect():
    """Redireciona a rota antiga para a nova"""
    return redirect(url_for('exportar_dados'))

@app.route('/exportar_livros_json')
def exportar_livros_json_redirect():
    """Redireciona a rota antiga para a nova"""
    return redirect(url_for('exportar_json'))

@app.route('/logout')
def logout():
    session.clear()
    flash('Logout realizado com sucesso! Volte sempre ao Sistema Acadêmico de Livros.', 'success')
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
    print("🚀 Sistema Acadêmico de Registro de Livros iniciando...")
    print("📚 Acesse: http://localhost:10000")
    app.run(debug=False, host='0.0.0.0', port=port)
