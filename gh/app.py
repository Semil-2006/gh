from flask import Flask,send_file, request, redirect, make_response, render_template, g,jsonify
from flask_cors import CORS
import sqlite3
import datetime
import pandas as pd
from io import BytesIO
import os

app = Flask(__name__)
app.secret_key = 'chave_secreta'
DATABASE_CRIANCAS = "criancas.db"
DATABASE_RESPONSAVEIS = "responsaveis.db"
DATABASE_USUARIOS = "usuarios.db"
CORS(app)
def get_db(database):
    conn = sqlite3.connect(database)
    conn.row_factory = sqlite3.Row 
    return conn


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()

def init_db():
    # Criando a tabela 'criancas'
    with sqlite3.connect(DATABASE_CRIANCAS) as db:
        db.execute('''CREATE TABLE IF NOT EXISTS criancas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT,
            idade INTEGER,
            escola TEXT,
            responsavel_id INTEGER,  -- Chave estrangeira
            telefone TEXT,
            cidade TEXT,
            turno TEXT,
            data TEXT,
            foto TEXT,
            entregue TEXT DEFAULT 'Ainda não entregue',
            observacoes TEXT,
            FOREIGN KEY (responsavel_id) REFERENCES responsaveis(id) ON DELETE CASCADE
        )''')

        db.execute('''CREATE TABLE IF NOT EXISTS presencas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            crianca_id INTEGER,
            data TEXT,
            turno TEXT,
            entregue TEXT DEFAULT 'Ainda não entregue',
            FOREIGN KEY (crianca_id) REFERENCES criancas(id) ON DELETE CASCADE
        )''')

    # Criando a tabela 'responsaveis'
    with sqlite3.connect(DATABASE_RESPONSAVEIS) as db:
        db.execute('''CREATE TABLE IF NOT EXISTS responsaveis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT,
            quantidade_filhos INTEGER,
            filhos TEXT,
            telefone TEXT,
            cidade TEXT,
            primeira_visita TEXT
        )''')

    # Criando a tabela 'usuarios'
    with sqlite3.connect(DATABASE_USUARIOS) as db:
        db.execute('''CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            cargo TEXT NOT NULL,
            senha TEXT NOT NULL
        )''')

    # Criando a tabela 'presencas' para registrar as presenças das crianças


@app.route('/')
def formulario():
    usuario = request.cookies.get('usuario')
    if usuario:
        return render_template('index.html')
    return render_template('login.html')

@app.route('/cadastro')
def cadastro():
    return render_template('cadastro.html')

@app.route('/cadastrar', methods=['POST'])
def cadastrar():
    nome = request.form.get('nome', '')
    cargo = request.form.get('cargo', '')
    senha = request.form.get('senha', '')
    if not nome or not cargo or not senha:
        return "Preencha todos os campos!"
    
    conn = sqlite3.connect(DATABASE_USUARIOS)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO usuarios (nome, cargo, senha) VALUES (?, ?, ?)', (nome, cargo, senha))
    conn.commit()
    conn.close()
    
    return redirect('/')

@app.route('/login', methods=['POST'])
def login():
    usuario = request.form.get('usuario', '')
    senha = request.form.get('senha', '')
    
    conn = sqlite3.connect(DATABASE_USUARIOS)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM usuarios WHERE nome = ? AND senha = ?", (usuario, senha))
    user = cursor.fetchone()
    conn.close()
    
    if user:
        resp = make_response(redirect('/'))
        expira = datetime.datetime.utcnow() + datetime.timedelta(days=7)
        resp.set_cookie('usuario', usuario, expires=expira, path='/')
        return resp
    else:
        return "Usuário ou senha incorretos. <a href='/'>Tentar novamente</a>"

from flask import Flask, render_template, request, redirect, flash, url_for

@app.route("/crianca_cadastro", methods=["GET", "POST"])
# @app.route("/", methods=["GET", "POST"])
def cadastro_crianca():
    if request.method == "POST":
        nome_crianca = request.form.get("nome_crianca", "")
        idade_crianca = request.form.get("idade_crianca", "")
        escola = request.form.get("escola", "")
        nome_responsavel = request.form.get("nome_responsavel", "")
        telefone_responsavel = request.form.get("telefone_responsavel", "")
        cidade_responsavel = request.form.get("cidade_responsavel", "")
        turno = request.form.get("turno", "")
        data_visita = request.form.get("data_visita", "")
        foto = request.files.get("foto")
        mais_filhos = request.form.get("mais_filhos", "nao")
        quantidade_filhos = request.form.get("quantidade_filhos", "")

        if quantidade_filhos.isdigit():
            quantidade_filhos = int(quantidade_filhos)
        else:
            quantidade_filhos = 0

        filhos_nomes = [nome_crianca]  # O primeiro filho também deve ser registrado

        try:
            db_resp = get_db(DATABASE_RESPONSAVEIS)
            db_resp.execute(
                "INSERT INTO responsaveis (nome, telefone, cidade, primeira_visita) VALUES (?, ?, ?, ?)",
                (nome_responsavel, telefone_responsavel, cidade_responsavel, data_visita)
            )
            db_resp.commit()
            responsavel_id = db_resp.execute("SELECT last_insert_rowid()").fetchone()[0]

            db = get_db(DATABASE_CRIANCAS)
            
            # Inserir o primeiro filho
            db.execute("""
                INSERT INTO criancas (nome, idade, escola, responsavel_id, telefone, cidade, turno, data, foto)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (nome_crianca, idade_crianca, escola, responsavel_id, telefone_responsavel, cidade_responsavel, turno, data_visita, foto.filename if foto else None))
            db.commit()

            if mais_filhos == "sim":
                for i in range(1, quantidade_filhos + 1):
                    nome_filho = request.form.get(f"nome_filho_{i}", "")
                    idade_filho = request.form.get(f"idade_filho_{i}", "")
                    filhos_nomes.append(nome_filho)

                    db.execute("""
                        INSERT INTO criancas (nome, idade, escola, responsavel_id, telefone, cidade, turno, data, foto)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (nome_filho, idade_filho, escola, responsavel_id, telefone_responsavel, cidade_responsavel, turno, data_visita, foto.filename if foto else None))
                    db.commit()

            db_resp.execute("""
                UPDATE responsaveis SET quantidade_filhos = ?, filhos = ? WHERE id = ?
            """, (len(filhos_nomes), ", ".join(filhos_nomes), responsavel_id))
            db_resp.commit()

            flash("Cadastro realizado com sucesso!", "success")
        except Exception as e:
            flash(f"Erro ao cadastrar: {str(e)}", "error")

        return redirect(url_for("cadastro_crianca"))

    return render_template("index.html")
@app.route('/responsaveis', methods=['GET'])
def responsaveis():
    nome_responsavel = request.args.get('responsavel', '')
    escola = request.args.get('escola', '')

    # Query para buscar responsáveis no banco 'responsaveis.db' com o filtro do nome
    query_responsaveis = """
        SELECT r.id, r.nome, r.telefone, r.quantidade_filhos
        FROM responsaveis r
        WHERE r.nome LIKE ?
    """
    
    nome_responsavel = f"{nome_responsavel}%"  # Adiciona o filtro LIKE para o nome
    db_resp = get_db(DATABASE_RESPONSAVEIS)
    responsaveis = db_resp.execute(query_responsaveis, (nome_responsavel,)).fetchall()

    filtered_responsaveis = []
    if escola:
        # Se houver filtro de escola, procuramos também nas crianças no banco 'criancas.db'
        db_criancas = get_db(DATABASE_CRIANCAS)
        for responsavel in responsaveis:
            query_criancas = """
                SELECT c.id FROM criancas c
                WHERE c.responsavel_id = ? AND c.escola LIKE ?
            """
            escola = f"{escola}%"  # Adiciona o filtro LIKE para a escola
            criancas = db_criancas.execute(query_criancas, (responsavel['id'], escola)).fetchall()

            if criancas:
                responsavel_dict = dict(responsavel)  # Converte o Row para dict
                responsavel_dict['criancas'] = [dict(crianca) for crianca in criancas]
                filtered_responsaveis.append(responsavel_dict)

    else:
        # Se não houver filtro de escola, apenas adiciona os responsáveis encontrados
        for responsavel in responsaveis:
            responsavel_dict = dict(responsavel)  # Converte o Row para dict
            filtered_responsaveis.append(responsavel_dict)

    # Verificar se é uma requisição AJAX (requisição assíncrona)
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify(filtered_responsaveis)

    # Caso contrário, renderizamos a página com os dados
    return render_template('responsaveis.html', responsaveis=filtered_responsaveis)


@app.route('/responsaveis/<int:id>', methods=['GET'])
@app.route('/gula', methods=['GET'])
def detalhes_responsavel(id):
    db_resp = get_db(DATABASE_RESPONSAVEIS)
    
    query_responsavel = """
    SELECT r.id, r.nome, r.telefone, r.quantidade_filhos
    FROM responsaveis r
    WHERE r.id = ?
    """
    responsavel = db_resp.execute(query_responsavel, (id,)).fetchone()

    if responsavel:
        db_criancas = get_db(DATABASE_CRIANCAS)
        query_criancas = """
            SELECT c.id, c.nome, c.idade, c.escola, c.entregue
            FROM criancas c
            WHERE c.responsavel_id = ?
        """
        criancas = db_criancas.execute(query_criancas, (id,)).fetchall()

        return render_template('responsavel_detalhes.html', responsavel=responsavel, criancas=criancas)
    else:
        return "Responsável não encontrado", 404


@app.route('/atualizar_entregue', methods=['POST'])
def atualizar_entregue():
    data = request.get_json()

    # Debug: Verifique o que foi enviado
    print("=== DADOS RECEBIDOS ===")
    print(data)

    presenca_id = data.get('id')  # Pode ser 'inicial', um ID numérico ou None
    crianca_id = data['crianca_id']
    entregue = data['entregue']

    print(f"Presenca ID: {presenca_id}, Crianca ID: {crianca_id}, Entregue: {entregue}")

    try:
        conn = sqlite3.connect('criancas.db')
        cursor = conn.cursor()

        if not presenca_id or presenca_id == "None":  # Se for None, atualiza criancas.db
            print("Atualizando presença inicial na tabela criancas...")
            cursor.execute("""
                UPDATE criancas
                SET entregue = ?
                WHERE id = ?
            """, (entregue, crianca_id))
        else:
            print(f"Atualizando presença ID {presenca_id} na tabela presencas...")
            cursor.execute("""
                UPDATE presencas
                SET entregue = ?
                WHERE id = ?
            """, (entregue, presenca_id))

        conn.commit()
        conn.close()

        print("Atualização bem-sucedida!")
        return jsonify({"success": True})
    except Exception as e:
        print("Erro ao atualizar status:", e)
        return jsonify({"success": False, "error": str(e)})


@app.route('/crianca/<int:id>', methods=['GET'])
def detalhes_crianca(id):
    db = get_db(DATABASE_CRIANCAS)

    # Buscar os dados da criança
    query_crianca = """
    SELECT id, nome, idade, escola, responsavel_id, data, turno, entregue
    FROM criancas
    WHERE id = ?
    """
    crianca = db.execute(query_crianca, (id,)).fetchone()

    # Buscar registros adicionais de presença da tabela `presencas`, ordenados do mais recente para o mais antigo
    query_presencas = """
    SELECT data, turno, entregue, id
    FROM presencas
    WHERE crianca_id = ?
    ORDER BY DATE(data) DESC
    """
    presencas = db.execute(query_presencas, (id,)).fetchall()

    # Criar uma lista de presenças, incluindo a primeira presença da tabela `criancas`
    lista_presencas = []

    if crianca[5]:  # Se houver data cadastrada na tabela `criancas`
        lista_presencas.append((crianca[5], crianca[6], crianca[7], None))  # ID None, pois está na tabela `criancas`

    lista_presencas.extend(presencas)  # Adicionar presenças da tabela `presencas`

    # Ordenar a lista de presenças por data, do mais recente para o mais antigo
    lista_presencas.sort(key=lambda x: x[0], reverse=True)

    if crianca:
        return render_template('crianca_detalhes.html', crianca=crianca, presencas=lista_presencas)
    else:
        return "Criança não encontrada", 404


@app.route('/adicionar_presenca', methods=['POST'])
def adicionar_presenca():
    db = get_db(DATABASE_CRIANCAS)
    data = request.json
    crianca_id = data.get("crianca_id")
    nova_data = data.get("data")
    novo_turno = data.get("turno")

    db.execute("INSERT INTO presencas (crianca_id, data, turno, entregue) VALUES (?, ?, ?, 'Ainda não entregue')", 
               (crianca_id, nova_data, novo_turno))
    db.commit()

    return jsonify({"mensagem": "Presença adicionada com sucesso!"})

@app.route('/logout')
def logout():
    resp = make_response(redirect('/'))
    resp.set_cookie('usuario', '', expires=0, path='/')
    return resp

# Função para obter todos os dados das crianças
def get_criancas_data():
    conn = sqlite3.connect(DATABASE_CRIANCAS)
    query = "SELECT * FROM criancas"
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

# Função para obter todos os dados dos responsáveis
def get_responsaveis_data():
    conn = sqlite3.connect(DATABASE_RESPONSAVEIS)
    query = "SELECT * FROM responsaveis"
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

# Rota para gerar a planilha de crianças
@app.route('/planilha_criancas')
def planilha_criancas():
    df_criancas = get_criancas_data()

    # Salvar o dataframe em um arquivo Excel em memória
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_criancas.to_excel(writer, index=False, sheet_name="Crianças")
    output.seek(0)

    return send_file(output, as_attachment=True, download_name="criancas.xlsx", mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# Rota para gerar a planilha de responsáveis
@app.route('/planilha_responsaveis')
def planilha_responsaveis():
    df_responsaveis = get_responsaveis_data()

    # Salvar o dataframe em um arquivo Excel em memória
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_responsaveis.to_excel(writer, index=False, sheet_name="Responsáveis")
    output.seek(0)

    return send_file(output, as_attachment=True, download_name="responsaveis.xlsx", mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")



if __name__ == '__main__':
    init_db()
    app.run(debug=True)
