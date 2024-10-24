# 1. Librerías estándar de Python
import logging
import os
import subprocess

# 2. Librerías externas
import pyodbc
import psycopg2
from cryptography.fernet import Fernet
from dotenv import load_dotenv
from flask import Flask, flash, jsonify, redirect, render_template, request, url_for, session
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash

# 3. Librerías de manejo de base de datos y errores
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy import inspect

# 4. Librerías de terceros para Langchain
from langchain_openai import OpenAI
from langchain_experimental.sql import SQLDatabaseChain
from langchain_community.utilities import SQLDatabase
from langchain.prompts import PromptTemplate

# 5. Formularios personalizados
from forms import RegistrationForm

# 6. Otros
from logging.handlers import RotatingFileHandler

from textoDb import DocumentLangchain


load_dotenv()

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
SECRET_KEY = os.getenv('FLASK_SECRET_KEY')
if not SECRET_KEY:
    raise RuntimeError(
        "La clave secreta de Flask ('FLASK_SECRET_KEY') no está configurada en el entorno. "
        "Por favor, define esta variable de entorno antes de iniciar la aplicación. "
        "Esto es crítico para la seguridad de las sesiones y la encriptación de datos sensibles."
    )

DATABASE_PATH = os.path.join(
    os.path.dirname(__file__), 'datasources/echoDB.db')

app = Flask(__name__)
# Establece una clave secreta para las sesiones
# Cambia esto por una clave segura
# app.secret_key = 'una_clave_secreta_super_segura'
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DATABASE_PATH}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

DATABASE_URIS = {
    'mysql': 'mysql+pymysql://{user}:{password}@{host}{port_part}/{database}',
    'postgresql': 'postgresql://{user}:{password}@{host}{port_part}/{database}',
    'sqlserver': 'mssql+pyodbc://{user}:{password}@{host}{port_part}/{database}?driver=SQL+Server',
    'sqlite': 'sqlite:///{database}',
    'oracle': 'oracle+cx_oracle://{user}:{password}@{host}{port_part}/?service_name={database}'
}


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(128))
    website = db.Column(db.String(100), nullable=False)
    api_key = db.Column(db.String(128), unique=True, nullable=False)
    hostDB = db.Column(db.String(100), nullable=False)
    userDB = db.Column(db.String(100), nullable=False)
    passwordDB = db.Column(db.String(100), nullable=True)
    databaseDB = db.Column(db.String(100), nullable=False)
    db_type = db.Column(db.String(50), nullable=False)
    port = db.Column(db.Integer, nullable=True)
    ssl_enabled = db.Column(db.Boolean, default=False)
    charset = db.Column(db.String(50), nullable=True)

    def set_password_db(self, password):
        fernet = Fernet(SECRET_KEY)
        self.passwordDB = fernet.encrypt(password.encode()).decode()

    def get_password_db(self):
        fernet = Fernet(SECRET_KEY)
        return fernet.decrypt(self.passwordDB.encode()).decode()

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def generate_api_key(self):
        self.api_key = Fernet.generate_key().decode()

    def __repr__(self):
        return f'<User {self.name}>'


# Variable global para almacenar DATABASE_URI
DATABASE_URI = None
CONTENIDO_TEXTO = None
db_chain = None  # Inicializa la variable

base_prompt = PromptTemplate(
    input_variables=["query"],
    template="Responde a la pregunta '{query}' de forma clara y concisa, proporcionando solo la información solicitada. Evita detalles técnicos y explicaciones adicionales."
)


# CORS(app)
CORS(app, resources={r"/*": {"origins": "http://localhost"}})

# CORS(app, resources={r"/chat": {
#     "origins": ["https://stackcodelab.com", "http://127.0.0.1:5010"],
#     "methods": ["GET", "POST", "OPTIONS"],
#     "allow_headers": ["Content-Type", "Authorization"]
# }, r"/validate-api-key": {
#     "origins": ["https://stackcodelab.com", "http://127.0.0.1:5010"],
#     "methods": ["POST"],
#     "allow_headers": ["Content-Type", "Authorization"]
# }})


@app.route('/setup-db', methods=['POST'])
def setup_db():
    # Declara que vamos a usar las variables globales
    global DATABASE_URI, db_chain, CONTENIDO_TEXTO

    data = request.json
    # Tipo de base de datos (por ejemplo, 'mysql')
    typeDB = data.get('typeDB')
    userDB = data.get('userDB')  # Nombre de usuario de la base de datos
    passwordDB = data.get('passwordDB')  # Contraseña de la base de datos
    hostDB = data.get('hostDB')  # Host de la base de datos
    port = data.get('port', '3306')  # Puerto de la base de datos
    databaseDB = data.get('databaseDB')  # Nombre de la base de datos

    # Construir la cadena de conexión (URI)
    port_part = f':{port}' if port else ''

    if typeDB.lower() == 'mysql':
        DATABASE_URI = f'{typeDB}://{userDB}:{passwordDB}@{hostDB}{port_part}/{databaseDB}'
    elif typeDB.lower() == 'postgresql':
        DATABASE_URI = f'postgresql://{userDB}:{passwordDB}@{hostDB}{port_part}/{databaseDB}'
    elif typeDB.lower() == 'sqlite':
        DATABASE_URI = f'sqlite:///{databaseDB}'
    elif typeDB.lower() == 'texto':
        DATABASE_URI = f'mysql://root:@localhost:3306/echodb'
        CONTENIDO_TEXTO = True
    elif typeDB.lower() == 'sqlserver':
        # No furula
        DATABASE_URI = f'mssql+pyodbc://{userDB}:{passwordDB}@{hostDB}/{databaseDB}?driver=ODBC+Driver+17+for+SQL+Server'

    elif typeDB.lower() == 'oracle':
        # No la he probado
        DATABASE_URI = f'oracle+cx_oracle://{userDB}:{passwordDB}@{hostDB}{port_part}/{databaseDB}'
    else:
        raise ValueError("Tipo de base de datos no soportado")

    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URI

    llm = OpenAI(api_key=OPENAI_API_KEY, temperature=0,
                 verbose=True, model_name='gpt-3.5-turbo')
    db_chain = SQLDatabaseChain.from_llm(
        OpenAI(api_key=OPENAI_API_KEY, temperature=0, verbose=True),
        SQLDatabase.from_uri(DATABASE_URI),
        verbose=True
    )
    print(f'Conexión configurada con éxito DATABASE_URI', {
          DATABASE_URI}, ' contenido texto: ', {CONTENIDO_TEXTO})
    return jsonify({'message': 'Conexión configurada con éxito', 'DATABASE_URI': DATABASE_URI})


def execute_langchain_query(query):
    if (CONTENIDO_TEXTO):
        from langchain_community.vectorstores import FAISS
        from langchain.chains import RetrievalQA
        from langchain_openai import OpenAIEmbeddings, ChatOpenAI
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker, declarative_base
        from sqlalchemy import Column, Integer, String

        # Configuración de la base de datos
        # DATABASE_URL = f'mysql://root:@localhost:3306/echoDB'
        DATABASE_URL = DATABASE_URI
        Base = declarative_base()

        # Definición del modelo
        class Document(Base):
            __tablename__ = 'user'  # Nombre de tu tabla
            id = Column(Integer, primary_key=True)
            contenido = Column(String)

        # Crear motor y sesión
        engine = create_engine(DATABASE_URL)
        Session = sessionmaker(bind=engine)
        session = Session()

        # Cargar documentos desde la base de datos
        def load_documents():
            documents = session.query(Document).all()
            return [DocumentLangchain(doc.contenido, metadata={"id": doc.id}) for doc in documents]

        # Crear un índice de los documentos
        def create_index(documents):
            embeddings = OpenAIEmbeddings()
            vectorstore = FAISS.from_documents(documents, embeddings)
            return vectorstore

        # Crear el chatbot
        def create_chatbot():
            documents = load_documents()
            vectorstore = create_index(documents)
            qa = RetrievalQA.from_chain_type(
                llm=ChatOpenAI(temperature=0),
                chain_type="stuff",
                retriever=vectorstore.as_retriever()
            )
            return qa

        # Ejecutar la lógica del chatbot con documentos
        chatbot = create_chatbot()
        result = chatbot.invoke({"query": query})
        return result.get('result', '').strip()

    else:
        modified_query = base_prompt.format(query=query)
        logging.debug("Consulta modificada para LangChain: %s", modified_query)

        result = db_chain.run(modified_query)
        logging.debug("Resultado obtenido: %s", result.strip())

    return result.strip()


@app.route('/')
def index():
    return render_template('index.html')

# @app.route('/cliente')
# def cliente():
#     return render_template('cliente.html')


@app.route('/langchain-db', methods=['POST'])
def langchain_db():
    data = request.get_json()
    query = data.get('query')

    logging.info("Consulta recibida: %s", query)

    try:
        result = execute_langchain_query(query)
        return jsonify({'result': result.strip()}), 200

    except OperationalError as e:
        logging.error("Error operativo en la base de datos: %s", e)
        return jsonify({'error': 'Error al conectar con la base de datos. Intenta nuevamente.'}), 500

    except TimeoutError as e:
        logging.error("Error de tiempo de espera en la base de datos: %s", e)
        return jsonify({'error': 'La conexión a la base de datos ha expirado. Intenta nuevamente.'}), 503

    except psycopg2.OperationalError as e:
        logging.error("Error específico de PostgreSQL: %s", e)
        return jsonify({'error': 'Error al conectar con PostgreSQL. Intenta nuevamente.'}), 500

    except Exception as e:
        logging.exception("Error inesperado: %s", e)
        return jsonify({'error': 'Ocurrió un error inesperado.'}), 500


@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.json.get('message')
    logging.info("Mensaje del usuario: %s", user_message)

    try:
        result = execute_langchain_query(user_message)
        return jsonify({
            "question": user_message,
            "response": result.strip()
        })

    except OperationalError as e:
        logging.error("Error de base de datos: %s", e)
        return jsonify({
            "error": 'Lo siento, pero solo manejo información relacionada con la base de datos.'
        }), 400

    except Exception as e:
        logging.exception("Error inesperado: %s", e)
        return jsonify({
            "error": str(e)
        }), 500


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        if User.query.filter_by(email=form.email.data).first():
            flash('El email ya está registrado. Por favor, usa otro.', 'danger')
            return render_template('register.html', form=form)

        new_user = User(
            name=form.name.data,
            email=form.email.data,
            password=form.password.data,
            website=form.website.data,
            api_key=form.api_key.data,
            hostDB=form.hostDB.data,
            userDB=form.userDB.data,
            passwordDB=form.passwordDB.data,
            databaseDB=form.databaseDB.data,
            db_type=form.db_type.data,
            port=form.port.data if form.port.data else None,
            ssl_enabled=(form.ssl_enabled.data == 'true'),
            charset=form.charset.data
        )

        new_user.set_password(form.password.data)

        if form.passwordDB.data:
            new_user.set_password_db(form.passwordDB.data)

        try:
            connection_uri = generate_database_uri(
                new_user.db_type,
                new_user.userDB,
                new_user.get_password_db(),
                new_user.hostDB,
                new_user.port,
                new_user.databaseDB,
                new_user.ssl_enabled
            )
            print(f"URI de conexión generada: {connection_uri}")

        except ValueError as e:
            flash(f"Error al generar la URI de conexión: {str(e)}", 'danger')
            return render_template('register.html', form=form)

        new_user.generate_api_key()

        try:
            db.session.add(new_user)
            db.session.commit()
            flash('Usuario registrado exitosamente!', 'success')
            flash(f'Por favor, copia y pega este script en tu sitio web: '
                  f'<script src="https://echodb-rlca.onrender.com/static/js/chatbot.js" '
                  f'data-api-key="{new_user.api_key}"></script>', 'info')
            return redirect(url_for('register'))

        except IntegrityError as e:
            db.session.rollback()
            flash(
                'Error de integridad de datos al registrar el usuario. Intenta con otros datos.', 'danger')
            print(f"Error de integridad: {e}")

        except OperationalError as e:
            db.session.rollback()
            flash('Error de conexión a la base de datos al registrar el usuario. Intenta de nuevo más tarde.', 'danger')
            print(f"Error de conexión: {e}")
        except Exception as e:
            db.session.rollback()
            flash('Error al registrar el usuario. Inténtalo de nuevo.', 'danger')
            print(f"Error inesperado: {e}")

    return render_template('register.html', form=form)


def generate_database_uri(db_type, user, password, host, port, database, ssl_enabled):
    if not user or not password or not host or not database:
        raise ValueError(
            "Faltan parámetros críticos para generar la URI de conexión.")

    port_part = f':{port}' if port else ''

    if db_type in DATABASE_URIS:
        return DATABASE_URIS[db_type].format(
            user=user,
            password=password,
            host=host,
            port_part=port_part,
            database=database
        )
    else:
        raise ValueError(f"Tipo de base de datos '{db_type}' no soportado.")


def create_tables_if_not_exist():
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()

    if not tables:
        db.create_all()
        logging.info("Tablas creadas exitosamente.")
    else:
        logging.info("Las tablas ya existen, no es necesario crearlas.")


if __name__ == '__main__':
    with app.app_context():
        create_tables_if_not_exist()
    app.run(debug=True, port=5010)
