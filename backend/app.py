from flask import Flask, request, jsonify, render_template, send_from_directory, session, redirect, url_for, flash
from werkzeug.utils import secure_filename
import os
from sqlalchemy import text
from database import engine
from functools import wraps
from datetime import date

app = Flask(
    __name__,
    template_folder='../frontend/templates',
    static_folder='../frontend/static'
)

app.secret_key = 'bioenem_secret_key'

UPLOAD_FOLDER = os.path.join(app.static_folder, 'uploads')

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
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
    with engine.connect() as conn:
        categorias = conn.execute(text("""
            SELECT *
            FROM Categoria
        """)).fetchall()

        niveis = conn.execute(text("""
            SELECT *
            FROM Nivel_dificuldade
        """)).fetchall()

        query_quizzes = text("""
            SELECT
                q.ID_Quiz,
                q.Titulo,
                c.Nome_categoria,
                n.Descricao_nivel,
                COUNT(que.ID_Questao) AS Total_Questoes
            FROM Quiz q
            JOIN Categoria c
                ON q.ID_Categoria = c.ID_Categoria
            JOIN Nivel_dificuldade n
                ON q.ID_Nivel = n.ID_Nivel
            LEFT JOIN Questao que
                ON q.ID_Quiz = que.ID_Quiz
            GROUP BY
                q.ID_Quiz,
                q.Titulo,
                c.Nome_categoria,
                n.Descricao_nivel
            ORDER BY q.ID_Quiz DESC
        """)

        lista_quizzes = conn.execute(query_quizzes).fetchall()

    return render_template(
        "questionarios.html",
        categorias=categorias,
        niveis=niveis,
        quizzes=lista_quizzes
    )

@app.route('/perfil')
def perfil():

    if 'usuario_id' not in session:
        return redirect(url_for('login_page'))

    editar = request.args.get('edit') == '1'

    id_usuario = session['usuario_id']

    with engine.connect() as conn:

        usuario = conn.execute(text("""
            SELECT Nome, Email, Ano_ENEM, Biografia, Curso_desejado, Foto_perfil
            FROM Usuarios
            WHERE ID_Usuario = :id
        """), {"id": id_usuario}).fetchone()

        quizzes = conn.execute(text("""
            SELECT COUNT(*) AS total
            FROM Desempenho_quiz
            WHERE ID_Usuario = :id
        """), {
            "id": id_usuario
        }).fetchone()

        media = conn.execute(text("""
            SELECT COALESCE(
                AVG(
                    (d.Pontuacao_obtida / q.total_questoes) * 100
                ),
                0
            ) AS media
            FROM Desempenho_quiz d
            JOIN (
                SELECT ID_Quiz, COUNT(*) AS total_questoes
                FROM Questao
                GROUP BY ID_Quiz
            ) q ON q.ID_Quiz = d.ID_Quiz
            WHERE d.ID_Usuario = :id
        """), {
            "id": id_usuario
        }).fetchone()

        pontuacao = conn.execute(text("""
            SELECT COALESCE(SUM(Pontuacao_obtida), 0) AS total
            FROM Desempenho_quiz
            WHERE ID_Usuario = :id
        """), {
            "id": id_usuario
        }).fetchone()

        flashcards = conn.execute(text("""
            SELECT COUNT(*) AS total
            FROM Flashcard
            WHERE ID_Usuario = :id
        """), {
            "id": id_usuario
        }).fetchone()

        ranking = conn.execute(text("""
            SELECT posicao
            FROM (
                SELECT
                    u.ID_Usuario,
                    ROW_NUMBER() OVER (
                        ORDER BY
                            COALESCE(SUM(d.Pontuacao_obtida), 0) DESC,
                            COUNT(d.ID_Desempenho) DESC,
                            u.ID_Usuario ASC
                    ) AS posicao
                FROM Usuarios u
                LEFT JOIN Desempenho_quiz d
                    ON d.ID_Usuario = u.ID_Usuario
                GROUP BY u.ID_Usuario
            ) AS ranking
            WHERE ID_Usuario = :id
        """), {
            "id": id_usuario
        }).fetchone()

        atividades = conn.execute(text("""
            SELECT
                q.Titulo AS nome,
                d.Data_Realizado AS data,
                d.Pontuacao_obtida AS acertos,
                total.total_questoes AS total,
                (d.Pontuacao_obtida / total.total_questoes) * 100 AS porcentagem
            FROM Desempenho_quiz d
            JOIN Quiz q
                ON q.ID_Quiz = d.ID_Quiz
            JOIN (
                SELECT
                    ID_Quiz,
                    COUNT(*) AS total_questoes
                FROM Questao
                GROUP BY ID_Quiz
            ) total
                ON total.ID_Quiz = d.ID_Quiz
            WHERE d.ID_Usuario = :id
            ORDER BY d.Data_Realizado DESC
            LIMIT 5
        """), {
            "id": id_usuario
        }).fetchall()

    return render_template(
        'perfil.html',
        usuario=usuario,
        editar=editar,
        quizzes=quizzes.total,
        media=media.media,
        pontuacao=pontuacao.total,
        flashcards=flashcards.total,
        ranking=ranking.posicao if ranking else 0,
        atividades=atividades
    )

@app.route('/editar_perfil', methods=['POST'])
def editar_perfil():

    if 'usuario_id' not in session:
        return redirect(url_for('login_page'))

    ano_enem = request.form.get('ano_enem')
    curso = request.form.get('curso')
    biografia = request.form.get('biografia')

    foto = request.files.get('foto_perfil')

    foto_nome = None

    if foto and foto.filename:

        nome_seguro = secure_filename(foto.filename)

        foto_nome = str(session['usuario_id']) + "_" + nome_seguro

        caminho = os.path.join(
            app.config['UPLOAD_FOLDER'],
            foto_nome
        )

        foto.save(caminho)

    with engine.connect() as conn:

        if foto_nome:

            conn.execute(text("""
                UPDATE Usuarios
                SET Ano_ENEM = :ano,
                    Curso_desejado = :curso,
                    Biografia = :bio,
                    Foto_perfil = :foto
                WHERE ID_Usuario = :id
            """), {
                "ano": ano_enem,
                "curso": curso,
                "bio": biografia,
                "foto": foto_nome,
                "id": session['usuario_id']
            })

        else:

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

def classe_usuario(pontos):
    """Converte a pontuação total em uma classe/nível do usuário."""
    if pontos >= 300:
        return "Expert"
    if pontos >= 200:
        return "Avançado"
    if pontos >= 100:
        return "Intermediário"
    return "Iniciante"

@app.route('/ranking')
@login_required
def ranking():
    with engine.connect() as conn:
        resultado = conn.execute(text("""
        SELECT
            u.ID_Usuario,
            u.Nome,
            u.Foto_perfil,
            COALESCE(SUM(d.Pontuacao_obtida), 0) AS Pontos,
            COUNT(d.ID_Desempenho) AS Quizzes
        FROM Usuarios u
        LEFT JOIN Desempenho_quiz d
            ON d.ID_Usuario = u.ID_Usuario
        GROUP BY u.ID_Usuario, u.Nome, u.Foto_perfil
        ORDER BY Pontos DESC, Quizzes DESC, u.ID_Usuario ASC
    """)).fetchall()

    classificacao = []
    for posicao, linha in enumerate(resultado, start=1):
        partes_nome = linha.Nome.split() if linha.Nome else []
        iniciais = "".join(p[0] for p in partes_nome[:2]).upper() or "?"

        classificacao.append({
            "posicao": posicao,
            "id_usuario": linha.ID_Usuario,
            "nome": linha.Nome,
            "foto": linha.Foto_perfil,
            "pontos": linha.Pontos,
            "classe": classe_usuario(linha.Pontos),
            "iniciais": iniciais
        })

    podio = classificacao[:3]
    demais = classificacao[3:]

    podio_exibicao = []
    if len(podio) >= 2:
        podio_exibicao.append(podio[1])
    if len(podio) >= 1:
        podio_exibicao.append(podio[0])
    if len(podio) >= 3:
        podio_exibicao.append(podio[2])

    return render_template(
        "ranking.html",
        podio=podio_exibicao,
        demais=demais,
        usuario_atual=session.get("usuario_id"),
        tem_dados=len(classificacao) > 0
    )

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

@app.route('/gerar-quiz', methods=['GET', 'POST'])
@login_required
def gerar_quiz():
    with engine.connect() as conn:
        if request.method == "POST":
            cat_id = request.form.get("categoria_id")
            niv_id = request.form.get("nivel_id")
            usuario_id = session["usuario_id"]

            quantidade = conn.execute(text("""
                SELECT COUNT(*) AS total
                FROM Questao
                WHERE ID_Categoria = :categoria
                AND ID_Nivel = :nivel
                AND ID_Quiz IS NULL
            """), {
                "categoria": cat_id,
                "nivel": niv_id
            }).fetchone()

            if quantidade.total == 0:
                categorias = conn.execute(text("""
                    SELECT *
                    FROM Categoria
                    ORDER BY Nome_categoria
                """)).fetchall()

                niveis = conn.execute(text("""
                    SELECT *
                    FROM Nivel_dificuldade
                    ORDER BY ID_Nivel
                """)).fetchall()

                return render_template(
                    "gerar_quiz.html",
                    categorias=categorias,
                    niveis=niveis,
                    erro="Não existem questões disponíveis para essa categoria e nível."
                )

            categoria = conn.execute(text("""
                SELECT Nome_categoria
                FROM Categoria
                WHERE ID_Categoria = :id
            """), {"id": cat_id}).fetchone()

            titulo_novo = categoria.Nome_categoria

            result = conn.execute(text("""
                INSERT INTO Quiz
                (Titulo, ID_Usuario, ID_Categoria, ID_Nivel)
                VALUES
                (:titulo, :usuario, :categoria, :nivel)
            """), {
                "titulo": titulo_novo,
                "usuario": usuario_id,
                "categoria": cat_id,
                "nivel": niv_id
            })

            novo_id_quiz = result.lastrowid

            conn.execute(text("""
                UPDATE Questao
                SET ID_Quiz = :quiz
                WHERE ID_Categoria = :categoria
                AND ID_Nivel = :nivel
                ORDER BY RAND()
                LIMIT 5
            """), {
                "quiz": novo_id_quiz,
                "categoria": cat_id,
                "nivel": niv_id
            })

            conn.commit()

            return redirect(url_for(
                "quiz",
                id_quiz=novo_id_quiz,
                numero=1
            ))

        categorias = conn.execute(text("""
            SELECT *
            FROM Categoria
            ORDER BY Nome_categoria
        """)).fetchall()

        niveis = conn.execute(text("""
            SELECT *
            FROM Nivel_dificuldade
            ORDER BY ID_Nivel
        """)).fetchall()

    return render_template(
        "gerar_quiz.html",
        categorias=categorias,
        niveis=niveis
    )

@app.route('/iniciar-quiz/<int:id_quiz>')
@login_required
def iniciar_quiz(id_quiz):
    session.pop("respostas", None)

    return redirect(url_for(
        "quiz",
        id_quiz=id_quiz,
        numero=1
    ))

@app.route("/quiz/<int:id_quiz>/<int:numero>", methods=["GET", "POST"])
@login_required
def quiz(id_quiz, numero):
    with engine.connect() as conn:
        questoes = conn.execute(text("""
            SELECT
                ID_Questao,
                Enunciado,
                Explicacao,
                Imagem
            FROM Questao
            WHERE ID_Quiz = :quiz
            ORDER BY ID_Questao
        """), {"quiz": id_quiz}).fetchall()

        total = len(questoes)
        if total == 0:
            return "Nenhuma questão encontrada."
        
        if numero < 1 or numero > total:
            return redirect(url_for(
                "quiz",
                id_quiz=id_quiz,
                numero=1
            ))

        questao = questoes[numero - 1]

        if request.method == "POST":
            alternativa = request.form.get("resposta")
            if alternativa:
                if "respostas" not in session:
                    session["respostas"] = {}

                respostas = session["respostas"]
                respostas[str(numero)] = alternativa
                session["respostas"] = respostas

            if numero < total:
                return redirect(url_for(
                    "quiz",
                    id_quiz=id_quiz,
                    numero=numero + 1
                ))

            return redirect(url_for(
                "resultado_quiz",
                id_quiz=id_quiz
            ))

        alternativas = conn.execute(text("""
            SELECT
                ID_Alternativa,
                Texto_Alternativa,
                Alternativa_Correta
            FROM Alternativa
            WHERE ID_Questao = :id
            ORDER BY ID_Alternativa
        """), {
            "id": questao.ID_Questao
        }).fetchall()

    return render_template(
        "pergunta.html",
        questao=questao,
        alternativas=alternativas,
        numero=numero,
        total=total,
        id_quiz=id_quiz
    )

@app.route("/resultado-quiz/<int:id_quiz>")
@login_required
def resultado_quiz(id_quiz):

    respostas = session.get("respostas", {})
    acertos = 0

    with engine.connect() as conn:
        questoes = conn.execute(text("""
            SELECT
                ID_Questao
            FROM Questao
            WHERE ID_Quiz = :quiz
            ORDER BY ID_Questao
        """), {
            "quiz": id_quiz
        }).fetchall()

        total = len(questoes)

        for indice, questao in enumerate(questoes, start=1):
            resposta_usuario = respostas.get(str(indice))

            if resposta_usuario is None:
                continue
            
            correta = conn.execute(text("""
                SELECT ID_Alternativa
                FROM Alternativa
                WHERE ID_Questao = :questao
                AND Alternativa_Correta = 1
            """), {
                "questao": questao.ID_Questao
            }).fetchone()

            if correta and str(correta.ID_Alternativa) == resposta_usuario:
                acertos += 1

    porcentagem = round((acertos / total) * 100) if total > 0 else 0

    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO Desempenho_quiz
            (
                Pontuacao_obtida,
                Data_Realizado,
                Tempo_Realizado,
                ID_Usuario,
                ID_Quiz
            )
            VALUES
            (
                :pontuacao,
                :data,
                NULL,
                :usuario,
                :quiz
            )
        """), {
            "pontuacao": acertos,
            "data": date.today(),
            "usuario": session["usuario_id"],
            "quiz": id_quiz
        })

    session["ultimo_desempenho"] = {
        "respostas": respostas
    }

    return render_template(
        "resultado_quiz.html",
        acertos=acertos,
        total=total,
        porcentagem=porcentagem,
        id_quiz=id_quiz
    )

@app.route("/correcao-quiz/<int:id_quiz>")
@login_required
def correcao_quiz(id_quiz):
    desempenho = session.get("ultimo_desempenho")

    if not desempenho:
        return redirect(url_for("questionarios"))

    respostas = desempenho["respostas"]
    correcao = []

    with engine.connect() as conn:
        questoes = conn.execute(text("""
            SELECT
                ID_Questao,
                Enunciado,
                Explicacao
            FROM Questao
            WHERE ID_Quiz = :quiz
            ORDER BY ID_Questao
        """), {
            "quiz": id_quiz
        }).fetchall()

        for indice, questao in enumerate(questoes, start=1):
            alternativas_db = conn.execute(text("""
                SELECT
                    ID_Alternativa,
                    Texto_Alternativa,
                    Alternativa_Correta
                FROM Alternativa
                WHERE ID_Questao = :questao
                ORDER BY ID_Alternativa
            """), {
                "questao": questao.ID_Questao
            }).fetchall()

            resposta_usuario = respostas.get(str(indice))
            resposta_correta = None
            acertou = False

            alternativas = []

            for alt in alternativas_db:
                alternativas.append({
                    "ID_Alternativa": alt.ID_Alternativa,
                    "Texto_Alternativa": alt.Texto_Alternativa,
                    "Alternativa_Correta": alt.Alternativa_Correta
                })

                if alt.Alternativa_Correta:
                    resposta_correta = alt.ID_Alternativa

            if resposta_usuario is not None:
                acertou = str(resposta_correta) == str(resposta_usuario)

            correcao.append({
                "numero": indice,
                "enunciado": questao.Enunciado,
                "explicacao": questao.Explicacao,
                "alternativas": alternativas,
                "resposta_usuario": resposta_usuario,
                "resposta_correta": resposta_correta,
                "acertou": acertou
            })

    session.pop("ultimo_desempenho", None)
    session.pop("respostas", None)

    return render_template(
        "correcao_quiz.html",
        correcao=correcao,
        id_quiz=id_quiz
    )

@app.route('/criar_card')
@login_required
def criar_card_compat():
    """Rota antiga mantida apenas para compatibilidade com links antigos."""
    return redirect(url_for("criar_lista_flashcards"))

@app.route('/flashcards/criar', methods=['GET', 'POST'])
@login_required
def criar_lista_flashcards():
    with engine.connect() as conn:
        categorias = conn.execute(text("""
            SELECT ID_Categoria, Nome_categoria
            FROM Categoria
            ORDER BY Nome_categoria
        """)).fetchall()

    if request.method == 'POST':
        titulo = request.form.get('titulo', '').strip()
        categoria = request.form.get('id_categoria') or None
        frentes = request.form.getlist('pergunta_frente[]')
        versos = request.form.getlist('pergunta_verso[]')

        pares = [
            (frente.strip(), verso.strip())
            for frente, verso in zip(frentes, versos)
            if frente.strip() and verso.strip()
        ]

        if not titulo:
            flash('Informe um título para a lista.', 'error')
        elif not pares:
            flash('Adicione pelo menos um flashcard completo.', 'error')
        else:
            with engine.begin() as conn:
                result = conn.execute(text("""
                    INSERT INTO FlashcardLista (Titulo, ID_Usuario, ID_Categoria)
                    VALUES (:titulo, :usuario, :categoria)
                """), {
                    'titulo': titulo,
                    'usuario': session['usuario_id'],
                    'categoria': categoria
                })
                lista_id = result.lastrowid

                for frente, verso in pares:
                    conn.execute(text("""
                        INSERT INTO Flashcard
                        (Pergunta_frente, Pergunta_verso, ID_Usuario, ID_Categoria, ID_Lista)
                        VALUES (:frente, :verso, :usuario, :categoria, :lista)
                    """), {
                        'frente': frente,
                        'verso': verso,
                        'usuario': session['usuario_id'],
                        'categoria': categoria,
                        'lista': lista_id
                    })

            return redirect(url_for('flashcards'))

    return render_template('form_flashcard.html', categorias=categorias, lista=None, cards=[])

@app.route('/flashcards/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_lista_flashcards(id):
    with engine.connect() as conn:
        lista = conn.execute(text("""
            SELECT ID_Lista, Titulo, ID_Categoria
            FROM FlashcardLista
            WHERE ID_Lista=:id AND ID_Usuario=:usuario
        """), {'id': id, 'usuario': session['usuario_id']}).fetchone()

        if not lista:
            flash('Lista de flashcards não encontrada.', 'error')
            return redirect(url_for('flashcards'))

        categorias = conn.execute(text("""
            SELECT ID_Categoria, Nome_categoria
            FROM Categoria
            ORDER BY Nome_categoria
        """)).fetchall()

        cards = conn.execute(text("""
            SELECT ID_Flashcard, Pergunta_frente, Pergunta_verso
            FROM Flashcard
            WHERE ID_Lista=:lista AND ID_Usuario=:usuario
            ORDER BY ID_Flashcard
        """), {'lista': id, 'usuario': session['usuario_id']}).fetchall()

    if request.method == 'POST':
        titulo = request.form.get('titulo', '').strip()
        categoria = request.form.get('id_categoria') or None
        ids = request.form.getlist('card_id[]')
        frentes = request.form.getlist('pergunta_frente[]')
        versos = request.form.getlist('pergunta_verso[]')

        pares = [
            (card_id, frente.strip(), verso.strip())
            for card_id, frente, verso in zip(ids, frentes, versos)
            if frente.strip() and verso.strip()
        ]

        if not titulo:
            flash('Informe um título para a lista.', 'error')
        elif not pares:
            flash('A lista precisa ter pelo menos um flashcard completo.', 'error')
        else:
            with engine.begin() as conn:
                conn.execute(text("""
                    UPDATE FlashcardLista
                    SET Titulo=:titulo, ID_Categoria=:categoria
                    WHERE ID_Lista=:lista AND ID_Usuario=:usuario
                """), {
                    'titulo': titulo,
                    'categoria': categoria,
                    'lista': id,
                    'usuario': session['usuario_id']
                })

                existing_ids = []
                for card_id, frente, verso in pares:
                    if card_id:
                        result = conn.execute(text("""
                            UPDATE Flashcard
                            SET Pergunta_frente=:frente,
                                Pergunta_verso=:verso,
                                ID_Categoria=:categoria
                            WHERE ID_Flashcard=:card
                              AND ID_Lista=:lista
                              AND ID_Usuario=:usuario
                        """), {
                            'frente': frente,
                            'verso': verso,
                            'categoria': categoria,
                            'card': card_id,
                            'lista': id,
                            'usuario': session['usuario_id']
                        })
                        if result.rowcount:
                            existing_ids.append(int(card_id))
                    else:
                        result = conn.execute(text("""
                            INSERT INTO Flashcard
                            (Pergunta_frente, Pergunta_verso, ID_Usuario, ID_Categoria, ID_Lista)
                            VALUES (:frente, :verso, :usuario, :categoria, :lista)
                        """), {
                            'frente': frente,
                            'verso': verso,
                            'usuario': session['usuario_id'],
                            'categoria': categoria,
                            'lista': id
                        })
                        existing_ids.append(result.lastrowid)

                if existing_ids:
                    placeholders = ','.join(str(x) for x in existing_ids)
                    conn.execute(text(f"""
                        DELETE FROM Flashcard
                        WHERE ID_Lista=:lista
                          AND ID_Usuario=:usuario
                          AND ID_Flashcard NOT IN ({placeholders})
                    """), {'lista': id, 'usuario': session['usuario_id']})

            return redirect(url_for('flashcards'))

    return render_template('form_flashcard.html', categorias=categorias, lista=lista, cards=cards)

@app.route('/flashcards/excluir/<int:id>', methods=['POST'])
@login_required
def excluir_lista_flashcards(id):
    with engine.begin() as conn:
        conn.execute(text("""
            DELETE FROM FlashcardLista
            WHERE ID_Lista=:lista AND ID_Usuario=:usuario
        """), {'lista': id, 'usuario': session['usuario_id']})

    return redirect(url_for('flashcards'))

@app.route('/flashcards/card/excluir/<int:id>', methods=['POST'])
@login_required
def excluir_card_flashcard(id):
    with engine.begin() as conn:
        lista = conn.execute(text("""
            SELECT ID_Lista FROM Flashcard
            WHERE ID_Flashcard=:card AND ID_Usuario=:usuario
        """), {'card': id, 'usuario': session['usuario_id']}).fetchone()

        if lista:
            conn.execute(text("""
                DELETE FROM Flashcard
                WHERE ID_Flashcard=:card AND ID_Usuario=:usuario
            """), {'card': id, 'usuario': session['usuario_id']})
            return redirect(url_for('editar_lista_flashcards', id=lista.ID_Lista))
        
    return redirect(url_for('flashcards'))

@app.route('/flashcards')
@login_required
def flashcards():
    with engine.connect() as conn:
        listas = conn.execute(text("""
            SELECT
                L.ID_Lista,
                L.Titulo,
                C.Nome_categoria AS Categoria,
                COUNT(F.ID_Flashcard) AS Quantidade
            FROM FlashcardLista L
            LEFT JOIN Categoria C ON L.ID_Categoria=C.ID_Categoria
            LEFT JOIN Flashcard F ON F.ID_Lista=L.ID_Lista
            WHERE L.ID_Usuario=:usuario
            GROUP BY L.ID_Lista, L.Titulo, C.Nome_categoria
            ORDER BY L.ID_Lista DESC
        """), {'usuario': session['usuario_id']}).fetchall()

    return render_template('flashcards.html', listas=listas)

@app.route('/flashcards/<int:id>')
@login_required
def estudar_flashcards(id):
    with engine.connect() as conn:
        lista = conn.execute(text("""
            SELECT L.ID_Lista, L.Titulo, C.Nome_categoria AS Categoria
            FROM FlashcardLista L
            LEFT JOIN Categoria C ON L.ID_Categoria=C.ID_Categoria
            WHERE L.ID_Lista=:lista AND L.ID_Usuario=:usuario
        """), {'lista': id, 'usuario': session['usuario_id']}).fetchone()

        if not lista:
            flash('Lista de flashcards não encontrada.', 'error')
            return redirect(url_for('flashcards'))

        cards = conn.execute(text("""
            SELECT ID_Flashcard, Pergunta_frente, Pergunta_verso
            FROM Flashcard
            WHERE ID_Lista=:lista AND ID_Usuario=:usuario
            ORDER BY ID_Flashcard
        """), {'lista': id, 'usuario': session['usuario_id']}).fetchall()

    return render_template('estudar_flashcards.html', lista=lista, cards=cards)
        
if __name__ == '__main__':
    app.run(debug=True)
