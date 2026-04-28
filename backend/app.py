from flask import Flask, request, jsonify, render_template, send_from_directory
from sqlalchemy import text
from database import engine

app = Flask(__name__, template_folder='../frontend/templates', static_folder='../frontend/static')
#app = Flask(__name__, static_folder='../frontend')#

@app.route('/')
def home():
    #return send_from_directory(app.static_folder, 'index.html')#
    return render_template('index.html')

# Rota para abrir páginas
# @app.route('/')
# def login_page():
#     return send_from_directory(app.static_folder, 'login.html')

@app.route('/login-page')
def login_page():
    #return send_from_directory(app.static_folder, 'login.html')#
    return render_template('login.html')

@app.route('/cadastro')
def cadastro_page():
    #return send_from_directory(app.static_folder, 'cadastro.html')#
    return render_template('cadastro.html')

@app.route("/pergunta")
def pergunta():
    return render_template("pergunta.html")

@app.route('/questionarios')
def questionarios():
    return render_template('questionarios.html')
    #return send_from_directory(app.static_folder, 'questionarios.html')#

# Cadastro
@app.route('/cadastrar', methods=['POST'])
def cadastrar():
    dados = request.json
    nome = dados.get('nome')
    email = dados.get('email')
    senha = dados.get('senha')
    ano_enem = dados.get('ano_enem') 

    try:
        with engine.connect() as conn:
            query = text("""
                INSERT INTO Usuarios (Nome, Email, Senha, Ano_ENEM) 
                VALUES (:nome, :email, :senha, :ano)
            """)
            conn.execute(query, {"nome": nome, "email": email, "senha": senha, "ano": ano_enem})
            conn.commit()
        return jsonify({'status': 'sucesso', 'msg': 'Cadastro realizado com sucesso!'})
    except Exception as e:
        return jsonify({'status': 'erro', 'msg': 'Erro ao cadastrar: E-mail já existe ou falha no banco.'}), 400

# Login
@app.route('/login', methods=['POST'])
def login():
    dados = request.json
    email = dados.get('email')
    senha = dados.get('senha')

    with engine.connect() as conn:
        query = text("SELECT * FROM Usuarios WHERE Email = :email AND Senha = :senha")
        usuario = conn.execute(query, {"email": email, "senha": senha}).fetchone()

        if usuario:
            return jsonify({
                'status': 'sucesso', 
                'nome': usuario.Nome, 
                'msg': f'Bem-vindo, {usuario.Nome}!'
            })

    return jsonify({'status': 'erro', 'msg': 'Usuário ou senha incorretos'}), 401

@app.route('/criar-pergunta', methods=['GET', 'POST'])
def criar_pergunta():
    if request.method == 'POST':
        enunciado = request.form['enunciado']
        ano = request.form.get('ano_enem')

        correta = int(request.form['correta']) - 1

        alternativas = [
            request.form.get('alt1'),
            request.form.get('alt2'),
            request.form.get('alt3'),
            request.form.get('alt4'),
            request.form.get('alt5')
        ]

        explicacao = request.form.get('explicacao') 

        nivel = request.form.get('nivel')

        with engine.begin() as conn:
            result = conn.execute(text("""
                INSERT INTO Questao (Enunciado, Ano_ENEM, Explicacao, ID_Nivel)
                VALUES (:e, :a, :c, :n)
    
            """), {
                "e": enunciado,
                "a": ano,
                "c": explicacao,
                "n": nivel
            })
            id_questao = result.lastrowid

            for i, alt in enumerate(alternativas):
                if alt and alt.strip():
                    conn.execute(text("""
                        INSERT INTO Alternativa 
                        (Texto_Alternativa, Alternativa_Correta, ID_Questao)
                        VALUES (:t, :c, :q)
                    """), {
                        "t": alt,
                        "c": 1 if i == correta else 0,
                        "q": id_questao
                    })

        return "Pergunta salva com sucesso!"

    return render_template('quiz.html')

if __name__ == '__main__':
    app.run(debug=True)
