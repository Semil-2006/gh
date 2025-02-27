from flask import Flask, request, jsonify, send_file, render_template,g,flash,redirect, url_for,make_response
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
from flask_cors import CORS
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from banco_de_cadastro_colab import Usuario, Base
import os


app = Flask(__name__)
PORT = 8080
DATABASE = 'banco.db'
app.secret_key = 'your_secret_key'
CORS(app)

def get_db():
    if not hasattr(g, 'db_session'):
        engine = create_engine(f'sqlite:///{DATABASE}', echo=True)
        Session = sessionmaker(bind=engine)
        g.db_session = Session()
    return g.db_session

@app.teardown_appcontext
def close_connection(exception):
    db_session = getattr(g, 'db_session', None)
    if db_session:
        db_session.close()

def init_db_usuarios():
    engine = create_engine(f'sqlite:///{DATABASE}', echo=True)
    Base.metadata.create_all(engine)

def init_db_criancas():
    with sqlite3.connect("criancas.db") as conn:
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS criancas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            idade INTEGER NOT NULL,
            responsavel TEXT NOT NULL,
            parentesco TEXT NOT NULL,
            telefone TEXT NOT NULL,
            cidade TEXT NOT NULL,
            turno TEXT NOT NULL,
            data_ingresso TEXT NOT NULL,
            mesma_sala BOOLEAN NOT NULL
        )''')
        conn.commit()

def usuario_logado():
    ultimo_acesso = request.cookies.get('ultimo_acesso')

    if ultimo_acesso:
        ultimo_acesso = datetime.strptime(ultimo_acesso, '%Y-%m-%d %H:%M:%S')

        # Se o usuário acessou nos últimos 7 dias, consideramos que ele está logado
        if datetime.now() - ultimo_acesso < timedelta(days=7):
            return True

    return False


@app.route("/criancas", methods=["GET"])
def get_criancas():
    with sqlite3.connect("criancas.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM criancas")
        criancas = cursor.fetchall()

    keys = [desc[0] for desc in cursor.description]
    result = [dict(zip(keys, row)) for row in criancas]
    return jsonify(result)

@app.route('/chat')
def chat():
    return render_template('chat.html')

@app.route('/')
@app.route('/home')
def index():
    if usuario_logado():
        resposta = make_response(render_template('teste.html'))
        resposta.set_cookie('ultimo_acesso', datetime.now().strftime('%Y-%m-%d %H:%M:%S'), max_age=7 * 24 * 60 * 60)
        return resposta
    return redirect(url_for('login'))



@app.route("/criancas", methods=["POST"])
def add_crianca():
    data = request.json
    with sqlite3.connect("criancas.db") as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO criancas (nome, idade, responsavel, parentesco, telefone, cidade, turno, data_ingresso, mesma_sala)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                       (data["nome"], data["idade"], data["responsavel"], data["parentesco"],
                        data["telefone"], data["cidade"], data["turno"], data["data_ingresso"], data["mesma_sala"])
                       )
        conn.commit()
    return jsonify({"message": "Criança adicionada com sucesso!"}), 201


@app.route("/exportar_excel", methods=["GET"])
def export_excel():
    with sqlite3.connect("criancas.db") as conn:
        df = pd.read_sql_query("SELECT * FROM criancas", conn)

    file_path = os.path.join(os.getcwd(), "lista_criancas.xlsx")  # Salva na pasta do projeto
    df.to_excel(file_path, index=False)
    return send_file(file_path, as_attachment=True)

@app.route("/cadastro", methods=["GET", "POST"])
def cadastro():
    return render_template("cadastro.html")

@app.route('/cadastrar_usuario', methods=['POST'])
def cadastrar_usuario():
    nome = request.form['nome']
    senha = request.form['senha']
    cargo = request.form['cargo']

    if cargo not in ['admin', 'operador', 'professora', 'auxiliar']:
        return "Cargo inválido", 400

    try:
        db_session = get_db()
        novo_usuario = Usuario(nome=nome, senha=senha, funcao=cargo)
        db_session.add(novo_usuario)
        db_session.commit()
        return "Usuário cadastrado com sucesso!"
    except Exception as e:
        db_session.rollback()
        return f"Erro ao cadastrar usuário: {str(e)}", 500



@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        nome_usuario = request.form['username']
        senha_usuario = request.form['password']
        db_session = get_db()
        usuario = db_session.query(Usuario).filter(Usuario.nome == nome_usuario).first()

        if usuario and usuario.senha == senha_usuario:
            resposta = make_response(redirect(url_for('index')))
            resposta.set_cookie('ultimo_acesso', datetime.now().strftime('%Y-%m-%d %H:%M:%S'), max_age=7 * 24 * 60 * 60)
            return resposta
        else:
            flash('Nome de usuário ou senha incorretos', 'danger')

    return render_template('login.html')

@app.route('/logout')
def logout():
    resposta = make_response(redirect(url_for('login')))
    resposta.set_cookie('ultimo_acesso', '', expires=0)
    return resposta

if __name__ == "__main__":
    init_db_usuarios()
    init_db_criancas()
    app.run(port=PORT, debug=True)
    app.run(debug=True, host='0.0.0.0')
