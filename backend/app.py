from flask import Flask, request, jsonify, render_template, send_from_directory, session, redirect, url_for
from sqlalchemy import text
from database import engine
from functools import wraps

app = Flask(__name__, template_folder='../frontend/templates', static_folder='../frontend/static')
app.secret_key = 'bioenem_secret_key'

@app.template_filter('letra_alternativa')
def letra_alternativa(index):
    """Converte índice (0-25) para letra (A-Z)"""
    return chr(65 + index)  # 65 é o código ASCII para 'A'

# Decorator para verificar login
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'usuario_id' not in session:
            return redirect(url_for('login_page'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/login-page')
def login_page():
    return render_template('login.html')

@app.route('/cadastro')
def cadastro_page():
    return render_template('cadastro.html')

@app.route('/dashboard')
@login_required
def dashboard():
    with engine.connect() as conn:
        usuario = conn.execute(text("""
            SELECT Nome, Ano_ENEM, Curso_desejado
            FROM Usuarios
            WHERE ID_Usuario = :id
        """), {"id": session['usuario_id']}).fetchone()
    
    return render_template('dashboard.html', usuario=usuario)

@app.route('/pergunta')
@login_required
def pergunta():
    return render_template('pergunta.html')

@app.route('/questionarios')
@login_required
def questionarios():
    return render_template('questionarios.html')

@app.route('/perfil')
@login_required
def perfil():
    editar = request.args.get('edit') is not None

    with engine.connect() as conn:
        usuario = conn.execute(text("""
            SELECT Nome, Email, Ano_ENEM, Biografia, Curso_desejado
            FROM Usuarios
            WHERE ID_Usuario = :id
        """), {"id": session['usuario_id']}).fetchone()

    return render_template('perfil.html', usuario=usuario, editar=editar)

@app.route('/editar_perfil', methods=['POST'])
@login_required
def editar_perfil():
    ano_enem = request.form.get('ano_enem')
    curso = request.form.get('curso')
    biografia = request.form.get('biografia')

    with engine.connect() as conn:
        conn.execute(text("""
            UPDATE Usuarios
            SET Ano_ENEM = :ano,
                Curso_desejado = :curso,
                Biografia = :bio
            WHERE ID_Usuario = :id
        """), {
            "ano": ano_enem,
            "curso": curso,
            "bio": biografia,
            "id": session['usuario_id']
        })
        conn.commit()

    return redirect(url_for('perfil'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

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
        return jsonify({'status': 'sucesso', 'msg': 'Cadastro realizado com sucesso! Faça login.'})
    except Exception as e:
        return jsonify({'status': 'erro', 'msg': 'Erro ao cadastrar: E-mail já existe ou falha no banco.'}), 400

# Login
@app.route('/login', methods=['POST'])
def login():
    dados = request.json
    email = dados.get('email')
    senha = dados.get('senha')

    with engine.connect() as conn:
        query = text("""
            SELECT ID_Usuario, Nome, Email, Ano_ENEM
            FROM Usuarios
            WHERE Email = :email AND Senha = :senha
        """)
        usuario = conn.execute(query, {
            "email": email,
            "senha": senha
        }).fetchone()

        if usuario:
            session['usuario_id'] = usuario.ID_Usuario
            session['usuario_nome'] = usuario.Nome
            session['usuario_email'] = usuario.Email

            return jsonify({
                'status': 'sucesso',
                'msg': f'Bem-vindo, {usuario.Nome}!'
            })

    return jsonify({'status': 'erro', 'msg': 'Usuário ou senha incorretos'}), 401

# Pergunta
@app.route('/criar-pergunta', methods=['GET', 'POST'])
@login_required
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


# Adicione no app.py

@app.route('/questoes')
@login_required
def listar_questoes():
    with engine.connect() as conn:
        questoes = conn.execute(text("""
            SELECT 
                q.ID_Questao,
                q.Enunciado,
                q.Ano_ENEM,
                q.Explicacao,
                q.Imagem,
                c.Nome_categoria as Categoria,
                n.Descricao_nivel as Nivel
            FROM Questao q
            LEFT JOIN Categoria c ON q.ID_Categoria = c.ID_Categoria
            LEFT JOIN Nivel_dificuldade n ON q.ID_Nivel = n.ID_Nivel
            ORDER BY q.ID_Questao
        """)).fetchall()
        
        questoes_com_alternativas = []
        for questao in questoes:
            alternativas = conn.execute(text("""
                SELECT ID_Alternativa, Texto_Alternativa, Alternativa_Correta, Imagem
                FROM Alternativa
                WHERE ID_Questao = :id
                ORDER BY ID_Alternativa
            """), {"id": questao.ID_Questao}).fetchall()
            
            questoes_com_alternativas.append({
                'questao': {
                    'ID_Questao': questao.ID_Questao,
                    'Enunciado': questao.Enunciado,
                    'Ano_ENEM': questao.Ano_ENEM,
                    'Explicacao': questao.Explicacao,
                    'Imagem': questao.Imagem,
                    'Categoria': questao.Categoria if questao.Categoria else 'Sem categoria',
                    'Nivel': questao.Nivel if questao.Nivel else 'Não definido'
                },
                'alternativas': [{
                    'ID_Alternativa': alt.ID_Alternativa,
                    'Texto_Alternativa': alt.Texto_Alternativa,
                    'Alternativa_Correta': alt.Alternativa_Correta,
                    'Imagem': alt.Imagem  # ← ESSA LINHA É CRUCIAL!
                } for alt in alternativas]
            })
    
    return render_template('questoes.html', questoes=questoes_com_alternativas)
        
if __name__ == '__main__':
    app.run(debug=True)
