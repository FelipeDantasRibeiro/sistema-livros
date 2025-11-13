# app.py - CÓDIGO SIMPLES PARA TESTE
from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Teste Sistema Livros</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body>
        <div class="container mt-5">
            <div class="row justify-content-center">
                <div class="col-md-6 text-center">
                    <h1 class="text-success">✅ FUNCIONANDO!</h1>
                    <p class="lead">Sistema de Livros - Versão Teste</p>
                    <div class="mt-4">
                        <a href="/login" class="btn btn-primary">Login</a>
                        <a href="/dashboard" class="btn btn-success">Dashboard</a>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    '''

@app.route('/login')
def login():
    return '''
    <div class="container mt-5">
        <div class="row justify-content-center">
            <div class="col-md-4">
                <div class="card">
                    <div class="card-body">
                        <h3 class="text-center">Login</h3>
                        <form>
                            <div class="mb-3">
                                <label>Email</label>
                                <input type="email" class="form-control" placeholder="seu@email.com">
                            </div>
                            <div class="mb-3">
                                <label>Senha</label>
                                <input type="password" class="form-control" placeholder="Sua senha">
                            </div>
                            <button type="submit" class="btn btn-primary w-100">Entrar</button>
                        </form>
                    </div>
                </div>
            </div>
        </div>
    </div>
    '''

@app.route('/dashboard')
def dashboard():
    return '''
    <div class="container mt-4">
        <h1>Dashboard</h1>
        <div class="card">
            <div class="card-body">
                <h5>Sistema funcionando perfeitamente!</h5>
                <p>Total de livros: <strong>0</strong></p>
                <a href="/" class="btn btn-primary">Voltar</a>
            </div>
        </div>
    </div>
    '''

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
