from flask import Flask, request, jsonify, send_from_directory
import json

app = Flask(__name__, static_folder='../frontend')

# Carregar usuários
try:
    with open('items.json', 'r') as f:
        usuarios = json.load(f)
except:
    usuarios = []

# Salvar usuários
def salvar():
    with open('items.json', 'w') as f:
        json.dump(usuarios, f)

# Rota para abrir páginas
@app.route('/')
def login_page():
    return send_from_directory(app.static_folder, 'login.html')

@app.route('/cadastro')
def cadastro_page():
    return send_from_directory(app.static_folder, 'cadastro.html')

# Cadastro
@app.route('/cadastrar', methods=['POST'])
def cadastrar():
    dados = request.json
    usuario = dados['usuario']
    senha = dados['senha']

    for u in usuarios:
        if u['usuario'] == usuario:
            return jsonify({'msg': 'Usuário já existe'})

    usuarios.append({'usuario': usuario, 'senha': senha})
    salvar()

    return jsonify({'msg': 'Cadastro realizado'})

# Login
@app.route('/login', methods=['POST'])
def login():
    dados = request.json
    usuario = dados['usuario']
    senha = dados['senha']

    for u in usuarios:
        if u['usuario'] == usuario and u['senha'] == senha:
            return jsonify({'msg': 'Usuário logado'})

    return jsonify({'msg': 'Usuário ou senha incorretos'})

app.run(debug=True)
