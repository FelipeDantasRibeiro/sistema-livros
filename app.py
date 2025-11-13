# -*- coding: utf-8 -*-
"""
📚 SISTEMA DE LIVROS - VERSÃO SIMPLES E FUNCIONAL
"""

import os
from flask import Flask, render_template_string, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# =============================================
# CONFIGURAÇÃO BÁSICA
# =============================================

app = Flask(__name__)
app.config['SECRET_KEY'] = 'chave-simples-para-teste'
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///teste.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# =============================================
# MODELOS SIMPLES
# =============================================

class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    senha = db.Column(db.String(100))
    nome = db.Column(db.String(100))

class Livro(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(200))
    autor = db.Column(db.String(100))
    usuario_id = db.Column(db.Integer)

# =============================================
# PÁGINA INICIAL - SEM LOGIN
# =============================================

@app.route('/')
def index():
    html = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Sistema de Livros</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body class="bg-light">
        <div class="container mt-5">
            <div class="row justify-content-center">
                <div class="col-md-6 text-center">
                    <h1>📚 Sistema de Livros</h1>
                    <p class="lead">Gerencie sua biblioteca pessoal</p>
                    <div class="mt-4">
                        <a href="/login" class="btn btn-primary btn-lg me-3">Entrar</a>
                        <a href="/cadastro" class="btn btn-outline-primary btn-lg">Cadastrar</a>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    '''
    return html

# =============================================
# LOGIN SIMPLES
# =============================================

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        
        # Login simples - apenas verifica se o usuário existe
        usuario = Usuario.query.filter_by(email=email).first()
        if usuario:
            session['usuario_id'] = usuario.id
            session['usuario_nome'] = usuario.nome
            return redirect('/dashboard')
        else:
            return "Usuário não encontrado. <a href='/cadastro'>Cadastre-se</a>"
    
    html = '''
    <div class="container mt-5">
        <div class="row justify-content-center">
            <div class="col-md-4">
                <div class="card">
                    <div class="card-body">
                        <h3 class="text-center">Login</h3>
                        <form method="POST">
                            <div class="mb-3">
                                <label>Email</label>
                                <input type="email" class="form-control" name="email" required>
                            </div>
                            <div class="mb-3">
                                <label>Senha</label>
                                <input type="password" class="form-control" name="senha">
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
    return html

# =============================================
# CADASTRO SIMPLES
# =============================================

@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        
        # Cria usuário simples
        usuario = Usuario(nome=nome, email=email, senha='123')
        db.session.add(usuario)
        db.session.commit()
        
        session['usuario_id'] = usuario.id
        session['usuario_nome'] = usuario.nome
        return redirect('/dashboard')
    
    html = '''
    <div class="container mt-5">
        <div class="row justify-content-center">
            <div class="col-md-4">
                <div class="card">
                    <div class="card-body">
                        <h3 class="text-center">Cadastro</h3>
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
                                <input type="password" class="form-control" name="senha">
                            </div>
                            <button type="submit" class="btn btn-primary w-100">Cadastrar</button>
                        </form>
                        <p class="text-center mt-3">
                            <a href="/login">Já tem conta?</a>
                        </p>
                    </div>
                </div>
            </div>
        </div>
    </div>
    '''
    return html

# =============================================
# DASHBOARD SUPER SIMPLES
# =============================================

@app.route('/dashboard')
def dashboard():
    if 'usuario_id' not in session:
        return redirect('/login')
    
    # Conta livros de forma simples
    total_livros = Livro.query.filter_by(usuario_id=session['usuario_id']).count()
    
    html = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Dashboard</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body>
        <nav class="navbar navbar-dark bg-dark">
            <div class="container">
                <span class="navbar-brand">📚 Meus Livros</span>
                <span class="text-light">Olá, {session.get('usuario_nome', 'Usuário')}</span>
                <a href="/logout" class="btn btn-outline-light btn-sm">Sair</a>
            </div>
        </nav>
        
        <div class="container mt-4">
            <h2>Dashboard</h2>
            
            <div class="row mt-4">
                <div class="col-md-3">
                    <div class="card text-white bg-primary">
                        <div class="card-body">
                            <h3>{total_livros}</h3>
                            <p>Total de Livros</p>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="card mt-4">
                <div class="card-body">
                    <h5>Bem-vindo ao seu sistema de livros!</h5>
                    <p>Total de livros no seu acervo: <strong>{total_livros}</strong></p>
                    <a href="/adicionar_livro" class="btn btn-success">➕ Adicionar Livro</a>
                    <a href="/meus_livros" class="btn btn-primary">📚 Ver Meus Livros</a>
                </div>
            </div>
        </div>
    </body>
    </html>
    '''
    return html

# =============================================
# ADICIONAR LIVRO SIMPLES
# =============================================

@app.route('/adicionar_livro', methods=['GET', 'POST'])
def adicionar_livro():
    if 'usuario_id' not in session:
        return redirect('/login')
    
    if request.method == 'POST':
        titulo = request.form['titulo']
        autor = request.form['autor']
        
        livro = Livro(
            titulo=titulo,
            autor=autor,
            usuario_id=session['usuario_id']
        )
        db.session.add(livro)
        db.session.commit()
        
        return redirect('/dashboard')
    
    html = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Adicionar Livro</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body>
        <nav class="navbar navbar-dark bg-dark">
            <div class="container">
                <span class="navbar-brand">📚 Adicionar Livro</span>
                <a href="/dashboard" class="btn btn-outline-light btn-sm">Voltar</a>
            </div>
        </nav>
        
        <div class="container mt-4">
            <h2>Adicionar Novo Livro</h2>
            
            <div class="card mt-4">
                <div class="card-body">
                    <form method="POST">
                        <div class="mb-3">
                            <label class="form-label">Título do Livro</label>
                            <input type="text" class="form-control" name="titulo" required>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Autor</label>
                            <input type="text" class="form-control" name="autor" required>
                        </div>
                        <button type="submit" class="btn btn-success">Adicionar Livro</button>
                        <a href="/dashboard" class="btn btn-secondary">Cancelar</a>
                    </form>
                </div>
            </div>
        </div>
    </body>
    </html>
    '''
    return html

# =============================================
# MEUS LIVROS SIMPLES
# =============================================

@app.route('/meus_livros')
def meus_livros():
    if 'usuario_id' not in session:
        return redirect('/login')
    
    livros = Livro.query.filter_by(usuario_id=session['usuario_id']).all()
    
    livros_html = ''
    for livro in livros:
        livros_html += f'''
        <div class="col-md-4 mb-3">
            <div class="card">
                <div class="card-body">
                    <h5>{livro.titulo}</h5>
                    <p><strong>Autor:</strong> {livro.autor}</p>
                </div>
            </div>
        </div>
        '''
    
    html = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Meus Livros</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body>
        <nav class="navbar navbar-dark bg-dark">
            <div class="container">
                <span class="navbar-brand">📚 Meus Livros</span>
                <div>
                    <a href="/adicionar_livro" class="btn btn-success btn-sm me-2">➕ Adicionar</a>
                    <a href="/dashboard" class="btn btn-outline-light btn-sm">Voltar</a>
                </div>
            </div>
        </nav>
        
        <div class="container mt-4">
            <h2>Meus Livros</h2>
            
            <div class="row mt-4">
                {livros_html if livros else '<div class="col-12"><div class="alert alert-info">Nenhum livro cadastrado ainda.</div></div>'}
            </div>
        </div>
    </body>
    </html>
    '''
    return html

# =============================================
# LOGOUT
# =============================================

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# =============================================
# INICIALIZAÇÃO
# =============================================

def init_db():
    with app.app_context():
        db.create_all()
        print("✅ Banco de dados inicializado!")
        
        # Criar usuário de teste se não existir
        if not Usuario.query.filter_by(email="teste@teste.com").first():
            usuario = Usuario(nome="Usuário Teste", email="teste@teste.com", senha="123")
            db.session.add(usuario)
            db.session.commit()
            print("✅ Usuário teste criado: teste@teste.com")

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 10000))
    print(f"🚀 Servidor rodando na porta {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
