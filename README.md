# 🧬 BIOENEM

## 📚 Sobre o projeto

O **BIOENEM** é uma plataforma web voltada para estudantes que estão se preparando para o ENEM, com foco em **Biologia**.

A aplicação reúne recursos para estudar, praticar questões e acompanhar atividades, oferecendo uma experiência de estudo organizada em um único sistema.
---

## 🛠️ Tecnologias utilizadas

### Backend

- Python
- Flask
- SQLAlchemy
- PyMySQL
- Werkzeug
- Flask-Login

### Frontend

- HTML5
- CSS3
- JavaScript

### Banco de dados

- MySQL

---

# 🚀 Como instalar e executar

Antes de iniciar, tenha instalado:

- **Python 3**
- **MySQL Server**
- **MySQL Workbench** (recomendado)
- **Git** (opcional)

Abra o CMD ou PowerShell e entre na pasta principal do projeto:

```cmd
cd C:\caminho\para\BIOENEM-main
```

Dentro da pasta principal do projeto:

```cmd
python -m venv venv
```

No Windows:

```cmd
venv\Scripts\activate
```

Com o ambiente virtual ativado:

```cmd
pip install -r requirements.txt
```
---

# 🗄️ Configuração do banco de dados

O BIOENEM utiliza o banco:

```text
BIOENEM_BD
```

Dentro da pasta:

```text
banco_dados_sql/
```

existem os arquivos:

```text
create_banco
inserts_sql
```

### create_banco

Responsável pela criação do banco e das tabelas utilizadas pelo sistema.

### inserts_sql

Responsável por inserir os dados iniciais utilizados pela aplicação.

---

# 6. Criar o banco no MySQL

Abra o **MySQL Workbench** e conecte-se ao servidor MySQL.

Abra:

```text
banco_dados_sql/create_banco
```

Execute o script.

Depois, abra:

```text
banco_dados_sql/inserts_sql
```

e execute também.

---

# 🔐 Configuração da conexão com o MySQL

A conexão com o banco está localizada em:

```text
backend/database.py
```

Confira as informações de conexão.

---

# ▶️ Executando o projeto

Depois de configurar o banco, entre na pasta:

```cmd
cd backend
```

Execute:

```cmd
python app.py
```

O servidor Flask será iniciado.

Abra o navegador e acesse:

```text
http://localhost:5000
```

---

# 🌐 Principais páginas

| Rota | Função |
|---|---|
| `/` | Página inicial |
| `/login-page` | Login |
| `/cadastro` | Cadastro |
| `/dashboard` | Dashboard |
| `/perfil` | Perfil do usuário |
| `/questionarios` | Questionários |
| `/ranking` | Ranking |
| `/flashcards` | Flashcards |
| `/criar_card` | Criar flashcard |
| `/logout` | Sair da conta |

Algumas páginas exigem que o usuário esteja logado.
