# -*- coding: utf-8 -*-
"""
⚔️ GRIMÓRIO BERSERK - SISTEMA DE ANOTAÇÕES DE PERSONAGENS
Versão Premium - Design Moderno com Interface Aprimorada
Tema Dark-Fantasy estilo Berserk refinado
"""

import os
from flask import Flask, render_template_string, request, redirect, url_for, flash, session, jsonify, get_flashed_messages
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import secrets
import json


# =============================================
# CONFIGURAÇÃO DA APLICAÇÃO
# =============================================

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', secrets.token_hex(16))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///grimorio_berserk_premium.db'
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
    avatar = db.Column(db.String(200), default='default')
    tema = db.Column(db.String(20), default='dark')
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    personagens = db.relationship('Personagem', backref='usuario', lazy=True, cascade='all, delete-orphan')


class Personagem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(200), nullable=False)
    tipo = db.Column(db.String(100), default='Personagem')
    descricao = db.Column(db.Text)
    prioridade = db.Column(db.Integer, default=5)
    
    historia = db.Column(db.Text)
    habilidades = db.Column(db.Text)
    notas = db.Column(db.Text)
    imagem_url = db.Column(db.String(500))
    
    objetivos = db.relationship('Objetivo', backref='personagem', lazy=True, cascade='all, delete-orphan')
    
    tags = db.Column(db.String(300))
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    data_atualizacao = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Objetivo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    descricao = db.Column(db.String(500), nullable=False)
    concluido = db.Column(db.Boolean, default=False)
    prioridade = db.Column(db.Integer, default=5)
    personagem_id = db.Column(db.Integer, db.ForeignKey('personagem.id'), nullable=False)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    data_conclusao = db.Column(db.DateTime)


class NotaRapida(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(200), nullable=False)
    conteudo = db.Column(db.Text)
    cor = db.Column(db.String(20), default='#8B0000')
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    data_atualizacao = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# =============================================
# FUNÇÕES AUXILIARES
# =============================================

def get_flashed_messages_html():
    messages_html = []
    for category, message in get_flashed_messages(with_categories=True):
        icon = {
            'success': 'check-circle',
            'error': 'exclamation-circle',
            'warning': 'exclamation-triangle',
            'info': 'info-circle'
        }.get(category, 'info-circle')
        
        messages_html.append(f'''
            <div class="alert alert-{category}">
                <i class="fas fa-{icon} me-2"></i>
                {message}
                <button class="alert-close">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        ''')
    
    return ''.join(messages_html)


def calcular_estatisticas(usuario_id):
    personagens = Personagem.query.filter_by(usuario_id=usuario_id).all()
    total_personagens = len(personagens)
    
    total_objetivos = 0
    objetivos_ativos = 0
    total_prioridade = 0
    objetivos_concluidos = 0
    
    for personagem in personagens:
        total_objetivos += len(personagem.objetivos)
        total_prioridade += personagem.prioridade
        
        for objetivo in personagem.objetivos:
            if objetivo.concluido:
                objetivos_concluidos += 1
            else:
                objetivos_ativos += 1
    
    prioridade_media = total_prioridade / total_personagens if total_personagens > 0 else 0
    
    objetivos_atrasados = 0
    data_limite = datetime.utcnow() - timedelta(days=7)
    
    for personagem in personagens:
        for objetivo in personagem.objetivos:
            if not objetivo.concluido and objetivo.data_criacao < data_limite:
                objetivos_atrasados += 1
    
    return {
        'total_personagens': total_personagens,
        'total_objetivos': total_objetivos,
        'objetivos_ativos': objetivos_ativos,
        'objetivos_concluidos': objetivos_concluidos,
        'objetivos_atrasados': objetivos_atrasados,
        'prioridade_media': round(prioridade_media, 1)
    }


def criar_menu_lateral(usuario_id, active_page='dashboard'):
    estatisticas = calcular_estatisticas(usuario_id)
    
    personagens_recentes = Personagem.query.filter_by(usuario_id=usuario_id)\
        .order_by(Personagem.data_atualizacao.desc()).limit(5).all()
    
    objetivos_pendentes = []
    for personagem in Personagem.query.filter_by(usuario_id=usuario_id).all():
        for objetivo in personagem.objetivos:
            if not objetivo.concluido:
                objetivos_pendentes.append((objetivo, personagem))
                if len(objetivos_pendentes) >= 5:
                    break
        if len(objetivos_pendentes) >= 5:
            break
    
    notas_rapidas = NotaRapida.query.filter_by(usuario_id=usuario_id)\
        .order_by(NotaRapida.data_atualizacao.desc()).limit(3).all()
    
    menu_html = f'''
    <aside class="sidebar">
        <div class="sidebar-header">
            <div class="sidebar-logo">
                <i class="fas fa-skull-crossbones"></i>
                <span>Painel Rápido</span>
            </div>
            <button class="sidebar-close" onclick="toggleSidebar()">
                <i class="fas fa-times"></i>
            </button>
        </div>
        
        <div class="sidebar-content">
            <div class="sidebar-section">
                <div class="stats-grid">
                    <div class="stat-card mini">
                        <div class="stat-value">{estatisticas['total_personagens']}</div>
                        <div class="stat-label">Personagens</div>
                    </div>
                    <div class="stat-card mini">
                        <div class="stat-value">{estatisticas['objetivos_ativos']}</div>
                        <div class="stat-label">Ativos</div>
                    </div>
                    <div class="stat-card mini">
                        <div class="stat-value">{estatisticas['objetivos_concluidos']}</div>
                        <div class="stat-label">Concluídos</div>
                    </div>
                    <div class="stat-card mini">
                        <div class="stat-value">{estatisticas['objetivos_atrasados']}</div>
                        <div class="stat-label">Atrasados</div>
                    </div>
                </div>
            </div>
            
            <div class="sidebar-section">
                <h6 class="section-title">
                    <i class="fas fa-bolt"></i>
                    Ações Rápidas
                </h6>
                <div class="quick-actions">
                    <a href="/novo_personagem" class="quick-action">
                        <div class="action-icon">
                            <i class="fas fa-user-plus"></i>
                        </div>
                        <span>Novo Personagem</span>
                    </a>
                    <a href="#" class="quick-action" onclick="novaNotaRapida(); return false;">
                        <div class="action-icon">
                            <i class="fas fa-sticky-note"></i>
                        </div>
                        <span>Nova Nota</span>
                    </a>
                    <a href="/buscar" class="quick-action">
                        <div class="action-icon">
                            <i class="fas fa-search"></i>
                        </div>
                        <span>Buscar</span>
                    </a>
                    <a href="/relatorio/personagens" class="quick-action">
                        <div class="action-icon">
                            <i class="fas fa-chart-pie"></i>
                        </div>
                        <span>Relatórios</span>
                    </a>
                </div>
            </div>
            
            <div class="sidebar-section">
                <h6 class="section-title">
                    <i class="fas fa-history"></i>
                    Recentes
                </h6>
                <div class="recent-list">
                    {''.join([f'''
                    <a href="/detalhes_personagem/{p.id}" class="recent-item">
                        <div class="recent-avatar">
                            <i class="fas fa-user-circle"></i>
                        </div>
                        <div class="recent-info">
                            <span class="recent-title">{p.nome[:20]}{'...' if len(p.nome) > 20 else ''}</span>
                            <span class="recent-subtitle">{p.tipo} • Pri: {p.prioridade}/10</span>
                        </div>
                        <div class="recent-time">
                            <i class="fas fa-clock"></i>
                        </div>
                    </a>''' for p in personagens_recentes]) or '''
                    <div class="empty-state">
                        <i class="fas fa-users-slash"></i>
                        <span>Nenhum personagem</span>
                    </div>'''}
                </div>
            </div>
            
            <div class="sidebar-section">
                <h6 class="section-title">
                    <i class="fas fa-flag"></i>
                    Objetivos Pendentes
                </h6>
                <div class="objectives-list">
                    {''.join([f'''
                    <div class="objective-item {'completed' if obj[0].concluido else ''}">
                        <div class="objective-check" onclick="toggleObjetivoSidebar({obj[0].id})">
                            <i class="fas {'fa-check' if obj[0].concluido else 'fa-circle'}"></i>
                        </div>
                        <div class="objective-content">
                            <span class="objective-text">{obj[0].descricao[:30]}{'...' if len(obj[0].descricao) > 30 else ''}</span>
                            <span class="objective-character">{obj[1].nome[:15]}</span>
                        </div>
                    </div>''' for obj in objetivos_pendentes]) or '''
                    <div class="empty-state">
                        <i class="fas fa-flag"></i>
                        <span>Nenhum objetivo</span>
                    </div>'''}
                </div>
            </div>
            
            <div class="sidebar-section">
                <h6 class="section-title">
                    <i class="fas fa-sticky-note"></i>
                    Notas Rápidas
                </h6>
                <div class="notes-list">
                    {''.join([f'''
                    <div class="note-item" style="border-color: {nota.cor}">
                        <div class="note-header">
                            <div class="note-title">{nota.titulo[:25]}{'...' if len(nota.titulo) > 25 else ''}</div>
                            <div class="note-actions">
                                <button class="note-action" onclick="editarNota({nota.id})">
                                    <i class="fas fa-edit"></i>
                                </button>
                                <button class="note-action" onclick="excluirNota({nota.id})">
                                    <i class="fas fa-trash"></i>
                                </button>
                            </div>
                        </div>
                        <div class="note-content">{nota.conteudo[:50]}{'...' if len(nota.conteudo) > 50 else ''}</div>
                        <div class="note-time">
                            <i class="fas fa-clock"></i>
                            {nota.data_criacao.strftime('%d/%m')}
                        </div>
                    </div>''' for nota in notas_rapidas]) or '''
                    <div class="empty-state">
                        <i class="fas fa-sticky-note"></i>
                        <span>Nenhuma nota</span>
                    </div>'''}
                </div>
                <button class="btn-add-note" onclick="novaNotaRapida()">
                    <i class="fas fa-plus"></i>
                    Nova Nota
                </button>
            </div>
            
            <div class="sidebar-footer">
                <div class="theme-toggle">
                    <span>Modo Escuro</span>
                    <label class="switch">
                        <input type="checkbox" id="darkModeToggle" checked onchange="toggleDarkMode()">
                        <span class="slider"></span>
                    </label>
                </div>
                <div class="sidebar-tags">
                    <span class="sidebar-tag" onclick="window.location='/personagens?tipo=Personagem'">Heróis</span>
                    <span class="sidebar-tag" onclick="window.location='/personagens?tipo=Vilão'">Vilões</span>
                    <span class="sidebar-tag" onclick="window.location='/personagens?prioridade_min=8'">Alta Pri</span>
                </div>
            </div>
        </div>
    </aside>
    
    <button class="sidebar-toggle" onclick="toggleSidebar()">
        <i class="fas fa-bars"></i>
    </button>
    '''
    
    return menu_html


def create_navbar(active_page='dashboard'):
    usuario_nome = session.get('usuario_nome', 'Criador')
    
    navbar = f'''
    <nav class="navbar">
        <div class="navbar-container">
            <div class="navbar-brand">
                <div class="brand-logo">
                    <i class="fas fa-skull-crossbones"></i>
                </div>
                <div class="brand-text">
                    <h1>GRIMÓRIO BERSERK</h1>
                    <p class="brand-subtitle">Sistema de Personagens</p>
                </div>
            </div>
            
            <button class="navbar-toggler" onclick="toggleNavbar()">
                <i class="fas fa-bars"></i>
            </button>
            
            <div class="navbar-menu" id="navbarMenu">
                <div class="nav-items">
                    <a href="/dashboard" class="nav-item {'active' if active_page == 'dashboard' else ''}">
                        <i class="fas fa-eye"></i>
                        <span>Dashboard</span>
                    </a>
                    <a href="/personagens" class="nav-item {'active' if active_page == 'personagens' else ''}">
                        <i class="fas fa-users"></i>
                        <span>Personagens</span>
                    </a>
                    <a href="/novo_personagem" class="nav-item {'active' if active_page == 'novo_personagem' else ''}">
                        <i class="fas fa-user-plus"></i>
                        <span>Novo</span>
                    </a>
                    <a href="/buscar" class="nav-item {'active' if active_page == 'buscar' else ''}">
                        <i class="fas fa-search"></i>
                        <span>Buscar</span>
                    </a>
                    <div class="nav-item dropdown">
                        <a href="#" class="nav-item">
                            <i class="fas fa-chart-bar"></i>
                            <span>Relatórios</span>
                            <i class="fas fa-chevron-down dropdown-arrow"></i>
                        </a>
                        <div class="dropdown-menu">
                            <a href="/relatorio/personagens" class="dropdown-item">
                                <i class="fas fa-users"></i>
                                Personagens
                            </a>
                            <a href="/relatorio/objetivos" class="dropdown-item">
                                <i class="fas fa-bullseye"></i>
                                Objetivos
                            </a>
                            <a href="/relatorio/estatisticas" class="dropdown-item">
                                <i class="fas fa-chart-line"></i>
                                Estatísticas
                            </a>
                        </div>
                    </div>
                </div>
                
                <div class="navbar-user">
                    <div class="user-dropdown">
                        <button class="user-profile">
                            <div class="user-avatar">
                                <i class="fas fa-user-circle"></i>
                            </div>
                            <span class="user-name">{usuario_nome}</span>
                            <i class="fas fa-chevron-down"></i>
                        </button>
                        <div class="user-menu">
                            <a href="/configuracoes" class="user-menu-item">
                                <i class="fas fa-cog"></i>
                                Configurações
                            </a>
                            <a href="/logout" class="user-menu-item">
                                <i class="fas fa-sign-out-alt"></i>
                                Sair
                            </a>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </nav>
    '''
    return navbar


# =============================================
# TEMPLATES HTML - DESIGN MODERNO
# =============================================

BASE_TEMPLATE = '''<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Grimório Berserk - Sistema de Personagens</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Cinzel:wght@400;600;700&family=Inter:wght@300;400;500;600&display=swap" rel="stylesheet">
    <style>
        :root {
            /* Cores principais */
            --primary-dark: #0a0a0a;
            --primary-darker: #050505;
            --secondary-dark: #141414;
            --tertiary-dark: #1a1a1a;
            
            /* Cores de destaque */
            --blood-red: #8B0000;
            --blood-dark: #5A0000;
            --blood-light: #B22222;
            --blood-glow: rgba(139, 0, 0, 0.3);
            
            /* Cores de texto */
            --text-primary: #f5f1e8;
            --text-secondary: #b8b5a8;
            --text-muted: #8a877c;
            
            /* Cores de elementos UI */
            --border-color: #2a2a2a;
            --border-light: #3a3a3a;
            --shadow-color: rgba(0, 0, 0, 0.5);
            --overlay: rgba(0, 0, 0, 0.8);
            
            /* Gradientes */
            --gradient-dark: linear-gradient(135deg, var(--primary-dark) 0%, var(--secondary-dark) 100%);
            --gradient-blood: linear-gradient(135deg, var(--blood-red) 0%, var(--blood-dark) 100%);
            
            /* Espaçamentos */
            --spacing-xs: 8px;
            --spacing-sm: 12px;
            --spacing-md: 16px;
            --spacing-lg: 24px;
            --spacing-xl: 32px;
            --spacing-xxl: 48px;
            
            /* Bordas */
            --radius-sm: 4px;
            --radius-md: 8px;
            --radius-lg: 12px;
            --radius-xl: 16px;
            --radius-full: 9999px;
            
            /* Transições */
            --transition-fast: 0.15s ease;
            --transition-normal: 0.3s ease;
            --transition-slow: 0.5s ease;
            
            /* Sombras */
            --shadow-sm: 0 2px 8px var(--shadow-color);
            --shadow-md: 0 4px 16px var(--shadow-color);
            --shadow-lg: 0 8px 32px var(--shadow-color);
            --shadow-inner: inset 0 2px 4px rgba(0, 0, 0, 0.5);
            --shadow-glow: 0 0 20px var(--blood-glow);
        }
        
        /* Reset e estilos base */
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Inter', sans-serif;
            background: var(--primary-dark);
            color: var(--text-primary);
            min-height: 100vh;
            overflow-x: hidden;
            line-height: 1.6;
        }
        
        .berserk-font {
            font-family: 'Cinzel', serif;
        }
        
        .container-main {
            padding: var(--spacing-md);
            max-width: 1400px;
            margin: 0 auto;
            position: relative;
        }
        
        /* ========== TYPOGRAPHY ========== */
        h1, h2, h3, h4, h5, h6 {
            font-family: 'Cinzel', serif;
            font-weight: 700;
            color: var(--text-primary);
            margin-bottom: var(--spacing-md);
        }
        
        h1 { font-size: 2.5rem; }
        h2 { font-size: 2rem; }
        h3 { font-size: 1.5rem; }
        h4 { font-size: 1.25rem; }
        h5 { font-size: 1.125rem; }
        h6 { font-size: 1rem; }
        
        .text-blood { color: var(--blood-red) !important; }
        .text-muted { color: var(--text-muted) !important; }
        .text-gradient {
            background: var(--gradient-blood);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        
        /* ========== NAVBAR ========== */
        .navbar {
            background: var(--secondary-dark);
            border-bottom: 1px solid var(--border-color);
            padding: 0 var(--spacing-lg);
            position: sticky;
            top: 0;
            z-index: 1000;
            backdrop-filter: blur(10px);
        }
        
        .navbar-container {
            display: flex;
            align-items: center;
            justify-content: space-between;
            height: 70px;
        }
        
        .navbar-brand {
            display: flex;
            align-items: center;
            gap: var(--spacing-md);
        }
        
        .brand-logo {
            width: 40px;
            height: 40px;
            background: var(--gradient-blood);
            border-radius: var(--radius-md);
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 1.5rem;
        }
        
        .brand-text h1 {
            font-size: 1.5rem;
            margin: 0;
            line-height: 1;
            color: var(--blood-red);
        }
        
        .brand-subtitle {
            font-size: 0.75rem;
            color: var(--text-muted);
            margin: 0;
        }
        
        .navbar-toggler {
            display: none;
            background: none;
            border: none;
            color: var(--text-primary);
            font-size: 1.25rem;
            cursor: pointer;
            padding: var(--spacing-sm);
        }
        
        .navbar-menu {
            display: flex;
            align-items: center;
            gap: var(--spacing-lg);
        }
        
        .nav-items {
            display: flex;
            gap: var(--spacing-sm);
        }
        
        .nav-item {
            display: flex;
            align-items: center;
            gap: var(--spacing-sm);
            padding: var(--spacing-sm) var(--spacing-md);
            color: var(--text-secondary);
            text-decoration: none;
            border-radius: var(--radius-md);
            transition: all var(--transition-fast);
            position: relative;
        }
        
        .nav-item:hover {
            background: var(--tertiary-dark);
            color: var(--text-primary);
        }
        
        .nav-item.active {
            background: var(--gradient-blood);
            color: white;
            box-shadow: var(--shadow-glow);
        }
        
        .nav-item i {
            font-size: 1.1rem;
        }
        
        .dropdown {
            position: relative;
        }
        
        .dropdown-menu {
            position: absolute;
            top: 100%;
            left: 0;
            background: var(--secondary-dark);
            border: 1px solid var(--border-color);
            border-radius: var(--radius-md);
            padding: var(--spacing-sm);
            min-width: 200px;
            display: none;
            box-shadow: var(--shadow-lg);
            z-index: 1001;
        }
        
        .dropdown:hover .dropdown-menu {
            display: block;
        }
        
        .dropdown-item {
            display: flex;
            align-items: center;
            gap: var(--spacing-sm);
            padding: var(--spacing-sm) var(--spacing-md);
            color: var(--text-secondary);
            text-decoration: none;
            border-radius: var(--radius-sm);
            transition: all var(--transition-fast);
        }
        
        .dropdown-item:hover {
            background: var(--tertiary-dark);
            color: var(--text-primary);
        }
        
        .navbar-user {
            position: relative;
        }
        
        .user-profile {
            display: flex;
            align-items: center;
            gap: var(--spacing-sm);
            background: none;
            border: none;
            color: var(--text-primary);
            padding: var(--spacing-sm);
            border-radius: var(--radius-md);
            cursor: pointer;
            transition: all var(--transition-fast);
        }
        
        .user-profile:hover {
            background: var(--tertiary-dark);
        }
        
        .user-avatar {
            width: 36px;
            height: 36px;
            background: var(--tertiary-dark);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .user-menu {
            position: absolute;
            top: 100%;
            right: 0;
            background: var(--secondary-dark);
            border: 1px solid var(--border-color);
            border-radius: var(--radius-md);
            padding: var(--spacing-sm);
            min-width: 200px;
            display: none;
            box-shadow: var(--shadow-lg);
        }
        
        .user-dropdown:hover .user-menu {
            display: block;
        }
        
        .user-menu-item {
            display: flex;
            align-items: center;
            gap: var(--spacing-sm);
            padding: var(--spacing-sm) var(--spacing-md);
            color: var(--text-secondary);
            text-decoration: none;
            border-radius: var(--radius-sm);
            transition: all var(--transition-fast);
        }
        
        .user-menu-item:hover {
            background: var(--tertiary-dark);
            color: var(--text-primary);
        }
        
        /* ========== SIDEBAR ========== */
        .sidebar {
            position: fixed;
            top: 70px;
            right: 0;
            width: 320px;
            height: calc(100vh - 70px);
            background: var(--secondary-dark);
            border-left: 1px solid var(--border-color);
            padding: var(--spacing-lg);
            overflow-y: auto;
            transform: translateX(100%);
            transition: transform var(--transition-normal);
            z-index: 999;
        }
        
        .sidebar.active {
            transform: translateX(0);
        }
        
        .sidebar-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: var(--spacing-lg);
            padding-bottom: var(--spacing-md);
            border-bottom: 1px solid var(--border-color);
        }
        
        .sidebar-logo {
            display: flex;
            align-items: center;
            gap: var(--spacing-sm);
            color: var(--blood-red);
            font-weight: 600;
        }
        
        .sidebar-close {
            background: none;
            border: none;
            color: var(--text-muted);
            cursor: pointer;
            padding: var(--spacing-sm);
        }
        
        .sidebar-close:hover {
            color: var(--text-primary);
        }
        
        .sidebar-toggle {
            position: fixed;
            bottom: var(--spacing-lg);
            right: var(--spacing-lg);
            width: 56px;
            height: 56px;
            background: var(--gradient-blood);
            border: none;
            border-radius: 50%;
            color: white;
            font-size: 1.5rem;
            cursor: pointer;
            display: none;
            align-items: center;
            justify-content: center;
            box-shadow: var(--shadow-lg);
            z-index: 998;
            transition: all var(--transition-normal);
        }
        
        .sidebar-toggle:hover {
            transform: scale(1.1);
        }
        
        .sidebar-section {
            margin-bottom: var(--spacing-xl);
        }
        
        .section-title {
            display: flex;
            align-items: center;
            gap: var(--spacing-sm);
            color: var(--text-primary);
            font-size: 0.875rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: var(--spacing-md);
        }
        
        .section-title i {
            color: var(--blood-red);
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: var(--spacing-sm);
        }
        
        .stat-card.mini {
            background: var(--tertiary-dark);
            padding: var(--spacing-md);
            border-radius: var(--radius-md);
            text-align: center;
            border: 1px solid var(--border-color);
            transition: all var(--transition-fast);
        }
        
        .stat-card.mini:hover {
            border-color: var(--blood-red);
            transform: translateY(-2px);
        }
        
        .stat-card.mini .stat-value {
            font-size: 1.5rem;
            font-weight: bold;
            color: var(--blood-red);
            line-height: 1;
        }
        
        .stat-card.mini .stat-label {
            font-size: 0.75rem;
            color: var(--text-muted);
            margin-top: var(--spacing-xs);
        }
        
        .quick-actions {
            display: flex;
            flex-direction: column;
            gap: var(--spacing-sm);
        }
        
        .quick-action {
            display: flex;
            align-items: center;
            gap: var(--spacing-sm);
            padding: var(--spacing-sm);
            background: var(--tertiary-dark);
            border: 1px solid var(--border-color);
            border-radius: var(--radius-md);
            color: var(--text-secondary);
            text-decoration: none;
            transition: all var(--transition-fast);
        }
        
        .quick-action:hover {
            background: var(--gradient-blood);
            color: white;
            border-color: var(--blood-red);
            transform: translateX(4px);
        }
        
        .action-icon {
            width: 36px;
            height: 36px;
            background: var(--secondary-dark);
            border-radius: var(--radius-sm);
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .recent-list, .objectives-list, .notes-list {
            display: flex;
            flex-direction: column;
            gap: var(--spacing-sm);
        }
        
        .recent-item, .objective-item, .note-item {
            display: flex;
            align-items: center;
            gap: var(--spacing-sm);
            padding: var(--spacing-sm);
            background: var(--tertiary-dark);
            border: 1px solid var(--border-color);
            border-radius: var(--radius-md);
            transition: all var(--transition-fast);
        }
        
        .recent-item {
            text-decoration: none;
            color: var(--text-secondary);
        }
        
        .recent-item:hover {
            background: var(--secondary-dark);
            border-color: var(--blood-red);
        }
        
        .recent-avatar {
            width: 40px;
            height: 40px;
            background: var(--secondary-dark);
            border-radius: var(--radius-md);
            display: flex;
            align-items: center;
            justify-content: center;
            color: var(--blood-red);
            font-size: 1.25rem;
        }
        
        .recent-info {
            flex: 1;
        }
        
        .recent-title {
            display: block;
            font-weight: 500;
            color: var(--text-primary);
        }
        
        .recent-subtitle {
            display: block;
            font-size: 0.75rem;
            color: var(--text-muted);
        }
        
        .recent-time {
            color: var(--text-muted);
            font-size: 0.75rem;
        }
        
        .objective-item {
            cursor: pointer;
        }
        
        .objective-item.completed {
            opacity: 0.7;
        }
        
        .objective-check {
            width: 24px;
            height: 24px;
            background: var(--secondary-dark);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            color: var(--blood-red);
        }
        
        .objective-item.completed .objective-check {
            color: #28a745;
        }
        
        .objective-content {
            flex: 1;
        }
        
        .objective-text {
            display: block;
            color: var(--text-primary);
            font-size: 0.875rem;
        }
        
        .objective-character {
            display: block;
            font-size: 0.75rem;
            color: var(--text-muted);
        }
        
        .note-item {
            flex-direction: column;
            align-items: stretch;
            border-left: 4px solid var(--blood-red);
        }
        
        .note-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: var(--spacing-xs);
        }
        
        .note-title {
            font-weight: 500;
            color: var(--text-primary);
        }
        
        .note-actions {
            display: flex;
            gap: var(--spacing-xs);
        }
        
        .note-action {
            background: none;
            border: none;
            color: var(--text-muted);
            cursor: pointer;
            padding: 2px;
        }
        
        .note-action:hover {
            color: var(--text-primary);
        }
        
        .note-content {
            font-size: 0.875rem;
            color: var(--text-secondary);
            margin-bottom: var(--spacing-xs);
        }
        
        .note-time {
            font-size: 0.75rem;
            color: var(--text-muted);
            display: flex;
            align-items: center;
            gap: 4px;
        }
        
        .btn-add-note {
            width: 100%;
            padding: var(--spacing-sm);
            background: var(--tertiary-dark);
            border: 1px dashed var(--border-color);
            border-radius: var(--radius-md);
            color: var(--text-muted);
            cursor: pointer;
            transition: all var(--transition-fast);
        }
        
        .btn-add-note:hover {
            background: var(--secondary-dark);
            border-color: var(--blood-red);
            color: var(--text-primary);
        }
        
        .sidebar-footer {
            margin-top: auto;
            padding-top: var(--spacing-lg);
            border-top: 1px solid var(--border-color);
        }
        
        .theme-toggle {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: var(--spacing-md);
        }
        
        .switch {
            position: relative;
            display: inline-block;
            width: 50px;
            height: 24px;
        }
        
        .switch input {
            opacity: 0;
            width: 0;
            height: 0;
        }
        
        .slider {
            position: absolute;
            cursor: pointer;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background-color: var(--border-color);
            transition: var(--transition-normal);
            border-radius: var(--radius-full);
        }
        
        .slider:before {
            position: absolute;
            content: "";
            height: 16px;
            width: 16px;
            left: 4px;
            bottom: 4px;
            background-color: var(--text-primary);
            transition: var(--transition-normal);
            border-radius: 50%;
        }
        
        input:checked + .slider {
            background-color: var(--blood-red);
        }
        
        input:checked + .slider:before {
            transform: translateX(26px);
        }
        
        .sidebar-tags {
            display: flex;
            gap: var(--spacing-xs);
            flex-wrap: wrap;
        }
        
        .sidebar-tag {
            padding: 4px 8px;
            background: var(--tertiary-dark);
            border: 1px solid var(--border-color);
            border-radius: var(--radius-full);
            font-size: 0.75rem;
            color: var(--text-muted);
            cursor: pointer;
            transition: all var(--transition-fast);
        }
        
        .sidebar-tag:hover {
            background: var(--blood-red);
            color: white;
            border-color: var(--blood-red);
        }
        
        .empty-state {
            text-align: center;
            padding: var(--spacing-xl);
            color: var(--text-muted);
        }
        
        .empty-state i {
            font-size: 2rem;
            margin-bottom: var(--spacing-sm);
            display: block;
        }
        
        /* ========== MAIN CONTENT ========== */
        .page-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: var(--spacing-xl);
            padding-bottom: var(--spacing-md);
            border-bottom: 1px solid var(--border-color);
        }
        
        .page-title {
            display: flex;
            align-items: center;
            gap: var(--spacing-md);
        }
        
        .page-title i {
            color: var(--blood-red);
        }
        
        .page-actions {
            display: flex;
            gap: var(--spacing-sm);
        }
        
        /* ========== CARDS ========== */
        .card {
            background: var(--secondary-dark);
            border: 1px solid var(--border-color);
            border-radius: var(--radius-lg);
            padding: var(--spacing-lg);
            transition: all var(--transition-normal);
            position: relative;
            overflow: hidden;
        }
        
        .card:hover {
            border-color: var(--border-light);
            transform: translateY(-4px);
            box-shadow: var(--shadow-lg);
        }
        
        .card.glow {
            border-color: var(--blood-red);
            box-shadow: var(--shadow-glow);
        }
        
        .card-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: var(--spacing-md);
            padding-bottom: var(--spacing-sm);
            border-bottom: 1px solid var(--border-color);
        }
        
        .card-title {
            display: flex;
            align-items: center;
            gap: var(--spacing-sm);
            color: var(--text-primary);
            font-weight: 600;
        }
        
        .card-title i {
            color: var(--blood-red);
        }
        
        /* ========== STATS CARDS ========== */
        .stats-grid-large {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: var(--spacing-lg);
            margin-bottom: var(--spacing-xl);
        }
        
        .stat-card {
            background: var(--secondary-dark);
            border: 1px solid var(--border-color);
            border-radius: var(--radius-lg);
            padding: var(--spacing-lg);
            text-align: center;
            transition: all var(--transition-normal);
        }
        
        .stat-card:hover {
            border-color: var(--blood-red);
            transform: translateY(-4px);
        }
        
        .stat-icon {
            width: 60px;
            height: 60px;
            background: var(--gradient-blood);
            border-radius: var(--radius-lg);
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0 auto var(--spacing-md);
            color: white;
            font-size: 1.5rem;
        }
        
        .stat-value {
            font-size: 2.5rem;
            font-weight: bold;
            color: var(--blood-red);
            line-height: 1;
            margin-bottom: var(--spacing-sm);
        }
        
        .stat-description {
            color: var(--text-muted);
            font-size: 0.875rem;
        }
        
        /* ========== BUTTONS ========== */
        .btn {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: var(--spacing-sm);
            padding: var(--spacing-sm) var(--spacing-lg);
            border: none;
            border-radius: var(--radius-md);
            font-family: 'Inter', sans-serif;
            font-weight: 500;
            cursor: pointer;
            transition: all var(--transition-fast);
            text-decoration: none;
        }
        
        .btn-primary {
            background: var(--gradient-blood);
            color: white;
        }
        
        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: var(--shadow-glow);
        }
        
        .btn-secondary {
            background: var(--tertiary-dark);
            color: var(--text-primary);
            border: 1px solid var(--border-color);
        }
        
        .btn-secondary:hover {
            background: var(--secondary-dark);
            border-color: var(--border-light);
        }
        
        .btn-outline {
            background: transparent;
            color: var(--text-primary);
            border: 1px solid var(--border-color);
        }
        
        .btn-outline:hover {
            border-color: var(--blood-red);
            color: var(--blood-red);
        }
        
        .btn-sm {
            padding: var(--spacing-xs) var(--spacing-md);
            font-size: 0.875rem;
        }
        
        .btn-lg {
            padding: var(--spacing-md) var(--spacing-xl);
            font-size: 1.125rem;
        }
        
        .btn-icon {
            width: 40px;
            height: 40px;
            padding: 0;
            border-radius: var(--radius-md);
        }
        
        /* ========== FORMS ========== */
        .form-group {
            margin-bottom: var(--spacing-lg);
        }
        
        .form-label {
            display: block;
            margin-bottom: var(--spacing-sm);
            color: var(--text-primary);
            font-weight: 500;
        }
        
        .form-control {
            width: 100%;
            padding: var(--spacing-sm) var(--spacing-md);
            background: var(--tertiary-dark);
            border: 1px solid var(--border-color);
            border-radius: var(--radius-md);
            color: var(--text-primary);
            font-family: 'Inter', sans-serif;
            transition: all var(--transition-fast);
        }
        
        .form-control:focus {
            outline: none;
            border-color: var(--blood-red);
            box-shadow: 0 0 0 2px var(--blood-glow);
        }
        
        .form-control::placeholder {
            color: var(--text-muted);
        }
        
        textarea.form-control {
            min-height: 100px;
            resize: vertical;
        }
        
        select.form-control {
            appearance: none;
            background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='%238B0000' viewBox='0 0 16 16'%3E%3Cpath d='M7.247 11.14 2.451 5.658C1.885 5.013 2.345 4 3.204 4h9.592a1 1 0 0 1 .753 1.659l-4.796 5.48a1 1 0 0 1-1.506 0z'/%3E%3C/svg%3E");
            background-repeat: no-repeat;
            background-position: right 12px center;
            background-size: 12px;
            padding-right: 36px;
        }
        
        /* ========== ALERTS ========== */
        .alert {
            display: flex;
            align-items: center;
            padding: var(--spacing-md);
            background: var(--tertiary-dark);
            border: 1px solid;
            border-radius: var(--radius-md);
            margin-bottom: var(--spacing-lg);
            position: relative;
        }
        
        .alert-success {
            border-color: #28a745;
            color: #d4edda;
        }
        
        .alert-error {
            border-color: #dc3545;
            color: #f8d7da;
        }
        
        .alert-warning {
            border-color: #ffc107;
            color: #fff3cd;
        }
        
        .alert-info {
            border-color: #17a2b8;
            color: #d1ecf1;
        }
        
        .alert-close {
            margin-left: auto;
            background: none;
            border: none;
            color: inherit;
            cursor: pointer;
            padding: 4px;
        }
        
        /* ========== TABLES ========== */
        .table-container {
            background: var(--secondary-dark);
            border: 1px solid var(--border-color);
            border-radius: var(--radius-lg);
            overflow: hidden;
        }
        
        .table {
            width: 100%;
            color: var(--text-primary);
            border-collapse: collapse;
        }
        
        .table th {
            background: var(--tertiary-dark);
            padding: var(--spacing-md);
            text-align: left;
            font-weight: 600;
            border-bottom: 1px solid var(--border-color);
        }
        
        .table td {
            padding: var(--spacing-md);
            border-bottom: 1px solid var(--border-color);
        }
        
        .table tr:last-child td {
            border-bottom: none;
        }
        
        .table tr:hover {
            background: var(--tertiary-dark);
        }
        
        /* ========== CHARACTER CARDS ========== */
        .characters-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
            gap: var(--spacing-lg);
        }
        
        .character-card {
            background: var(--secondary-dark);
            border: 1px solid var(--border-color);
            border-radius: var(--radius-lg);
            overflow: hidden;
            transition: all var(--transition-normal);
        }
        
        .character-card:hover {
            transform: translateY(-4px);
            border-color: var(--blood-red);
            box-shadow: var(--shadow-lg);
        }
        
        .character-cover {
            height: 160px;
            background: var(--tertiary-dark);
            display: flex;
            align-items: center;
            justify-content: center;
            border-bottom: 1px solid var(--border-color);
            position: relative;
            overflow: hidden;
        }
        
        .character-cover i {
            font-size: 4rem;
            color: var(--blood-red);
            opacity: 0.5;
        }
        
        .character-cover img {
            width: 100%;
            height: 100%;
            object-fit: cover;
        }
        
        .character-body {
            padding: var(--spacing-lg);
        }
        
        .character-header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: var(--spacing-md);
        }
        
        .character-name {
            font-size: 1.25rem;
            font-weight: 600;
            color: var(--text-primary);
            margin: 0;
        }
        
        .character-meta {
            display: flex;
            gap: var(--spacing-sm);
            margin-bottom: var(--spacing-md);
        }
        
        .character-type {
            background: var(--tertiary-dark);
            color: var(--blood-red);
            padding: 4px 8px;
            border-radius: var(--radius-full);
            font-size: 0.75rem;
            font-weight: 500;
        }
        
        .character-priority {
            display: inline-flex;
            align-items: center;
            gap: 4px;
            background: var(--tertiary-dark);
            color: var(--text-muted);
            padding: 4px 8px;
            border-radius: var(--radius-full);
            font-size: 0.75rem;
        }
        
        .character-priority i {
            color: var(--blood-red);
        }
        
        .character-description {
            color: var(--text-secondary);
            font-size: 0.875rem;
            line-height: 1.5;
            margin-bottom: var(--spacing-lg);
            display: -webkit-box;
            -webkit-line-clamp: 3;
            -webkit-box-orient: vertical;
            overflow: hidden;
        }
        
        .character-footer {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding-top: var(--spacing-md);
            border-top: 1px solid var(--border-color);
        }
        
        .character-stats {
            display: flex;
            gap: var(--spacing-lg);
        }
        
        .character-stat {
            text-align: center;
        }
        
        .stat-number {
            display: block;
            font-size: 1.25rem;
            font-weight: bold;
            color: var(--blood-red);
        }
        
        .stat-label {
            display: block;
            font-size: 0.75rem;
            color: var(--text-muted);
        }
        
        /* ========== PRIORITY BAR ========== */
        .priority-bar {
            width: 100%;
            height: 6px;
            background: var(--tertiary-dark);
            border-radius: var(--radius-full);
            overflow: hidden;
            margin: var(--spacing-md) 0;
        }
        
        .priority-fill {
            height: 100%;
            background: var(--gradient-blood);
            border-radius: var(--radius-full);
            transition: width var(--transition-normal);
        }
        
        .priority-circle {
            width: 120px;
            height: 120px;
            border-radius: 50%;
            border: 3px solid var(--blood-red);
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            margin: var(--spacing-lg) auto;
            background: var(--secondary-dark);
            position: relative;
        }
        
        .priority-value {
            font-size: 2.5rem;
            font-weight: bold;
            color: var(--blood-red);
        }
        
        .priority-label {
            font-size: 0.875rem;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        /* ========== OBJECTIVES ========== */
        .objectives-list-full {
            display: flex;
            flex-direction: column;
            gap: var(--spacing-sm);
        }
        
        .objective-card {
            background: var(--tertiary-dark);
            border: 1px solid var(--border-color);
            border-radius: var(--radius-md);
            padding: var(--spacing-md);
            display: flex;
            align-items: center;
            gap: var(--spacing-md);
            transition: all var(--transition-fast);
        }
        
        .objective-card:hover {
            border-color: var(--blood-red);
            transform: translateX(4px);
        }
        
        .objective-card.completed {
            opacity: 0.7;
            background: var(--secondary-dark);
        }
        
        .objective-checkbox {
            width: 24px;
            height: 24px;
            background: var(--secondary-dark);
            border: 2px solid var(--border-color);
            border-radius: var(--radius-sm);
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            transition: all var(--transition-fast);
        }
        
        .objective-card.completed .objective-checkbox {
            background: var(--blood-red);
            border-color: var(--blood-red);
        }
        
        .objective-checkbox i {
            color: white;
            font-size: 0.75rem;
            opacity: 0;
        }
        
        .objective-card.completed .objective-checkbox i {
            opacity: 1;
        }
        
        .objective-content-full {
            flex: 1;
        }
        
        .objective-description {
            color: var(--text-primary);
            margin-bottom: 4px;
        }
        
        .objective-meta {
            display: flex;
            gap: var(--spacing-md);
            font-size: 0.75rem;
            color: var(--text-muted);
        }
        
        .objective-actions {
            display: flex;
            gap: var(--spacing-xs);
        }
        
        /* ========== TAGS ========== */
        .tags-cloud {
            display: flex;
            flex-wrap: wrap;
            gap: var(--spacing-xs);
            margin-top: var(--spacing-md);
        }
        
        .tag {
            padding: 4px 12px;
            background: var(--tertiary-dark);
            border: 1px solid var(--border-color);
            border-radius: var(--radius-full);
            font-size: 0.875rem;
            color: var(--text-secondary);
            transition: all var(--transition-fast);
        }
        
        .tag:hover {
            background: var(--blood-red);
            color: white;
            border-color: var(--blood-red);
        }
        
        /* ========== ANIMATIONS ========== */
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        @keyframes slideIn {
            from { transform: translateX(-20px); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
        
        .fade-in {
            animation: fadeIn 0.5s ease-out;
        }
        
        .slide-in {
            animation: slideIn 0.3s ease-out;
        }
        
        /* ========== RESPONSIVE ========== */
        @media (max-width: 1200px) {
            .container-main {
                padding: var(--spacing-md);
            }
            
            .characters-grid {
                grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            }
        }
        
        @media (max-width: 992px) {
            .navbar-toggler {
                display: block;
            }
            
            .navbar-menu {
                position: fixed;
                top: 70px;
                left: 0;
                right: 0;
                background: var(--secondary-dark);
                border-bottom: 1px solid var(--border-color);
                flex-direction: column;
                padding: var(--spacing-lg);
                display: none;
                box-shadow: var(--shadow-lg);
            }
            
            .navbar-menu.active {
                display: flex;
            }
            
            .nav-items {
                flex-direction: column;
                width: 100%;
            }
            
            .nav-item {
                width: 100%;
                justify-content: flex-start;
            }
            
            .sidebar-toggle {
                display: flex;
            }
            
            .sidebar {
                top: 0;
                height: 100vh;
                width: 100%;
                max-width: 400px;
            }
        }
        
        @media (max-width: 768px) {
            .container-main {
                padding: var(--spacing-sm);
            }
            
            .page-header {
                flex-direction: column;
                align-items: flex-start;
                gap: var(--spacing-md);
            }
            
            .page-actions {
                width: 100%;
                justify-content: space-between;
            }
            
            .stats-grid-large {
                grid-template-columns: repeat(2, 1fr);
            }
            
            .characters-grid {
                grid-template-columns: 1fr;
            }
        }
        
        @media (max-width: 576px) {
            .stats-grid-large {
                grid-template-columns: 1fr;
            }
            
            h1 { font-size: 2rem; }
            h2 { font-size: 1.75rem; }
            h3 { font-size: 1.5rem; }
            
            .stat-value {
                font-size: 2rem;
            }
            
            .character-cover {
                height: 120px;
            }
        }
        
        /* ========== UTILITY CLASSES ========== */
        .mb-0 { margin-bottom: 0 !important; }
        .mb-1 { margin-bottom: var(--spacing-xs) !important; }
        .mb-2 { margin-bottom: var(--spacing-sm) !important; }
        .mb-3 { margin-bottom: var(--spacing-md) !important; }
        .mb-4 { margin-bottom: var(--spacing-lg) !important; }
        .mb-5 { margin-bottom: var(--spacing-xl) !important; }
        
        .mt-0 { margin-top: 0 !important; }
        .mt-1 { margin-top: var(--spacing-xs) !important; }
        .mt-2 { margin-top: var(--spacing-sm) !important; }
        .mt-3 { margin-top: var(--spacing-md) !important; }
        .mt-4 { margin-top: var(--spacing-lg) !important; }
        .mt-5 { margin-top: var(--spacing-xl) !important; }
        
        .text-center { text-align: center !important; }
        .text-right { text-align: right !important; }
        
        .d-flex { display: flex !important; }
        .d-none { display: none !important; }
        
        .justify-between { justify-content: space-between !important; }
        .align-center { align-items: center !important; }
        
        .w-100 { width: 100% !important; }
        
        .opacity-50 { opacity: 0.5 !important; }
        .opacity-75 { opacity: 0.75 !important; }
        
        .cursor-pointer { cursor: pointer !important; }
        
        .scrollbar {
            scrollbar-width: thin;
            scrollbar-color: var(--blood-red) var(--tertiary-dark);
        }
        
        .scrollbar::-webkit-scrollbar {
            width: 8px;
        }
        
        .scrollbar::-webkit-scrollbar-track {
            background: var(--tertiary-dark);
            border-radius: var(--radius-full);
        }
        
        .scrollbar::-webkit-scrollbar-thumb {
            background: var(--blood-red);
            border-radius: var(--radius-full);
        }
        
        .scrollbar::-webkit-scrollbar-thumb:hover {
            background: var(--blood-light);
        }
    </style>
</head>
<body>
    {{ navbar|safe }}
    
    <main class="container-main fade-in">
        {{ content|safe }}
    </main>
    
    {{ sidebar|safe }}
    
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        // Funções globais
        function toggleSidebar() {
            const sidebar = document.querySelector('.sidebar');
            const toggle = document.querySelector('.sidebar-toggle');
            sidebar.classList.toggle('active');
            
            if (sidebar.classList.contains('active')) {
                toggle.innerHTML = '<i class="fas fa-times"></i>';
            } else {
                toggle.innerHTML = '<i class="fas fa-bars"></i>';
            }
        }
        
        function toggleNavbar() {
            const menu = document.getElementById('navbarMenu');
            menu.classList.toggle('active');
        }
        
        function toggleDarkMode() {
            const toggle = document.getElementById('darkModeToggle');
            document.body.classList.toggle('light-mode', !toggle.checked);
        }
        
        function novaNotaRapida() {
            const titulo = prompt('Título da nota:');
            if (titulo) {
                const conteudo = prompt('Conteúdo da nota:');
                if (conteudo !== null) {
                    fetch('/salvar_nota_rapida', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            titulo: titulo,
                            conteudo: conteudo,
                            cor: '#8B0000'
                        })
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            showToast('Nota salva com sucesso!', 'success');
                            setTimeout(() => location.reload(), 1000);
                        } else {
                            showToast('Erro ao salvar nota: ' + data.message, 'error');
                        }
                    });
                }
            }
        }
        
        function editarNota(notaId) {
            const novoTitulo = prompt('Novo título:');
            if (novoTitulo) {
                const novoConteudo = prompt('Novo conteúdo:');
                if (novoConteudo !== null) {
                    alert('Funcionalidade de edição em desenvolvimento!');
                }
            }
        }
        
        function excluirNota(notaId) {
            if (confirm('Tem certeza que deseja excluir esta nota?')) {
                fetch('/excluir_nota_rapida/' + notaId, {
                    method: 'DELETE'
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        showToast('Nota excluída com sucesso!', 'success');
                        setTimeout(() => location.reload(), 1000);
                    } else {
                        showToast('Erro ao excluir nota: ' + data.message, 'error');
                    }
                });
            }
        }
        
        function toggleObjetivoSidebar(objetivoId) {
            fetch('/toggle_objetivo/' + objetivoId, {
                method: 'POST'
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    setTimeout(() => location.reload(), 300);
                }
            });
        }
        
        function gerarRelatorio() {
            fetch('/gerar_relatorio')
            .then(() => {
                showToast('Relatório gerado com sucesso!', 'success');
                setTimeout(() => location.reload(), 1000);
            });
        }
        
        function updatePriorityBars() {
            const prioridade = document.getElementById('prioridade')?.value || 5;
            const bar = document.getElementById('prioridade-bar');
            if (bar) {
                bar.style.width = (prioridade * 10) + '%';
            }
        }
        
        function showToast(message, type = 'info') {
            // Implementação simplificada de toast
            alert(`${type.toUpperCase()}: ${message}`);
        }
        
        function confirmDelete(message) {
            return confirm(message || 'Tem certeza que deseja excluir?');
        }
        
        // Inicialização
        document.addEventListener('DOMContentLoaded', function() {
            updatePriorityBars();
            
            // Fechar alertas
            document.querySelectorAll('.alert-close').forEach(button => {
                button.addEventListener('click', function() {
                    this.closest('.alert').style.display = 'none';
                });
            });
            
            // Fechar sidebar ao clicar fora (mobile)
            document.addEventListener('click', function(event) {
                const sidebar = document.querySelector('.sidebar');
                const toggle = document.querySelector('.sidebar-toggle');
                
                if (window.innerWidth <= 992 && 
                    sidebar.classList.contains('active') &&
                    !sidebar.contains(event.target) &&
                    !toggle.contains(event.target)) {
                    toggleSidebar();
                }
            });
            
            // Adicionar animações de entrada
            const cards = document.querySelectorAll('.card, .character-card, .stat-card');
            cards.forEach((card, index) => {
                card.style.animationDelay = `${index * 0.1}s`;
                card.classList.add('fade-in');
            });
        });
    </script>
</body>
</html>'''

# =============================================
# TEMPLATES DE LOGIN E CADASTRO
# =============================================

LOGIN_TEMPLATE = '''
<div class="auth-container">
    <div class="auth-card">
        <div class="auth-header">
            <div class="auth-logo">
                <i class="fas fa-skull-crossbones"></i>
            </div>
            <h1 class="berserk-font">GRIMÓRIO BERSERK</h1>
            <p class="auth-subtitle">Entre no mundo dos personagens</p>
        </div>
        
        <div class="auth-body">
            {{ messages|safe }}
            
            <form method="POST" class="auth-form">
                <div class="form-group">
                    <label class="form-label">Email</label>
                    <input type="email" class="form-control" name="email" required 
                           placeholder="seu@email.com">
                </div>
                
                <div class="form-group">
                    <label class="form-label">Senha</label>
                    <input type="password" class="form-control" name="senha" required 
                           placeholder="Sua senha secreta">
                </div>
                
                <button type="submit" class="btn btn-primary w-100">
                    <i class="fas fa-sign-in-alt me-2"></i>
                    Entrar no Grimório
                </button>
            </form>
            
            <div class="auth-divider">
                <span>OU</span>
            </div>
            
            <a href="/cadastro" class="btn btn-outline w-100">
                <i class="fas fa-user-plus me-2"></i>
                Criar Nova Conta
            </a>
        </div>
    </div>
</div>

<style>
.auth-container {
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    background: var(--primary-dark);
    padding: var(--spacing-lg);
}

.auth-card {
    background: var(--secondary-dark);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-xl);
    padding: var(--spacing-xxl);
    width: 100%;
    max-width: 400px;
    box-shadow: var(--shadow-lg);
}

.auth-header {
    text-align: center;
    margin-bottom: var(--spacing-xl);
}

.auth-logo {
    width: 80px;
    height: 80px;
    background: var(--gradient-blood);
    border-radius: var(--radius-lg);
    display: flex;
    align-items: center;
    justify-content: center;
    margin: 0 auto var(--spacing-lg);
    color: white;
    font-size: 2rem;
}

.auth-header h1 {
    font-size: 2rem;
    margin-bottom: var(--spacing-sm);
    color: var(--blood-red);
}

.auth-subtitle {
    color: var(--text-muted);
    font-size: 0.875rem;
}

.auth-body {
    margin-top: var(--spacing-xl);
}

.auth-divider {
    display: flex;
    align-items: center;
    margin: var(--spacing-lg) 0;
    color: var(--text-muted);
}

.auth-divider::before,
.auth-divider::after {
    content: '';
    flex: 1;
    height: 1px;
    background: var(--border-color);
}

.auth-divider span {
    padding: 0 var(--spacing-md);
    font-size: 0.875rem;
}
</style>
'''

CADASTRO_TEMPLATE = '''
<div class="auth-container">
    <div class="auth-card">
        <div class="auth-header">
            <div class="auth-logo">
                <i class="fas fa-user-plus"></i>
            </div>
            <h1 class="berserk-font">CRIAR CONTA</h1>
            <p class="auth-subtitle">Junte-se à legião de criadores</p>
        </div>
        
        <div class="auth-body">
            {{ messages|safe }}
            
            <form method="POST" class="auth-form">
                <div class="form-group">
                    <label class="form-label">Nome</label>
                    <input type="text" class="form-control" name="nome" required 
                           placeholder="Seu nome">
                </div>
                
                <div class="form-group">
                    <label class="form-label">Email</label>
                    <input type="email" class="form-control" name="email" required 
                           placeholder="seu@email.com">
                </div>
                
                <div class="form-group">
                    <label class="form-label">Senha</label>
                    <input type="password" class="form-control" name="senha" required 
                           placeholder="Crie uma senha forte">
                </div>
                
                <div class="form-group">
                    <label class="form-label">Confirmar Senha</label>
                    <input type="password" class="form-control" name="confirmar_senha" required 
                           placeholder="Repita a senha">
                </div>
                
                <div class="form-check mb-4">
                    <input class="form-check-input" type="checkbox" id="terms" required>
                    <label class="form-check-label" for="terms">
                        Aceito os termos deste mundo sombrio
                    </label>
                </div>
                
                <button type="submit" class="btn btn-primary w-100">
                    <i class="fas fa-user-plus me-2"></i>
                    Criar Conta
                </button>
            </form>
            
            <div class="auth-divider">
                <span>JÁ TEM UMA CONTA?</span>
            </div>
            
            <a href="/login" class="btn btn-outline w-100">
                <i class="fas fa-sign-in-alt me-2"></i>
                Fazer Login
            </a>
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
            flash('Bem-vindo ao Grimório, criador de mundos!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Credenciais inválidas! Verifique seu email e senha.', 'error')
    
    content = LOGIN_TEMPLATE.replace('{{ messages|safe }}', get_flashed_messages_html())
    template = BASE_TEMPLATE.replace('{{ content|safe }}', content)\
                            .replace('{{ navbar|safe }}', '')\
                            .replace('{{ sidebar|safe }}', '')
    
    return render_template_string(template)


@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        senha = request.form['senha']
        confirmar_senha = request.form['confirmar_senha']
        
        if senha != confirmar_senha:
            flash('As senhas não coincidem!', 'error')
            return redirect(url_for('cadastro'))
        
        if Usuario.query.filter_by(email=email).first():
            flash('Este email já está registrado!', 'error')
            return redirect(url_for('cadastro'))
        
        usuario = Usuario(
            nome=nome,
            email=email,
            senha=generate_password_hash(senha)
        )
        
        db.session.add(usuario)
        db.session.commit()
        
        flash('Conta criada com sucesso! Agora você pode fazer login.', 'success')
        return redirect(url_for('login'))
    
    content = CADASTRO_TEMPLATE.replace('{{ messages|safe }}', get_flashed_messages_html())
    template = BASE_TEMPLATE.replace('{{ content|safe }}', content)\
                            .replace('{{ navbar|safe }}', '')\
                            .replace('{{ sidebar|safe }}', '')
    
    return render_template_string(template)


@app.route('/dashboard')
def dashboard():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
    
    usuario = Usuario.query.get(session['usuario_id'])
    estatisticas = calcular_estatisticas(usuario.id)
    
    personagens_recentes = Personagem.query.filter_by(usuario_id=usuario.id)\
        .order_by(Personagem.data_atualizacao.desc()).limit(3).all()
    
    personagens_html = ""
    for personagem in personagens_recentes:
        objetivos_concluidos = sum(1 for obj in personagem.objetivos if obj.concluido)
        objetivos_total = len(personagem.objetivos)
        
        personagens_html += f'''
        <div class="character-card slide-in">
            <div class="character-cover">
                {'<img src="' + personagem.imagem_url + '">' if personagem.imagem_url else '<i class="fas fa-user-ninja"></i>'}
            </div>
            <div class="character-body">
                <div class="character-header">
                    <h3 class="character-name">{personagem.nome}</h3>
                    <div class="dropdown">
                        <button class="btn btn-icon btn-secondary">
                            <i class="fas fa-ellipsis-v"></i>
                        </button>
                        <div class="dropdown-menu">
                            <a href="/detalhes_personagem/{personagem.id}" class="dropdown-item">
                                <i class="fas fa-eye"></i> Ver Detalhes
                            </a>
                            <a href="/editar_personagem/{personagem.id}" class="dropdown-item">
                                <i class="fas fa-edit"></i> Editar
                            </a>
                            <a href="/excluir_personagem/{personagem.id}" class="dropdown-item" 
                               onclick="return confirmDelete('Excluir {personagem.nome}?')">
                                <i class="fas fa-trash"></i> Excluir
                            </a>
                        </div>
                    </div>
                </div>
                
                <div class="character-meta">
                    <span class="character-type">{personagem.tipo}</span>
                    <span class="character-priority">
                        <i class="fas fa-bolt"></i>
                        Prioridade {personagem.prioridade}/10
                    </span>
                </div>
                
                <p class="character-description">
                    {personagem.descricao[:100] if personagem.descricao else 'Sem descrição...'}
                </p>
                
                <div class="character-footer">
                    <div class="character-stats">
                        <div class="character-stat">
                            <span class="stat-number">{len(personagem.objetivos)}</span>
                            <span class="stat-label">Objetivos</span>
                        </div>
                        <div class="character-stat">
                            <span class="stat-number">{objetivos_concluidos}</span>
                            <span class="stat-label">Concluídos</span>
                        </div>
                        <div class="character-stat">
                            <span class="stat-number">{personagem.prioridade}</span>
                            <span class="stat-label">Prioridade</span>
                        </div>
                    </div>
                    <a href="/detalhes_personagem/{personagem.id}" class="btn btn-sm btn-outline">
                        <i class="fas fa-arrow-right"></i>
                    </a>
                </div>
            </div>
        </div>
        '''
    
    dashboard_content = f'''
    <div class="page-header">
        <div class="page-title">
            <h1><i class="fas fa-eye text-blood"></i> Dashboard</h1>
            <span class="text-muted">Bem-vindo, {usuario.nome}</span>
        </div>
        <div class="page-actions">
            <a href="/novo_personagem" class="btn btn-primary">
                <i class="fas fa-user-plus"></i> Novo Personagem
            </a>
            <a href="/buscar" class="btn btn-secondary">
                <i class="fas fa-search"></i> Buscar
            </a>
        </div>
    </div>
    
    {get_flashed_messages_html()}
    
    <div class="stats-grid-large mb-5">
        <div class="stat-card">
            <div class="stat-icon">
                <i class="fas fa-users"></i>
            </div>
            <div class="stat-value">{estatisticas['total_personagens']}</div>
            <div class="stat-description">Personagens Criados</div>
        </div>
        
        <div class="stat-card">
            <div class="stat-icon">
                <i class="fas fa-bullseye"></i>
            </div>
            <div class="stat-value">{estatisticas['objetivos_ativos']}</div>
            <div class="stat-description">Objetivos Ativos</div>
        </div>
        
        <div class="stat-card">
            <div class="stat-icon">
                <i class="fas fa-chart-line"></i>
            </div>
            <div class="stat-value">{estatisticas['prioridade_media']}</div>
            <div class="stat-description">Prioridade Média</div>
        </div>
        
        <div class="stat-card">
            <div class="stat-icon">
                <i class="fas fa-check-circle"></i>
            </div>
            <div class="stat-value">{estatisticas['objetivos_concluidos']}</div>
            <div class="stat-description">Objetivos Concluídos</div>
        </div>
    </div>
    
    <div class="card mb-5">
        <div class="card-header">
            <h3 class="card-title"><i class="fas fa-history text-blood"></i> Personagens Recentes</h3>
            <a href="/personagens" class="btn btn-sm btn-outline">
                Ver Todos <i class="fas fa-arrow-right"></i>
            </a>
        </div>
        <div class="card-body">
            <div class="characters-grid">
                {personagens_html if personagens_html else '''
                <div class="empty-state">
                    <i class="fas fa-users-slash fa-3x"></i>
                    <h4>Nenhum personagem encontrado</h4>
                    <p class="text-muted">Comece criando seu primeiro personagem!</p>
                    <a href="/novo_personagem" class="btn btn-primary mt-3">
                        <i class="fas fa-user-plus"></i> Criar Primeiro Personagem
                    </a>
                </div>'''}
            </div>
        </div>
    </div>
    
    <div class="row">
        <div class="col-md-6 mb-4">
            <div class="card h-100">
                <div class="card-header">
                    <h3 class="card-title"><i class="fas fa-bolt text-blood"></i> Ações Rápidas</h3>
                </div>
                <div class="card-body">
                    <div class="quick-actions">
                        <a href="/novo_personagem" class="quick-action">
                            <div class="action-icon">
                                <i class="fas fa-user-plus"></i>
                            </div>
                            <span>Novo Personagem</span>
                        </a>
                        <a href="#" class="quick-action" onclick="novaNotaRapida(); return false;">
                            <div class="action-icon">
                                <i class="fas fa-sticky-note"></i>
                            </div>
                            <span>Nova Nota</span>
                        </a>
                        <a href="/buscar" class="quick-action">
                            <div class="action-icon">
                                <i class="fas fa-search"></i>
                            </div>
                            <span>Buscar Personagens</span>
                        </a>
                        <a href="/relatorio/personagens" class="quick-action">
                            <div class="action-icon">
                                <i class="fas fa-chart-pie"></i>
                            </div>
                            <span>Gerar Relatório</span>
                        </a>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="col-md-6 mb-4">
            <div class="card h-100">
                <div class="card-header">
                    <h3 class="card-title"><i class="fas fa-info-circle text-blood"></i> Sistema de Prioridades</h3>
                </div>
                <div class="card-body">
                    <p class="text-muted mb-3">
                        O sistema de prioridades (1-10) ajuda a organizar seus personagens por importância na história.
                    </p>
                    <div class="priority-bar mb-3">
                        <div class="priority-fill" style="width: 50%"></div>
                    </div>
                    <div class="d-flex justify-between text-sm">
                        <span class="text-muted">1 = Baixa prioridade</span>
                        <span class="text-muted">10 = Alta prioridade</span>
                    </div>
                </div>
            </div>
        </div>
    </div>
    '''
    
    template = BASE_TEMPLATE.replace('{{ content|safe }}', dashboard_content)\
                            .replace('{{ navbar|safe }}', create_navbar('dashboard'))\
                            .replace('{{ sidebar|safe }}', criar_menu_lateral(usuario.id, 'dashboard'))
    
    return render_template_string(template)


@app.route('/personagens')
def listar_personagens():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
    
    usuario = Usuario.query.get(session['usuario_id'])
    tipo_filter = request.args.get('tipo', 'todos')
    
    query = Personagem.query.filter_by(usuario_id=usuario.id)
    
    if tipo_filter != 'todos':
        query = query.filter_by(tipo=tipo_filter)
    
    personagens = query.order_by(Personagem.data_atualizacao.desc()).all()
    
    tipos = db.session.query(Personagem.tipo, db.func.count(Personagem.id)).filter_by(usuario_id=usuario.id).group_by(Personagem.tipo).all()
    
    filtro_html = '<div class="tags-cloud mb-4">'
    filtro_html += f'<span class="tag {'active' if tipo_filter == 'todos' else ''}" onclick="window.location=\'/personagens?tipo=todos\'">Todos ({Personagem.query.filter_by(usuario_id=usuario.id).count()})</span>'
    
    for tipo, quantidade in tipos:
        active = 'active' if tipo_filter == tipo else ''
        filtro_html += f'<span class="tag {active}" onclick="window.location=\'/personagens?tipo={tipo}\'">{tipo} ({quantidade})</span>'
    
    filtro_html += '</div>'
    
    personagens_html = ""
    for personagem in personagens:
        objetivos_concluidos = sum(1 for obj in personagem.objetivos if obj.concluido)
        objetivos_total = len(personagem.objetivos)
        
        personagens_html += f'''
        <div class="character-card">
            <div class="character-cover">
                {'<img src="' + personagem.imagem_url + '">' if personagem.imagem_url else '<i class="fas fa-user-circle"></i>'}
            </div>
            <div class="character-body">
                <div class="character-header">
                    <h3 class="character-name">{personagem.nome}</h3>
                    <div class="dropdown">
                        <button class="btn btn-icon btn-secondary">
                            <i class="fas fa-ellipsis-v"></i>
                        </button>
                        <div class="dropdown-menu">
                            <a href="/detalhes_personagem/{personagem.id}" class="dropdown-item">
                                <i class="fas fa-eye"></i> Ver Detalhes
                            </a>
                            <a href="/editar_personagem/{personagem.id}" class="dropdown-item">
                                <i class="fas fa-edit"></i> Editar
                            </a>
                            <a href="/excluir_personagem/{personagem.id}" class="dropdown-item" 
                               onclick="return confirmDelete('Excluir {personagem.nome}?')">
                                <i class="fas fa-trash"></i> Excluir
                            </a>
                        </div>
                    </div>
                </div>
                
                <div class="character-meta">
                    <span class="character-type">{personagem.tipo}</span>
                    <span class="character-priority">
                        <i class="fas fa-bolt"></i>
                        Prioridade {personagem.prioridade}/10
                    </span>
                </div>
                
                <p class="character-description">
                    {personagem.descricao[:150] if personagem.descricao else 'Sem descrição...'}
                </p>
                
                <div class="priority-bar">
                    <div class="priority-fill" style="width: {personagem.prioridade * 10}%"></div>
                </div>
                
                <div class="character-footer">
                    <div class="character-stats">
                        <div class="character-stat">
                            <span class="stat-number">{objetivos_total}</span>
                            <span class="stat-label">Objetivos</span>
                        </div>
                        <div class="character-stat">
                            <span class="stat-number">{objetivos_concluidos}</span>
                            <span class="stat-label">Concluídos</span>
                        </div>
                    </div>
                    <a href="/detalhes_personagem/{personagem.id}" class="btn btn-sm btn-primary">
                        Ver Detalhes
                    </a>
                </div>
            </div>
        </div>
        '''
    
    if not personagens_html:
        personagens_html = '''
        <div class="empty-state">
            <i class="fas fa-users-slash fa-3x"></i>
            <h4>Nenhum personagem encontrado</h4>
            <p class="text-muted">Comece criando seu primeiro personagem!</p>
            <a href="/novo_personagem" class="btn btn-primary mt-3">
                <i class="fas fa-user-plus"></i> Criar Primeiro Personagem
            </a>
        </div>
        '''
    
    content = f'''
    <div class="page-header">
        <div class="page-title">
            <h1><i class="fas fa-users text-blood"></i> Meus Personagens</h1>
        </div>
        <div class="page-actions">
            <a href="/novo_personagem" class="btn btn-primary">
                <i class="fas fa-user-plus"></i> Novo Personagem
            </a>
        </div>
    </div>
    
    {get_flashed_messages_html()}
    
    <div class="card mb-4">
        <div class="card-body">
            <h5 class="card-title mb-3"><i class="fas fa-filter text-blood"></i> Filtrar por Tipo</h5>
            {filtro_html}
        </div>
    </div>
    
    <div class="characters-grid">
        {personagens_html}
    </div>
    '''
    
    template = BASE_TEMPLATE.replace('{{ content|safe }}', content)\
                            .replace('{{ navbar|safe }}', create_navbar('personagens'))\
                            .replace('{{ sidebar|safe }}', criar_menu_lateral(usuario.id, 'personagens'))
    
    return render_template_string(template)


@app.route('/novo_personagem', methods=['GET', 'POST'])
def novo_personagem():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
    
    tipos = ['Personagem', 'NPC', 'Vilão', 'Aliado', 'Criatura', 'Monstro', 'Deus', 'Outro']
    
    if request.method == 'POST':
        nome = request.form['nome']
        tipo = request.form['tipo']
        descricao = request.form.get('descricao', '')
        prioridade = int(request.form.get('prioridade', 5))
        historia = request.form.get('historia', '')
        habilidades = request.form.get('habilidades', '')
        notas = request.form.get('notas', '')
        imagem_url = request.form.get('imagem_url', '')
        tags = request.form.get('tags', '')
        
        personagem = Personagem(
            nome=nome,
            tipo=tipo,
            descricao=descricao,
            prioridade=prioridade,
            historia=historia,
            habilidades=habilidades,
            notas=notas,
            imagem_url=imagem_url,
            tags=tags,
            usuario_id=session['usuario_id']
        )
        
        db.session.add(personagem)
        db.session.commit()
        
        objetivos_texto = request.form.get('objetivos', '')
        if objetivos_texto:
            objetivos_linhas = [obj.strip() for obj in objetivos_texto.split('\n') if obj.strip()]
            for obj_text in objetivos_linhas:
                if obj_text.startswith('-'):
                    obj_text = obj_text[1:].strip()
                
                objetivo = Objetivo(
                    descricao=obj_text,
                    personagem_id=personagem.id
                )
                db.session.add(objetivo)
        
        db.session.commit()
        
        flash(f'✅ Personagem Criado! {nome} foi adicionado com sucesso.', 'success')
        return redirect(url_for('detalhes_personagem', personagem_id=personagem.id))
    
    tipos_options = ''.join([f'<option value="{tipo}">{tipo}</option>' for tipo in tipos])
    
    form_html = f'''
    <div class="page-header">
        <div class="page-title">
            <h1><i class="fas fa-user-plus text-blood"></i> Criar Novo Personagem</h1>
        </div>
        <div class="page-actions">
            <a href="/personagens" class="btn btn-secondary">
                <i class="fas fa-arrow-left"></i> Voltar
            </a>
        </div>
    </div>
    
    {get_flashed_messages_html()}
    
    <form method="POST" onsubmit="return validateCharacterForm()">
        <div class="card mb-4">
            <div class="card-header">
                <h3 class="card-title"><i class="fas fa-scroll text-blood"></i> Informações Básicas</h3>
            </div>
            <div class="card-body">
                <div class="row">
                    <div class="col-md-6 mb-3">
                        <label class="form-label">Nome do Personagem *</label>
                        <input type="text" class="form-control" name="nome" required 
                               placeholder="Ex: Guts, Griffith, Casca, etc.">
                    </div>
                    <div class="col-md-6 mb-3">
                        <label class="form-label">Tipo *</label>
                        <select class="form-control" name="tipo" required>
                            <option value="">Selecione um tipo</option>
                            {tipos_options}
                        </select>
                    </div>
                </div>
                
                <div class="row">
                    <div class="col-md-6 mb-3">
                        <label class="form-label">Prioridade (1-10)</label>
                        <input type="number" class="form-control" name="prioridade" 
                               min="1" max="10" value="5" id="prioridade"
                               onchange="updatePriorityBars()" onkeyup="updatePriorityBars()">
                        <div class="priority-bar mt-2">
                            <div class="priority-fill" id="prioridade-bar" style="width: 50%"></div>
                        </div>
                        <small class="text-muted">1 = Baixa prioridade, 10 = Alta prioridade</small>
                    </div>
                    <div class="col-md-6 mb-3">
                        <label class="form-label">URL da Imagem</label>
                        <input type="url" class="form-control" name="imagem_url" 
                               placeholder="https://exemplo.com/imagem.jpg">
                        <small class="text-muted">Link para uma imagem do personagem</small>
                    </div>
                </div>
                
                <div class="mb-3">
                    <label class="form-label">Descrição</label>
                    <textarea class="form-control" name="descricao" rows="3"
                              placeholder="Descreva brevemente o personagem..."></textarea>
                </div>
            </div>
        </div>
        
        <div class="card mb-4">
            <div class="card-header">
                <h3 class="card-title"><i class="fas fa-bullseye text-blood"></i> Objetivos do Personagem</h3>
            </div>
            <div class="card-body">
                <textarea class="form-control" name="objetivos" rows="4"
                          placeholder="- Objetivo 1&#10;- Objetivo 2&#10;- Objetivo 3&#10;&#10;(Um objetivo por linha, comece com - )"></textarea>
                <small class="text-muted">Adicione os objetivos iniciais do personagem</small>
            </div>
        </div>
        
        <div class="card mb-4">
            <div class="card-header">
                <h3 class="card-title"><i class="fas fa-book text-blood"></i> Informações Adicionais</h3>
            </div>
            <div class="card-body">
                <div class="row">
                    <div class="col-md-6 mb-3">
                        <label class="form-label">História/Background</label>
                        <textarea class="form-control" name="historia" rows="4"
                                  placeholder="Conte a história do personagem..."></textarea>
                    </div>
                    <div class="col-md-6 mb-3">
                        <label class="form-label">Habilidades/Talentos</label>
                        <textarea class="form-control" name="habilidades" rows="4"
                                  placeholder="Habilidades, poderes, talentos..."></textarea>
                    </div>
                </div>
                
                <div class="row">
                    <div class="col-md-6 mb-3">
                        <label class="form-label">Notas Pessoais</label>
                        <textarea class="form-control" name="notas" rows="3"
                                  placeholder="Anotações, lembretes, detalhes..."></textarea>
                    </div>
                    <div class="col-md-6 mb-3">
                        <label class="form-label">Tags</label>
                        <input type="text" class="form-control" name="tags" 
                               placeholder="Ex: protagonista, campanha-1, grupo-espada">
                        <small class="text-muted">Separe as tags por vírgula</small>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="d-flex justify-content-end gap-2">
            <button type="reset" class="btn btn-secondary">
                <i class="fas fa-eraser"></i> Limpar
            </button>
            <button type="submit" class="btn btn-primary">
                <i class="fas fa-save"></i> Criar Personagem
            </button>
        </div>
    </form>
    
    <script>
        function validateCharacterForm() {{
            const nome = document.querySelector('input[name="nome"]').value;
            const tipo = document.querySelector('select[name="tipo"]').value;
            
            if (!nome.trim()) {{
                alert('Por favor, preencha o nome do personagem.');
                return false;
            }}
            
            if (!tipo) {{
                alert('Por favor, selecione um tipo para o personagem.');
                return false;
            }}
            
            return true;
        }}
    </script>
    '''
    
    template = BASE_TEMPLATE.replace('{{ content|safe }}', form_html)\
                            .replace('{{ navbar|safe }}', create_navbar('novo_personagem'))\
                            .replace('{{ sidebar|safe }}', criar_menu_lateral(session['usuario_id'], 'novo_personagem'))
    
    return render_template_string(template)


@app.route('/detalhes_personagem/<int:personagem_id>')
def detalhes_personagem(personagem_id):
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
    
    personagem = Personagem.query.get_or_404(personagem_id)
    
    if personagem.usuario_id != session['usuario_id']:
        flash('Acesso negado! Este personagem não pertence a você.', 'error')
        return redirect(url_for('dashboard'))
    
    tags_html = ""
    if personagem.tags:
        tags = [tag.strip() for tag in personagem.tags.split(',') if tag.strip()]
        tags_html = '<div class="tags-cloud">'
        for tag in tags:
            tags_html += f'<span class="tag">{tag}</span>'
        tags_html += '</div>'
    
    objetivos_html = ""
    for objetivo in personagem.objetivos:
        completed_class = 'completed' if objetivo.concluido else ''
        check_icon = 'fa-check' if objetivo.concluido else 'fa-circle'
        objetivos_html += f'''
        <div class="objective-card {completed_class}">
            <div class="objective-checkbox" onclick="toggleObjetivo({objetivo.id})">
                <i class="fas {check_icon}"></i>
            </div>
            <div class="objective-content-full">
                <div class="objective-description">{objetivo.descricao}</div>
                <div class="objective-meta">
                    <span>Prioridade: {objetivo.prioridade}/10</span>
                    {f'<span>Concluído em: {objetivo.data_conclusao.strftime("%d/%m/%Y")}</span>' if objetivo.concluido else ''}
                </div>
            </div>
            <div class="objective-actions">
                <a href="/excluir_objetivo/{objetivo.id}" class="btn btn-icon btn-sm btn-secondary" 
                   onclick="return confirmDelete('Excluir este objetivo?')">
                    <i class="fas fa-trash"></i>
                </a>
            </div>
        </div>
        '''
    
    if not objetivos_html:
        objetivos_html = '''
        <div class="empty-state">
            <i class="fas fa-flag"></i>
            <h4>Nenhum objetivo</h4>
            <p class="text-muted">Adicione objetivos para este personagem</p>
        </div>
        '''
    
    detalhes_html = f'''
    <div class="page-header">
        <div class="page-title">
            <h1><i class="fas fa-scroll text-blood"></i> {personagem.nome}</h1>
            <span class="text-muted">{personagem.tipo}</span>
        </div>
        <div class="page-actions">
            <a href="/editar_personagem/{personagem.id}" class="btn btn-secondary">
                <i class="fas fa-edit"></i> Editar
            </a>
            <a href="/personagens" class="btn btn-outline">
                <i class="fas fa-arrow-left"></i> Voltar
            </a>
        </div>
    </div>
    
    {get_flashed_messages_html()}
    
    <div class="row">
        <div class="col-lg-4 mb-4">
            <div class="card h-100">
                <div class="character-cover">
                    {'<img src="' + personagem.imagem_url + '">' if personagem.imagem_url else '<i class="fas fa-user-ninja"></i>'}
                </div>
                <div class="card-body">
                    <div class="text-center mb-4">
                        <h2 class="text-blood">{personagem.nome}</h2>
                        <div class="d-flex justify-center gap-2 mb-3">
                            <span class="character-type">{personagem.tipo}</span>
                            <span class="character-priority">
                                <i class="fas fa-bolt"></i> Pri: {personagem.prioridade}/10
                            </span>
                        </div>
                        
                        <div class="priority-circle">
                            <div class="priority-value">{personagem.prioridade}</div>
                            <div class="priority-label">PRIORIDADE</div>
                        </div>
                    </div>
                    
                    <div class="mb-4">
                        <table class="table">
                            <tr>
                                <td><i class="fas fa-calendar text-muted"></i></td>
                                <td>Criado em</td>
                                <td class="text-right">{personagem.data_criacao.strftime('%d/%m/%Y')}</td>
                            </tr>
                            <tr>
                                <td><i class="fas fa-sync text-muted"></i></td>
                                <td>Atualizado</td>
                                <td class="text-right">{personagem.data_atualizacao.strftime('%d/%m/%Y')}</td>
                            </tr>
                            <tr>
                                <td><i class="fas fa-bullseye text-muted"></i></td>
                                <td>Objetivos</td>
                                <td class="text-right">{len(personagem.objetivos)}</td>
                            </tr>
                        </table>
                    </div>
                    
                    {tags_html}
                </div>
            </div>
        </div>
        
        <div class="col-lg-8 mb-4">
            <div class="card mb-4">
                <div class="card-header">
                    <h3 class="card-title"><i class="fas fa-align-left text-blood"></i> Descrição</h3>
                </div>
                <div class="card-body">
                    <p class="text-muted" style="white-space: pre-line;">
                        {personagem.descricao or '<i>Nenhuma descrição fornecida.</i>'}
                    </p>
                </div>
            </div>
            
            <div class="card mb-4">
                <div class="card-header">
                    <div class="d-flex justify-between align-center">
                        <h3 class="card-title"><i class="fas fa-bullseye text-blood"></i> Objetivos</h3>
                        <span class="badge bg-secondary">
                            {len([o for o in personagem.objetivos if o.concluido])}/{len(personagem.objetivos)} concluídos
                        </span>
                    </div>
                </div>
                <div class="card-body">
                    <div class="objectives-list-full">
                        {objetivos_html}
                    </div>
                </div>
                <div class="card-footer">
                    <form method="POST" action="/adicionar_objetivo/{personagem.id}" class="d-flex gap-2">
                        <input type="text" class="form-control" name="descricao" 
                               placeholder="Novo objetivo..." required>
                        <button type="submit" class="btn btn-primary">
                            <i class="fas fa-plus"></i> Adicionar
                        </button>
                    </form>
                </div>
            </div>
            
            <div class="row">
                <div class="col-md-6 mb-4">
                    <div class="card h-100">
                        <div class="card-header">
                            <h3 class="card-title"><i class="fas fa-book text-blood"></i> História</h3>
                        </div>
                        <div class="card-body">
                            <p class="text-muted" style="white-space: pre-line;">
                                {personagem.historia or '<i>Nenhuma história registrada.</i>'}
                            </p>
                        </div>
                    </div>
                </div>
                
                <div class="col-md-6 mb-4">
                    <div class="card h-100">
                        <div class="card-header">
                            <h3 class="card-title"><i class="fas fa-fire text-blood"></i> Habilidades</h3>
                        </div>
                        <div class="card-body">
                            <p class="text-muted" style="white-space: pre-line;">
                                {personagem.habilidades or '<i>Nenhuma habilidade registrada.</i>'}
                            </p>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="card">
                <div class="card-header">
                    <h3 class="card-title"><i class="fas fa-sticky-note text-blood"></i> Notas</h3>
                </div>
                <div class="card-body">
                    <p class="text-muted" style="white-space: pre-line;">
                        {personagem.notas or '<i>Nenhuma nota registrada.</i>'}
                    </p>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        function toggleObjetivo(objetivoId) {{
            fetch('/toggle_objetivo/' + objetivoId, {{
                method: 'POST'
            }})
            .then(response => response.json())
            .then(data => {{
                if (data.success) {{
                    setTimeout(() => location.reload(), 300);
                }}
            }});
        }}
    </script>
    '''
    
    template = BASE_TEMPLATE.replace('{{ content|safe }}', detalhes_html)\
                            .replace('{{ navbar|safe }}', create_navbar())\
                            .replace('{{ sidebar|safe }}', criar_menu_lateral(session['usuario_id']))
    
    return render_template_string(template)


@app.route('/adicionar_objetivo/<int:personagem_id>', methods=['POST'])
def adicionar_objetivo(personagem_id):
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
    
    personagem = Personagem.query.get_or_404(personagem_id)
    
    if personagem.usuario_id != session['usuario_id']:
        flash('Acesso negado!', 'error')
        return redirect(url_for('dashboard'))
    
    descricao = request.form['descricao']
    prioridade = int(request.form.get('prioridade', 5))
    
    objetivo = Objetivo(
        descricao=descricao,
        prioridade=prioridade,
        personagem_id=personagem_id
    )
    
    db.session.add(objetivo)
    db.session.commit()
    
    flash('Objetivo adicionado com sucesso!', 'success')
    return redirect(url_for('detalhes_personagem', personagem_id=personagem_id))


@app.route('/toggle_objetivo/<int:objetivo_id>', methods=['POST'])
def toggle_objetivo(objetivo_id):
    if 'usuario_id' not in session:
        return jsonify({'success': False, 'message': 'Não autorizado'})
    
    objetivo = Objetivo.query.get_or_404(objetivo_id)
    personagem = Personagem.query.get(objetivo.personagem_id)
    
    if personagem.usuario_id != session['usuario_id']:
        return jsonify({'success': False, 'message': 'Acesso negado'})
    
    objetivo.concluido = not objetivo.concluido
    if objetivo.concluido:
        objetivo.data_conclusao = datetime.utcnow()
    else:
        objetivo.data_conclusao = None
    
    db.session.commit()
    
    return jsonify({'success': True, 'concluido': objetivo.concluido})


@app.route('/salvar_nota_rapida', methods=['POST'])
def salvar_nota_rapida():
    if 'usuario_id' not in session:
        return jsonify({'success': False, 'message': 'Não autorizado'})
    
    try:
        data = request.get_json()
        titulo = data['titulo']
        conteudo = data['conteudo']
        cor = data.get('cor', '#8B0000')
        
        nota = NotaRapida(
            titulo=titulo,
            conteudo=conteudo,
            cor=cor,
            usuario_id=session['usuario_id']
        )
        
        db.session.add(nota)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Nota salva com sucesso!'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@app.route('/excluir_nota_rapida/<int:nota_id>', methods=['DELETE'])
def excluir_nota_rapida(nota_id):
    if 'usuario_id' not in session:
        return jsonify({'success': False, 'message': 'Não autorizado'})
    
    nota = NotaRapida.query.get_or_404(nota_id)
    
    if nota.usuario_id != session['usuario_id']:
        return jsonify({'success': False, 'message': 'Acesso negado'})
    
    db.session.delete(nota)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Nota excluída com sucesso!'})


@app.route('/gerar_relatorio')
def gerar_relatorio():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
    
    flash('Relatório gerado com sucesso! (funcionalidade simulada)', 'success')
    return redirect(url_for('dashboard'))


@app.route('/buscar')
def buscar():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
    
    usuario = Usuario.query.get(session['usuario_id'])
    
    content = f'''
    <div class="page-header">
        <div class="page-title">
            <h1><i class="fas fa-search text-blood"></i> Buscar</h1>
        </div>
        <div class="page-actions">
            <a href="/personagens" class="btn btn-outline">
                <i class="fas fa-arrow-left"></i> Voltar
            </a>
        </div>
    </div>
    
    {get_flashed_messages_html()}
    
    <div class="card">
        <div class="card-header">
            <h3 class="card-title"><i class="fas fa-search text-blood"></i> Busca Avançada</h3>
        </div>
        <div class="card-body">
            <form method="GET" action="/buscar" class="mb-4">
                <div class="row">
                    <div class="col-md-8 mb-3">
                        <input type="text" class="form-control" name="q" 
                               placeholder="Digite o nome do personagem, tipo ou tags...">
                    </div>
                    <div class="col-md-4 mb-3">
                        <button type="submit" class="btn btn-primary w-100">
                            <i class="fas fa-search"></i> Buscar
                        </button>
                    </div>
                </div>
            </form>
            
            <div class="empty-state">
                <i class="fas fa-search fa-3x"></i>
                <h4>Funcionalidade de Busca</h4>
                <p class="text-muted">Em desenvolvimento...</p>
                <p class="text-muted">Aqui você poderá buscar personagens por nome, tipo, tags ou objetivos.</p>
                <a href="/personagens" class="btn btn-primary mt-3">
                    <i class="fas fa-arrow-left"></i> Voltar para Personagens
                </a>
            </div>
        </div>
    </div>
    '''
    
    template = BASE_TEMPLATE.replace('{{ content|safe }}', content)\
                            .replace('{{ navbar|safe }}', create_navbar('buscar'))\
                            .replace('{{ sidebar|safe }}', criar_menu_lateral(usuario.id, 'buscar'))
    
    return render_template_string(template)


@app.route('/configuracoes')
def configuracoes():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
    
    usuario = Usuario.query.get(session['usuario_id'])
    
    content = f'''
    <div class="page-header">
        <div class="page-title">
            <h1><i class="fas fa-cog text-blood"></i> Configurações</h1>
        </div>
        <div class="page-actions">
            <a href="/dashboard" class="btn btn-outline">
                <i class="fas fa-arrow-left"></i> Voltar
            </a>
        </div>
    </div>
    
    {get_flashed_messages_html()}
    
    <div class="card mb-4">
        <div class="card-header">
            <h3 class="card-title"><i class="fas fa-user text-blood"></i> Conta</h3>
        </div>
        <div class="card-body">
            <div class="row">
                <div class="col-md-6 mb-4">
                    <table class="table">
                        <tr>
                            <td><i class="fas fa-user text-muted"></i> Nome:</td>
                            <td class="text-right">{usuario.nome}</td>
                        </tr>
                        <tr>
                            <td><i class="fas fa-envelope text-muted"></i> Email:</td>
                            <td class="text-right">{usuario.email}</td>
                        </tr>
                        <tr>
                            <td><i class="fas fa-calendar text-muted"></i> Conta criada:</td>
                            <td class="text-right">{usuario.data_criacao.strftime('%d/%m/%Y')}</td>
                        </tr>
                    </table>
                </div>
                <div class="col-md-6 mb-4">
                    <div class="mb-3">
                        <label class="form-label">Notificações por email</label>
                        <div class="form-check form-switch">
                            <input class="form-check-input" type="checkbox" id="notifications" checked>
                        </div>
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Modo Noturno</label>
                        <div class="form-check form-switch">
                            <input class="form-check-input" type="checkbox" id="darkMode" checked>
                        </div>
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Salvar automaticamente</label>
                        <div class="form-check form-switch">
                            <input class="form-check-input" type="checkbox" id="autoSave" checked>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <div class="card">
        <div class="card-header">
            <h3 class="card-title"><i class="fas fa-database text-blood"></i> Gerenciamento de Dados</h3>
        </div>
        <div class="card-body">
            <div class="row text-center">
                <div class="col-md-4 mb-3">
                    <button class="btn btn-secondary w-100 py-3">
                        <i class="fas fa-download fa-2x mb-2"></i><br>
                        Exportar Dados
                    </button>
                </div>
                <div class="col-md-4 mb-3">
                    <button class="btn btn-secondary w-100 py-3">
                        <i class="fas fa-upload fa-2x mb-2"></i><br>
                        Importar Dados
                    </button>
                </div>
                <div class="col-md-4 mb-3">
                    <button class="btn btn-outline w-100 py-3" 
                            onclick="return confirm('Tem certeza? Esta ação não pode ser desfeita!')">
                        <i class="fas fa-trash fa-2x mb-2"></i><br>
                        Limpar Dados
                    </button>
                </div>
            </div>
        </div>
    </div>
    '''
    
    template = BASE_TEMPLATE.replace('{{ content|safe }}', content)\
                            .replace('{{ navbar|safe }}', create_navbar())\
                            .replace('{{ sidebar|safe }}', criar_menu_lateral(usuario.id))
    
    return render_template_string(template)


@app.route('/relatorio/<tipo>')
def relatorio(tipo):
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
    
    usuario = Usuario.query.get(session['usuario_id'])
    
    content = f'''
    <div class="page-header">
        <div class="page-title">
            <h1><i class="fas fa-chart-bar text-blood"></i> Relatório - {tipo.capitalize()}</h1>
        </div>
        <div class="page-actions">
            <a href="/dashboard" class="btn btn-outline">
                <i class="fas fa-arrow-left"></i> Voltar
            </a>
        </div>
    </div>
    
    <div class="alert alert-info">
        <i class="fas fa-info-circle"></i>
        Funcionalidade de relatórios em desenvolvimento. Em breve você terá gráficos e estatísticas detalhadas.
    </div>
    
    <div class="card">
        <div class="card-body">
            <h5 class="mb-3">Relatório: {tipo.capitalize()}</h5>
            <p class="text-muted">Aqui serão exibidos gráficos e estatísticas detalhadas sobre seus personagens e objetivos.</p>
        </div>
    </div>
    '''
    
    template = BASE_TEMPLATE.replace('{{ content|safe }}', content)\
                            .replace('{{ navbar|safe }}', create_navbar())\
                            .replace('{{ sidebar|safe }}', criar_menu_lateral(usuario.id))
    
    return render_template_string(template)


@app.route('/logout')
def logout():
    session.clear()
    flash('Você saiu do Grimório. Até a próxima criação!', 'success')
    return redirect(url_for('login'))


@app.route('/excluir_personagem/<int:personagem_id>')
def excluir_personagem(personagem_id):
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
    
    personagem = Personagem.query.get_or_404(personagem_id)
    
    if personagem.usuario_id != session['usuario_id']:
        flash('Acesso negado! Este personagem não pertence a você.', 'error')
        return redirect(url_for('dashboard'))
    
    db.session.delete(personagem)
    db.session.commit()
    
    flash(f'Personagem "{personagem.nome}" excluído com sucesso!', 'success')
    return redirect(url_for('listar_personagens'))


@app.route('/excluir_objetivo/<int:objetivo_id>')
def excluir_objetivo(objetivo_id):
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
    
    objetivo = Objetivo.query.get_or_404(objetivo_id)
    personagem = Personagem.query.get(objetivo.personagem_id)
    
    if personagem.usuario_id != session['usuario_id']:
        flash('Acesso negado!', 'error')
        return redirect(url_for('dashboard'))
    
    db.session.delete(objetivo)
    db.session.commit()
    
    flash('Objetivo excluído com sucesso!', 'success')
    return redirect(url_for('detalhes_personagem', personagem_id=personagem.id))


@app.route('/editar_personagem/<int:personagem_id>', methods=['GET', 'POST'])
def editar_personagem(personagem_id):
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
    
    personagem = Personagem.query.get_or_404(personagem_id)
    
    if personagem.usuario_id != session['usuario_id']:
        flash('Acesso negado! Este personagem não pertence a você.', 'error')
        return redirect(url_for('dashboard'))
    
    tipos = ['Personagem', 'NPC', 'Vilão', 'Aliado', 'Criatura', 'Monstro', 'Deus', 'Outro']
    
    if request.method == 'POST':
        personagem.nome = request.form['nome']
        personagem.tipo = request.form['tipo']
        personagem.descricao = request.form.get('descricao', '')
        personagem.prioridade = int(request.form.get('prioridade', 5))
        personagem.historia = request.form.get('historia', '')
        personagem.habilidades = request.form.get('habilidades', '')
        personagem.notas = request.form.get('notas', '')
        personagem.imagem_url = request.form.get('imagem_url', '')
        personagem.tags = request.form.get('tags', '')
        
        db.session.commit()
        
        flash(f'✅ Personagem atualizado! {personagem.nome} foi modificado com sucesso.', 'success')
        return redirect(url_for('detalhes_personagem', personagem_id=personagem.id))
    
    tipos_options = ''.join([f'<option value="{tipo}" {"selected" if personagem.tipo == tipo else ""}>{tipo}</option>' for tipo in tipos])
    
    form_html = f'''
    <div class="page-header">
        <div class="page-title">
            <h1><i class="fas fa-edit text-blood"></i> Editar Personagem</h1>
        </div>
        <div class="page-actions">
            <div class="d-flex gap-2">
                <a href="/detalhes_personagem/{personagem.id}" class="btn btn-secondary">
                    <i class="fas fa-times"></i> Cancelar
                </a>
                <a href="/excluir_personagem/{personagem.id}" class="btn btn-outline" 
                   onclick="return confirmDelete('Tem certeza que deseja excluir {personagem.nome}?')">
                    <i class="fas fa-trash"></i> Excluir
                </a>
            </div>
        </div>
    </div>
    
    {get_flashed_messages_html()}
    
    <form method="POST">
        <div class="card mb-4">
            <div class="card-header">
                <h3 class="card-title"><i class="fas fa-scroll text-blood"></i> Informações Básicas</h3>
            </div>
            <div class="card-body">
                <div class="row">
                    <div class="col-md-6 mb-3">
                        <label class="form-label">Nome do Personagem *</label>
                        <input type="text" class="form-control" name="nome" required 
                               value="{personagem.nome}">
                    </div>
                    <div class="col-md-6 mb-3">
                        <label class="form-label">Tipo *</label>
                        <select class="form-control" name="tipo" required>
                            <option value="">Selecione um tipo</option>
                            {tipos_options}
                        </select>
                    </div>
                </div>
                
                <div class="row">
                    <div class="col-md-6 mb-3">
                        <label class="form-label">Prioridade (1-10)</label>
                        <input type="number" class="form-control" name="prioridade" 
                               min="1" max="10" value="{personagem.prioridade}" id="prioridade"
                               onchange="updatePriorityBars()" onkeyup="updatePriorityBars()">
                        <div class="priority-bar mt-2">
                            <div class="priority-fill" id="prioridade-bar" style="width: {personagem.prioridade * 10}%"></div>
                        </div>
                    </div>
                    <div class="col-md-6 mb-3">
                        <label class="form-label">URL da Imagem</label>
                        <input type="url" class="form-control" name="imagem_url" 
                               value="{personagem.imagem_url or ''}">
                    </div>
                </div>
                
                <div class="mb-3">
                    <label class="form-label">Descrição</label>
                    <textarea class="form-control" name="descricao" rows="3">{personagem.descricao or ''}</textarea>
                </div>
            </div>
        </div>
        
        <div class="card mb-4">
            <div class="card-header">
                <h3 class="card-title"><i class="fas fa-book text-blood"></i> Informações Adicionais</h3>
            </div>
            <div class="card-body">
                <div class="row">
                    <div class="col-md-6 mb-3">
                        <label class="form-label">História/Background</label>
                        <textarea class="form-control" name="historia" rows="4">{personagem.historia or ''}</textarea>
                    </div>
                    <div class="col-md-6 mb-3">
                        <label class="form-label">Habilidades/Talentos</label>
                        <textarea class="form-control" name="habilidades" rows="4">{personagem.habilidades or ''}</textarea>
                    </div>
                </div>
                
                <div class="row">
                    <div class="col-md-6 mb-3">
                        <label class="form-label">Notas Pessoais</label>
                        <textarea class="form-control" name="notas" rows="3">{personagem.notas or ''}</textarea>
                    </div>
                    <div class="col-md-6 mb-3">
                        <label class="form-label">Tags</label>
                        <input type="text" class="form-control" name="tags" 
                               value="{personagem.tags or ''}">
                    </div>
                </div>
            </div>
        </div>
        
        <div class="d-flex justify-content-end gap-2">
            <a href="/detalhes_personagem/{personagem.id}" class="btn btn-secondary">
                <i class="fas fa-times"></i> Cancelar
            </a>
            <button type="submit" class="btn btn-primary">
                <i class="fas fa-save"></i> Salvar Alterações
            </button>
        </div>
    </form>
    '''
    
    template = BASE_TEMPLATE.replace('{{ content|safe }}', form_html)\
                            .replace('{{ navbar|safe }}', create_navbar('personagens'))\
                            .replace('{{ sidebar|safe }}', criar_menu_lateral(session['usuario_id']))
    
    return render_template_string(template)


# =============================================
# INICIALIZAÇÃO
# =============================================

def init_database():
    with app.app_context():
        db.create_all()
        print("=" * 80)
        print("⚔️  GRIMÓRIO BERSERK - Sistema de Anotações de Personagens")
        print("🎨 VERSÃO: Premium - Design Moderno")
        print("📊 SISTEMA: Personagens com prioridades e objetivos")
        print("✨ RECURSOS: Interface aprimorada, animações, design responsivo")
        print("🚀 Iniciando servidor...")
        print("📚 Acesse: http://localhost:5000")
        print("💡 DICA: Use o menu lateral para acesso rápido às funcionalidades!")
        print("=" * 80)


if __name__ == '__main__':
    init_database()
    app.run(debug=True, host='0.0.0.0', port=5000)
