from sqlalchemy import create_engine, text

user = "root"
password = "" 
host = "localhost"
port = 3306
database = "BIOENEM_BD"

engine = create_engine(
    f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}",
    echo=True
)

with engine.connect() as conn:

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS Categoria (
            ID_Categoria INT AUTO_INCREMENT PRIMARY KEY,
            Nome_categoria VARCHAR(100) NOT NULL
        )
    """))

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS Nivel_dificuldade (
            ID_Nivel INT AUTO_INCREMENT PRIMARY KEY,
            Descricao_nivel VARCHAR(50) NOT NULL
        )
    """))

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS Usuarios (
            ID_Usuario INT AUTO_INCREMENT PRIMARY KEY,
            Nome VARCHAR(500) NOT NULL,
            Email VARCHAR(500) NOT NULL UNIQUE,
            Senha VARCHAR(100) NOT NULL,
            Biografia TEXT,
            Ano_ENEM INT,
            Curso_desejado VARCHAR(200),
            ID_Nivel INT,
            FOREIGN KEY (ID_Nivel) REFERENCES Nivel_dificuldade(ID_Nivel)
        )
    """))

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS Flashcard (
            ID_Flashcard INT AUTO_INCREMENT PRIMARY KEY,
            Pergunta_frente TEXT NOT NULL,
            Pergunta_verso TEXT NOT NULL,
            ID_Usuario INT,
            ID_Categoria INT,
            FOREIGN KEY (ID_Usuario) REFERENCES Usuarios(ID_Usuario),
            FOREIGN KEY (ID_Categoria) REFERENCES Categoria(ID_Categoria)
        )
    """))

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS Quiz (
            ID_Quiz INT AUTO_INCREMENT PRIMARY KEY,
            Titulo VARCHAR(100) NOT NULL,
            ID_Usuario INT,
            ID_Categoria INT,
            FOREIGN KEY (ID_Usuario) REFERENCES Usuarios(ID_Usuario),
            FOREIGN KEY (ID_Categoria) REFERENCES Categoria(ID_Categoria)
        )
    """))

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS Questao (
            ID_Questao INT AUTO_INCREMENT PRIMARY KEY,
            Enunciado TEXT NOT NULL,
            Explicacao TEXT,
            Ano_ENEM TEXT,
            ID_Quiz INT,
            ID_Nivel INT,
            FOREIGN KEY (ID_Quiz) REFERENCES Quiz(ID_Quiz) ON DELETE CASCADE,
            FOREIGN KEY (ID_Nivel) REFERENCES Nivel_dificuldade(ID_Nivel)
        )
    """))

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS Alternativa (
            ID_Alternativa INT AUTO_INCREMENT PRIMARY KEY,
            Texto_Alternativa TEXT NOT NULL,
            Alternativa_Correta TINYINT(1) DEFAULT 0,
            ID_Questao INT,
            FOREIGN KEY (ID_Questao) REFERENCES Questao(ID_Questao) ON DELETE CASCADE
        )
    """))

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS Desempenho_quiz (
            ID_Desempenho INT AUTO_INCREMENT PRIMARY KEY,
            Pontuacao_obtida INT NOT NULL,
            Data_Realizado DATE NOT NULL,
            Tempo_Realizado TIME,
            ID_Usuario INT,
            ID_Quiz INT,
            FOREIGN KEY (ID_Usuario) REFERENCES Usuarios(ID_Usuario),
            FOREIGN KEY (ID_Quiz) REFERENCES Quiz(ID_Quiz)
        )
    """))

    conn.commit()

print("Banco BIOENEM criado")
