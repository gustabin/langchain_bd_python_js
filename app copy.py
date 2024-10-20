import logging
import os
from logging.handlers import RotatingFileHandler

import psycopg2
from cryptography.fernet import Fernet
from dotenv import load_dotenv
from flask import Flask, flash, jsonify, redirect, render_template, request, url_for
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from langchain.prompts import PromptTemplate
from langchain_community.utilities import SQLDatabase
from langchain_experimental.sql import SQLDatabaseChain
from langchain_openai import OpenAI
from sqlalchemy import inspect
from sqlalchemy.exc import IntegrityError, OperationalError
from werkzeug.security import generate_password_hash, check_password_hash

from forms import RegistrationForm

cache = {}

logging.basicConfig(
    filename='app_queries.log',
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

handler = RotatingFileHandler('app_queries.log', maxBytes=10**6, backupCount=3)
logging.getLogger().addHandler(handler)

load_dotenv()

openai_api_key = os.getenv('OPENAI_API_KEY')
app = Flask(__name__)

# DATABASE_PATH = os.path.join(
#     os.path.dirname(__file__), 'datasources/echoDB.db')
# app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DATABASE_PATH}'
# {ssl_part}
# user = 'root'
# password = ''
# host = 'localhost'
# port_part = ''  # Puedes dejar esto vacío si no usas un puerto personalizado
# database = 'restaurante'


user = 'stackcod_analistadatos'
password = '1234567890qwerty'
host = 'stackcodelab.com'
port_part = ':3306'
database = 'stackcod_echodb'

# Usar f-string para interpolar las variables dentro de la cadena
DATABASE_URI = f'mysql+pymysql://{user}:{password}@{host}{port_part}/{database}'

# Configurar la URI en SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URI

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

SECRET_KEY = os.getenv('FLASK_SECRET_KEY')
if not SECRET_KEY:
    raise RuntimeError(
        "La clave secreta de Flask ('FLASK_SECRET_KEY') no está configurada en el entorno. "
        "Por favor, define esta variable de entorno antes de iniciar la aplicación. "
        "Esto es crítico para la seguridad de las sesiones y la encriptación de datos sensibles."
    )


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


CORS(app, resources={r"/chat": {
    "origins": ["https://stackcodelab.com", "http://127.0.0.1:5010"],
    "methods": ["GET", "POST", "OPTIONS"],
    "allow_headers": ["Content-Type", "Authorization"]
}, r"/validate-api-key": {
    "origins": ["https://stackcodelab.com", "http://127.0.0.1:5010"],
    "methods": ["POST"],
    "allow_headers": ["Content-Type", "Authorization"]
}})


llm = OpenAI(api_key=openai_api_key, temperature=0, verbose=True)
# db_chain = SQLDatabaseChain.from_llm(llm, SQLDatabase.from_uri(
#     "sqlite:///datasources/inventario.db"), verbose=True)


db_chain = SQLDatabaseChain.from_llm(
    llm, SQLDatabase.from_uri(DATABASE_URI), verbose=True
)

base_prompt = PromptTemplate(
    input_variables=["query"],
    template="Responde a la pregunta '{query}' de forma clara y concisa, proporcionando solo la información solicitada. Evita detalles técnicos y explicaciones adicionales."
)


@app.route('/')
def index():
    return render_template('index.html')

# @app.route('/cliente')
# def cliente():
#     return render_template('cliente.html')


def execute_langchain_query(query):
    if query in cache:
        logging.debug("Consulta obtenida desde el caché: %s", query)
        return cache[query]

    modified_query = base_prompt.format(query=query)
    logging.debug("Consulta modificada para LangChain: %s", modified_query)

    result = db_chain.run(modified_query)

    cache[query] = result.strip()

    logging.debug("Resultado obtenido: %s", result.strip())
    return result.strip()


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


@app.route('/validate-api-key', methods=['POST'])
def validate_api_key():
    data = request.get_json()
    api_key = data.get('api_key')

    if not api_key:
        return jsonify({'error': 'Clave API faltante'}), 400

    if not isinstance(api_key, str) or len(api_key) != 44:
        return jsonify({'error': 'Formato de clave API inválido'}), 400

    try:
        user = User.query.filter_by(api_key=api_key).first()

        if user:
            return jsonify({
                'access': True,
                'user': {
                    'name': user.name,
                    'email': user.email,
                    'password': user.password,
                    'website': user.website,
                    'api_key': user.api_key,
                    'hostDB': user.hostDB,
                    'userDB': user.userDB,
                    'passwordDB': user.passwordDB,
                    'databaseDB': user.databaseDB,
                    'db_type': user.db_type,
                    'port': user.port,
                    'ssl_enabled': user.ssl_enabled,
                    'charset': user.charset
                }
            }), 200
        else:
            return jsonify({'access': False, 'message': 'Clave API no encontrada'}), 403

    except Exception as e:
        logging.error(f"Error en la validación de la clave API: {e}")
        return jsonify({'error': 'Ocurrió un error al validar la clave API'}), 500


@app.route('/clear-cache', methods=['POST'])
def clear_cache():
    global cache
    cache.clear()
    logging.info("Caché limpiado manualmente.")
    return jsonify({"message": "Caché limpiado exitosamente."}), 200


DATABASE_URIS = {
    'mysql': 'mysql+pymysql://{user}:{password}@{host}{port_part}/{database}',
    'postgresql': 'postgresql://{user}:{password}@{host}{port_part}/{database}',
    'sqlserver': 'mssql+pyodbc://{user}:{password}@{host}{port_part}/{database}?driver=SQL+Server',
    'sqlite': 'sqlite:///{database}',
    'oracle': 'oracle+cx_oracle://{user}:{password}@{host}{port_part}/?service_name={database}'
}


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
