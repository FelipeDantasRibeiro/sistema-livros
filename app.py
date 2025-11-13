# -*- coding: utf-8 -*-
"""
📚 SISTEMA DE LIVROS - VERSÃO RAILWAY OTIMIZADA
"""

import os
from flask import Flask, request, redirect, session, render_template_string
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'chave-secreta-padrao')

# =============================================
# CONFIGURAÇÃO DO BANCO DE DADOS
# =============================================

def get_db_connection():
    """Cria conexão com o banco SQLite"""
    conn = sqlite3.connect('livros.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Inicializa o banco de dados com tabelas necessárias"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Tabela de usuários
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            senha TEXT NOT NULL,
            data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Tabela de livros
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS livros (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT NOT NULL,
            autor TEXT NOT NULL,
            genero TEXT,
            status TEXT DEFAULT 'quero_ler',
            paginas INTEGER DEFAULT 0,
            paginas_lidas INTEGER DEFAULT 0,
            nota INTEGER,
            usuario_id INTEGER NOT NULL,
            data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
        )
    ''')
    
    # Criar usuário de teste se não existir
    cursor.execute("SELECT id FROM usuarios WHERE email = 'teste@teste.com'")
    if not cursor.fetchone():
        cursor.execute(
            "INSERT INTO usuarios (nome, email, senha) VALUES (?, ?, ?)",
            ('Usuário Teste', 'teste@teste.com', '123')
        )
        print("✅ Usuário teste criado: teste@teste.com / 123")
    
    conn.commit()
    conn.close()
    print("✅ Banco de dados inicializado com sucesso!")

# Inicializar banco na primeira execução
init_db()

# =============================================
# FUNÇÕES AUXILIARES
# =============================================

def get_user_books_count(user_id):
    """Retorna estatísticas dos livros do usuário"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM livros WHERE usuario_id = ?", (user_id,))
    total_livros = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM livros WHERE usuario_id = ? AND status = 'lido'", (user_id,))
    livros_lidos = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM livros WHERE usuario_id = ? AND status = 'lendo'", (user_id,))
    livros_lendo = cursor.fetchone()[0]
    
    conn.close()
    
    return {
        'total': total_livros,
        'lidos': livros_lidos,
        'lendo': livros_lendo
    }

# =============================================
# ROTAS PRINCIPAIS
# =============================================

@app.route('/')
def index():
    """Página inicial"""
    return '''
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>📚 Sistema de Livros</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            .hero-section {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 80px 0;
                border-radius: 0 0 20px 20px;
            }
            .feature-icon {
                font-size: 2.5rem;
                margin-bottom: 1rem;
            }
        </style>
    </head>
    <body>
        <!-- Hero Section -->
        <div class="hero-section">
            <div class="container">
                <div class="row align-items-center">
                    <div class="col-lg-6">
                        <h1 class="display-4 fw-bold">📚 Sistema de Livros</h1>
                        <p class="lead">Sua biblioteca pessoal online. Organize, acompanhe e descubra novos livros.</p>
                        <div class="mt-4">
                            <a href="/login" class="btn btn-light btn-lg me-3">🚀 Entrar</a>
                            <a href="/cadastro" class="btn btn-outline-light btn-lg">📝 Cadastrar</a>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Features Section -->
        <div class="container my-5">
            <div class="row text-center">
                <div class="col-md-4 mb-4">
                    <div class="feature-icon">📖</div>
                    <h3>Organize sua Biblioteca</h3>
                    <p>Cadastre todos os seus livros e mantenha sua coleção organizada</p>
                </div>
                <div class="col-md-4 mb-4">
                    <div class="feature-icon">📊</div>
                    <h3>Acompanhe seu Progresso</h3>
                    <p>Veja estatísticas e acompanhe seus hábitos de leitura</p>
                </div>
                <div class="col-md-4 mb-4">
                    <div class="feature-icon">⭐</div>
                    <h3>Avalie e Comente</h3>
                    <p>Dê notas e registre suas impressões sobre cada livro</p>
                </div>
            </div>
        </div>

        <footer class="bg-dark text-white text-center py-4 mt-5">
            <div class="container">
                <p>&copy; 2024 Sistema de Livros. Desenvolvido com ❤️ e Flask.</p>
            </div>
        </footer>
    </body>
    </html>
    '''

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Página de login"""
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, nome, email FROM usuarios WHERE email = ?", (email,))
        usuario = cursor.fetchone()
        conn.close()
        
        if usuario:
            session['usuario_id'] = usuario['id']
            session['usuario_nome'] = usuario['nome']
            session['usuario_email'] = usuario['email']
            return redirect('/dashboard')
        else:
            error_html = '''
            <div class="alert alert-danger alert-dismissible fade show" role="alert">
                ❌ Usuário não encontrado. Verifique o email ou <a href="/cadastro" class="alert-link">cadastre-se</a>.
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
            '''
            return render_login_page(error_html)
    
    return render_login_page()

def render_login_page(error_html=''):
    """Renderiza a página de login"""
    return f'''
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Login - Sistema de Livros</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body class="bg-light">
        <div class="container mt-5">
            <div class="row justify-content-center">
                <div class="col-md-5">
                    <div class="card shadow">
                        <div class="card-body p-4">
                            <div class="text-center mb-4">
                                <h1 class="h3">📚 Entrar</h1>
                                <p class="text-muted">Acesse sua biblioteca pessoal</p>
                            </div>
                            
                            {error_html}
                            
                            <form method="POST">
                                <div class="mb-3">
                                    <label for="email" class="form-label">📧 Email</label>
                                    <input type="email" class="form-control form-control-lg" id="email" name="email" 
                                           placeholder="seu@email.com" required>
                                </div>
                                <div class="mb-3">
                                    <label for="senha" class="form-label">🔒 Senha</label>
                                    <input type="password" class="form-control form-control-lg" id="senha" name="senha" 
                                           placeholder="Sua senha">
                                </div>
                                <button type="submit" class="btn btn-primary btn-lg w-100 py-2">
                                    🚀 Entrar na Biblioteca
                                </button>
                            </form>
                            
                            <div class="text-center mt-4">
                                <p class="mb-0">
                                    Não tem conta? <a href="/cadastro" class="text-decoration-none">Crie uma aqui</a>
                                </p>
                            </div>

                            <div class="mt-4 p-3 bg-light rounded">
                                <small class="text-muted">
                                    <strong>Usuário de teste:</strong><br>
                                    Email: <code>teste@teste.com</code><br>
                                    Senha: qualquer uma
                                </small>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    '''

@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    """Página de cadastro"""
    if request.method == 'POST':
        nome = request.form.get('nome', '').strip()
        email = request.form.get('email', '').strip()
        
        if not nome or not email:
            return render_cadastro_page('❌ Preencha todos os campos obrigatórios.')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "INSERT INTO usuarios (nome, email, senha) VALUES (?, ?, ?)", 
                (nome, email, '123')  # Senha simples para demonstração
            )
            usuario_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            session['usuario_id'] = usuario_id
            session['usuario_nome'] = nome
            session['usuario_email'] = email
            
            return redirect('/dashboard')
            
        except sqlite3.IntegrityError:
            conn.close()
            return render_cadastro_page('❌ Este email já está cadastrado. <a href="/login">Faça login aqui</a>.')
    
    return render_cadastro_page()

def render_cadastro_page(error_html=''):
    """Renderiza a página de cadastro"""
    return f'''
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Cadastro - Sistema de Livros</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body class="bg-light">
        <div class="container mt-5">
            <div class="row justify-content-center">
                <div class="col-md-5">
                    <div class="card shadow">
                        <div class="card-body p-4">
                            <div class="text-center mb-4">
                                <h1 class="h3">📝 Criar Conta</h1>
                                <p class="text-muted">Junte-se à nossa comunidade de leitores</p>
                            </div>
                            
                            {error_html}
                            
                            <form method="POST">
                                <div class="mb-3">
                                    <label for="nome" class="form-label">👤 Nome Completo</label>
                                    <input type="text" class="form-control form-control-lg" id="nome" name="nome" 
                                           placeholder="Seu nome" required>
                                </div>
                                <div class="mb-3">
                                    <label for="email" class="form-label">📧 Email</label>
                                    <input type="email" class="form-control form-control-lg" id="email" name="email" 
                                           placeholder="seu@email.com" required>
                                </div>
                                <div class="mb-3">
                                    <label for="senha" class="form-label">🔒 Senha</label>
                                    <input type="password" class="form-control form-control-lg" id="senha" name="senha" 
                                           placeholder="Crie uma senha">
                                </div>
                                <button type="submit" class="btn btn-success btn-lg w-100 py-2">
                                    ✅ Criar Minha Conta
                                </button>
                            </form>
                            
                            <div class="text-center mt-4">
                                <p class="mb-0">
                                    Já tem conta? <a href="/login" class="text-decoration-none">Entre aqui</a>
                                </p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    '''

@app.route('/dashboard')
def dashboard():
    """Dashboard principal"""
    if 'usuario_id' not in session:
        return redirect('/login')
    
    stats = get_user_books_count(session['usuario_id'])
    
    return f'''
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Dashboard - Sistema de Livros</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            .stat-card {{
                border: none;
                border-radius: 15px;
                transition: transform 0.2s;
            }}
            .stat-card:hover {{
                transform: translateY(-5px);
            }}
            .sidebar {{
                background: #2c3e50;
                min-height: 100vh;
            }}
            .sidebar .nav-link {{
                color: #ecf0f1;
                padding: 12px 20px;
                margin: 5px 0;
                border-radius: 8px;
            }}
            .sidebar .nav-link:hover {{
                background: #34495e;
                color: white;
            }}
            .sidebar .nav-link.active {{
                background: #3498db;
            }}
        </style>
    </head>
    <body>
        <div class="container-fluid">
            <div class="row">
                <!-- Sidebar -->
                <nav class="col-md-3 col-lg-2 d-md-block sidebar collapse bg-dark">
                    <div class="position-sticky pt-3">
                        <div class="text-center text-white mb-4">
                            <h5>👤 {session['usuario_nome']}</h5>
                            <small class="text-muted">{session['usuario_email']}</small>
                        </div>
                        
                        <ul class="nav flex-column">
                            <li class="nav-item">
                                <a class="nav-link active" href="/dashboard">
                                    📊 Dashboard
                                </a>
                            </li>
                            <li class="nav-item">
                                <a class="nav-link" href="/meus_livros">
                                    📚 Meus Livros
                                </a>
                            </li>
                            <li class="nav-item">
                                <a class="nav-link" href="/adicionar_livro">
                                    ➕ Adicionar Livro
                                </a>
                            </li>
                            <li class="nav-item mt-4">
                                <a class="nav-link text-warning" href="/logout">
                                    🚪 Sair
                                </a>
                            </li>
                        </ul>
                    </div>
                </nav>

                <!-- Main Content -->
                <main class="col-md-9 ms-sm-auto col-lg-10 px-md-4 py-4">
                    <div class="d-flex justify-content-between flex-wrap flex-md-nowrap align-items-center pt-3 pb-2 mb-3 border-bottom">
                        <h1 class="h2">📊 Dashboard</h1>
                        <div class="btn-toolbar mb-2 mb-md-0">
                            <a href="/adicionar_livro" class="btn btn-success">
                                ➕ Adicionar Livro
                            </a>
                        </div>
                    </div>

                    <!-- Stats Cards -->
                    <div class="row mb-4">
                        <div class="col-xl-4 col-md-6 mb-4">
                            <div class="card stat-card border-left-primary shadow h-100 py-2">
                                <div class="card-body">
                                    <div class="row no-gutters align-items-center">
                                        <div class="col mr-2">
                                            <div class="text-xs font-weight-bold text-primary text-uppercase mb-1">
                                                Total de Livros</div>
                                            <div class="h5 mb-0 font-weight-bold text-gray-800">{stats['total']}</div>
                                        </div>
                                        <div class="col-auto">
                                            <i class="fas fa-book fa-2x text-gray-300">📚</i>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div class="col-xl-4 col-md-6 mb-4">
                            <div class="card stat-card border-left-success shadow h-100 py-2">
                                <div class="card-body">
                                    <div class="row no-gutters align-items-center">
                                        <div class="col mr-2">
                                            <div class="text-xs font-weight-bold text-success text-uppercase mb-1">
                                                Livros Lidos</div>
                                            <div class="h5 mb-0 font-weight-bold text-gray-800">{stats['lidos']}</div>
                                        </div>
                                        <div class="col-auto">
                                            <i class="fas fa-check fa-2x text-gray-300">✅</i>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div class="col-xl-4 col-md-6 mb-4">
                            <div class="card stat-card border-left-warning shadow h-100 py-2">
                                <div class="card-body">
                                    <div class="row no-gutters align-items-center">
                                        <div class="col mr-2">
                                            <div class="text-xs font-weight-bold text-warning text-uppercase mb-1">
                                                Lendo Agora</div>
                                            <div class="h5 mb-0 font-weight-bold text-gray-800">{stats['lendo']}</div>
                                        </div>
                                        <div class="col-auto">
                                            <i class="fas fa-book-reader fa-2x text-gray-300">📖</i>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Welcome Card -->
                    <div class="row">
                        <div class="col-12">
                            <div class="card shadow">
                                <div class="card-body">
                                    <h5 class="card-title">🎉 Bem-vindo ao seu Sistema de Livros!</h5>
                                    <p class="card-text">
                                        Aqui você pode gerenciar sua biblioteca pessoal, acompanhar seu progresso de leitura 
                                        e descobrir novos livros incríveis.
                                    </p>
                                    <div class="mt-4">
                                        <a href="/adicionar_livro" class="btn btn-primary me-2">
                                            ➕ Adicionar Primeiro Livro
                                        </a>
                                        <a href="/meus_livros" class="btn btn-outline-secondary">
                                            📚 Ver Todos os Livros
                                        </a>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </main>
            </div>
        </div>

        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    '''

@app.route('/adicionar_livro', methods=['GET', 'POST'])
def adicionar_livro():
    """Página para adicionar novo livro"""
    if 'usuario_id' not in session:
        return redirect('/login')
    
    if request.method == 'POST':
        titulo = request.form.get('titulo', '').strip()
        autor = request.form.get('autor', '').strip()
        genero = request.form.get('genero', '').strip()
        status = request.form.get('status', 'quero_ler')
        
        if not titulo or not autor:
            return render_add_book_page('❌ Título e autor são obrigatórios.')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            """INSERT INTO livros (titulo, autor, genero, status, usuario_id) 
               VALUES (?, ?, ?, ?, ?)""",
            (titulo, autor, genero, status, session['usuario_id'])
        )
        conn.commit()
        conn.close()
        
        return redirect('/meus_livros')
    
    return render_add_book_page()

def render_add_book_page(error_html=''):
    """Renderiza a página de adicionar livro"""
    return f'''
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Adicionar Livro - Sistema de Livros</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body>
        <div class="container-fluid">
            <div class="row">
                <!-- Sidebar -->
                <nav class="col-md-3 col-lg-2 d-md-block sidebar collapse bg-dark">
                    <div class="position-sticky pt-3">
                        <div class="text-center text-white mb-4">
                            <h5>👤 {session['usuario_nome']}</h5>
                        </div>
                        
                        <ul class="nav flex-column">
                            <li class="nav-item">
                                <a class="nav-link" href="/dashboard">
                                    📊 Dashboard
                                </a>
                            </li>
                            <li class="nav-item">
                                <a class="nav-link" href="/meus_livros">
                                    📚 Meus Livros
                                </a>
                            </li>
                            <li class="nav-item">
                                <a class="nav-link active" href="/adicionar_livro">
                                    ➕ Adicionar Livro
                                </a>
                            </li>
                            <li class="nav-item mt-4">
                                <a class="nav-link text-warning" href="/logout">
                                    🚪 Sair
                                </a>
                            </li>
                        </ul>
                    </div>
                </nav>

                <!-- Main Content -->
                <main class="col-md-9 ms-sm-auto col-lg-10 px-md-4 py-4">
                    <div class="d-flex justify-content-between flex-wrap flex-md-nowrap align-items-center pt-3 pb-2 mb-3 border-bottom">
                        <h1 class="h2">➕ Adicionar Novo Livro</h1>
                        <div class="btn-toolbar mb-2 mb-md-0">
                            <a href="/meus_livros" class="btn btn-secondary">
                                ↩️ Voltar
                            </a>
                        </div>
                    </div>

                    {error_html}

                    <div class="row">
                        <div class="col-lg-8">
                            <div class="card shadow">
                                <div class="card-body">
                                    <form method="POST">
                                        <div class="row">
                                            <div class="col-md-6 mb-3">
                                                <label for="titulo" class="form-label">📖 Título do Livro *</label>
                                                <input type="text" class="form-control" id="titulo" name="titulo" 
                                                       placeholder="Ex: O Pequeno Príncipe" required>
                                            </div>
                                            <div class="col-md-6 mb-3">
                                                <label for="autor" class="form-label">✍️ Autor *</label>
                                                <input type="text" class="form-control" id="autor" name="autor" 
                                                       placeholder="Ex: Antoine de Saint-Exupéry" required>
                                            </div>
                                        </div>
                                        
                                        <div class="row">
                                            <div class="col-md-6 mb-3">
                                                <label for="genero" class="form-label">📚 Gênero</label>
                                                <input type="text" class="form-control" id="genero" name="genero" 
                                                       placeholder="Ex: Ficção, Romance, etc.">
                                            </div>
                                            <div class="col-md-6 mb-3">
                                                <label for="status" class="form-label">📈 Status</label>
                                                <select class="form-select" id="status" name="status">
                                                    <option value="quero_ler">📥 Quero Ler</option>
                                                    <option value="lendo">📖 Lendo</option>
                                                    <option value="lido">✅ Lido</option>
                                                </select>
                                            </div>
                                        </div>
                                        
                                        <div class="mt-4">
                                            <button type="submit" class="btn btn-success btn-lg">
                                                💾 Salvar Livro
                                            </button>
                                            <a href="/meus_livros" class="btn btn-secondary btn-lg">
                                                ❌ Cancelar
                                            </a>
                                        </div>
                                    </form>
                                </div>
                            </div>
                        </div>
                        
                        <div class="col-lg-4">
                            <div class="card shadow">
                                <div class="card-body">
                                    <h6>💡 Dicas</h6>
                                    <ul class="small text-muted">
                                        <li>Preencha pelo menos título e autor</li>
                                        <li>Use o status para acompanhar seu progresso</li>
                                        <li>Você pode editar as informações depois</li>
                                    </ul>
                                </div>
                            </div>
                        </div>
                    </div>
                </main>
            </div>
        </div>

        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    '''

@app.route('/meus_livros')
def meus_livros():
    """Página com lista de todos os livros do usuário"""
    if 'usuario_id' not in session:
        return redirect('/login')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, titulo, autor, genero, status, data_criacao 
        FROM livros 
        WHERE usuario_id = ? 
        ORDER BY data_criacao DESC
    ''', (session['usuario_id'],))
    livros = cursor.fetchall()
    conn.close()
    
    livros_html = ''
    for livro in livros:
        status_icon = {
            'quero_ler': '📥',
            'lendo': '📖', 
            'lido': '✅'
        }.get(livro['status'], '📚')
        
        status_text = {
            'quero_ler': 'Quero Ler',
            'lendo': 'Lendo',
            'lido': 'Lido'
        }.get(livro['status'], 'Desconhecido')
        
        livros_html += f'''
        <div class="col-md-6 col-lg-4 mb-4">
            <div class="card h-100 shadow-sm">
                <div class="card-body">
                    <h5 class="card-title">{livro['titulo']}</h5>
                    <h6 class="card-subtitle mb-2 text-muted">por {livro['autor']}</h6>
                    <p class="card-text">
                        <span class="badge bg-secondary">{livro['genero'] or 'Sem gênero'}</span>
                    </p>
                </div>
                <div class="card-footer">
                    <small class="text-muted">
                        {status_icon} {status_text}
                    </small>
                </div>
            </div>
        </div>
        '''
    
    return f'''
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Meus Livros - Sistema de Livros</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body>
        <div class="container-fluid">
            <div class="row">
                <!-- Sidebar -->
                <nav class="col-md-3 col-lg-2 d-md-block sidebar collapse bg-dark">
                    <div class="position-sticky pt-3">
                        <div class="text-center text-white mb-4">
                            <h5>👤 {session['usuario_nome']}</h5>
                        </div>
                        
                        <ul class="nav flex-column">
                            <li class="nav-item">
                                <a class="nav-link" href="/dashboard">
                                    📊 Dashboard
                                </a>
                            </li>
                            <li class="nav-item">
                                <a class="nav-link active" href="/meus_livros">
                                    📚 Meus Livros
                                </a>
                            </li>
                            <li class="nav-item">
                                <a class="nav-link" href="/adicionar_livro">
                                    ➕ Adicionar Livro
                                </a>
                            </li>
                            <li class="nav-item mt-4">
                                <a class="nav-link text-warning" href="/logout">
                                    🚪 Sair
                                </a>
                            </li>
                        </ul>
                    </div>
                </nav>

                <!-- Main Content -->
                <main class="col-md-9 ms-sm-auto col-lg-10 px-md-4 py-4">
                    <div class="d-flex justify-content-between flex-wrap flex-md-nowrap align-items-center pt-3 pb-2 mb-3 border-bottom">
                        <h1 class="h2">📚 Minha Biblioteca</h1>
                        <div class="btn-toolbar mb-2 mb-md-0">
                            <a href="/adicionar_livro" class="btn btn-success">
                                ➕ Adicionar Livro
                            </a>
                        </div>
                    </div>

                    <div class="row">
                        {livros_html if livros else '''
                        <div class="col-12">
                            <div class="card shadow text-center py-5">
                                <div class="card-body">
                                    <h3 class="text-muted">📚</h3>
                                    <h4 class="text-muted">Sua biblioteca está vazia</h4>
                                    <p class="text-muted">Comece adicionando seu primeiro livro à coleção!</p>
                                    <a href="/adicionar_livro" class="btn btn-primary btn-lg mt-3">
                                        ➕ Adicionar Primeiro Livro
                                    </a>
                                </div>
                            </div>
                        </div>
                        '''}
                    </div>
                </main>
            </div>
        </div>

        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    '''

@app.route('/logout')
def logout():
    """Faz logout do usuário"""
    session.clear()
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Logout - Sistema de Livros</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body class="bg-light">
        <div class="container mt-5">
            <div class="row justify-content-center">
                <div class="col-md-6 text-center">
                    <div class="card shadow">
                        <div class="card-body py-5">
                            <h1 class="text-success">✅</h1>
                            <h3>Logout realizado com sucesso!</h3>
                            <p class="text-muted">Você saiu do sistema de livros.</p>
                            <div class="mt-4">
                                <a href="/" class="btn btn-primary">🏠 Página Inicial</a>
                                <a href="/login" class="btn btn-outline-primary">🔐 Fazer Login Novamente</a>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    '''

# =============================================
# INICIALIZAÇÃO
# =============================================

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    print(f"🚀 Servidor iniciado na porta {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
