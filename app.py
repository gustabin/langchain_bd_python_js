from flask import render_template, Flask, request, jsonify, redirect, url_for, flash
from flask_cors import CORS
from dotenv import load_dotenv
from langchain.prompts import PromptTemplate
from langchain_community.utilities import SQLDatabase
from langchain_openai import OpenAI
from langchain_experimental.sql import SQLDatabaseChain
from flask_sqlalchemy import SQLAlchemy
from cryptography.fernet import Fernet
from werkzeug.security import generate_password_hash, check_password_hash
from forms import RegistrationForm
from sqlalchemy import inspect
from sqlalchemy.exc import OperationalError, TimeoutError
from logging.handlers import RotatingFileHandler
import psycopg2
import os
import logging

cache = {}

# Configurar el logging
logging.basicConfig(
    filename='app_queries.log',  # Nombre del archivo de log
    level=logging.DEBUG,  # Nivel de logging (DEBUG es útil para desarrollo)
    format='%(asctime)s %(levelname)s: %(message)s',  # Formato de los mensajes
    datefmt='%Y-%m-%d %H:%M:%S'
)


handler = RotatingFileHandler('app_queries.log', maxBytes=10**6, backupCount=3)
logging.getLogger().addHandler(handler)


# Cargar variables de entorno desde el archivo .env
load_dotenv()

openai_api_key = os.getenv('OPENAI_API_KEY')
# Crear una instancia de la aplicación Flask
app = Flask(__name__)

# Usa una ruta absoluta para evitar problemas de ruta
DATABASE_PATH = os.path.join(
    os.path.dirname(__file__), 'datasources/echoDB.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DATABASE_PATH}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Generar una clave para encriptar y desencriptar (haz esto solo una vez y guarda la clave en un lugar seguro)
# key = Fernet.generate_key()
# print(key.decode())

# Reemplaza esta clave con la que generaste y guardaste
# Asegúrate de que esta clave sea secreta y segura

# app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY')

SECRET_KEY = os.getenv('FLASK_SECRET_KEY')
if not SECRET_KEY:
    raise RuntimeError(
        "La clave secreta de Flask ('FLASK_SECRET_KEY') no está configurada en el entorno. "
        "Por favor, define esta variable de entorno antes de iniciar la aplicación. "
        "Esto es crítico para la seguridad de las sesiones y la encriptación de datos sensibles."
    )


# Definición del modelo de usuario

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
    db_type = db.Column(db.String(50), nullable=False)  # Tipo de base de datos
    port = db.Column(db.Integer, nullable=True)
    ssl_enabled = db.Column(db.Boolean, default=False)
    charset = db.Column(db.String(50), nullable=True)

    # Método para encriptar la contraseña de la base de datos
    def set_password_db(self, password):
        fernet = Fernet(SECRET_KEY)
        self.passwordDB = fernet.encrypt(password.encode()).decode()

    # Método para desencriptar la contraseña de la base de datos
    def get_password_db(self):
        fernet = Fernet(SECRET_KEY)
        return fernet.decrypt(self.passwordDB.encode()).decode()

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def generate_api_key(self):
        # Generar una clave de API única
        self.api_key = Fernet.generate_key().decode()

    def __repr__(self):
        return f'<User {self.name}>'


# Habilitar CORS para la aplicación Flask
CORS(app, resources={r"/chat": {
    "origins": ["https://stackcodelab.com", "http://127.0.0.1:5010"],
    "methods": ["GET", "POST", "OPTIONS"],
    "allow_headers": ["Content-Type", "Authorization"]
}, r"/validate-api-key": {  # Añadir esta línea
    "origins": ["https://stackcodelab.com", "http://127.0.0.1:5010"],
    "methods": ["POST"],
    "allow_headers": ["Content-Type", "Authorization"]
}})


# Configurar el modelo de lenguaje para LangChain
# llm = OpenAI(temperature=0, verbose=True)
llm = OpenAI(api_key=openai_api_key, temperature=0, verbose=True)
db_chain = SQLDatabaseChain.from_llm(llm, SQLDatabase.from_uri(
    "sqlite:///datasources/inventario.db"), verbose=True)

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
    # Verificar si la consulta está en caché
    if query in cache:
        logging.debug(f"Consulta obtenida desde el caché: {query}")
        return cache[query]

    # Modificar la consulta
    modified_query = base_prompt.format(query=query)
    logging.debug(f"Consulta modificada para LangChain: {modified_query}")

    # Ejecutar la consulta en LangChain
    result = db_chain.run(modified_query)

    # Almacenar el resultado en caché
    cache[query] = result.strip()

    logging.debug(f"Resultado obtenido: {result.strip()}")
    return result.strip()


@app.route('/langchain-db', methods=['POST'])
def langchain_db():
    data = request.get_json()
    query = data.get('query')

    logging.info(f"Consulta recibida: {query}")

    try:
        result = execute_langchain_query(query)
        return jsonify({'result': result.strip()}), 200

    except OperationalError as e:
        logging.error(f"Error operativo en la base de datos: {e}")
        return jsonify({'error': 'Error al conectar con la base de datos. Intenta nuevamente.'}), 500

    except TimeoutError as e:
        logging.error(f"Error de tiempo de espera en la base de datos: {e}")
        return jsonify({'error': 'La conexión a la base de datos ha expirado. Intenta nuevamente.'}), 503

    except psycopg2.OperationalError as e:
        logging.error(f"Error específico de PostgreSQL: {e}")
        return jsonify({'error': 'Error al conectar con PostgreSQL. Intenta nuevamente.'}), 500

    except Exception as e:
        logging.exception(f"Error inesperado: {e}")
        return jsonify({'error': 'Ocurrió un error inesperado.'}), 500


@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.json.get('message')

    # Registrar el mensaje del usuario
    logging.info(f"Mensaje del usuario: {user_message}")

    try:
        result = execute_langchain_query(user_message)
        return jsonify({
            "question": user_message,  # Mostrar la pregunta del usuario
            "response": result.strip()  # Mostrar la respuesta del modelo
        })

    except OperationalError as e:
        # Registrar el error de base de datos
        logging.error(f"Error de base de datos: {e}")
        return jsonify({
            "error": 'Lo siento, pero solo manejo información relacionada con la base de datos.'
        }), 400

    except Exception as e:
        # Registrar cualquier otro error
        logging.exception(f"Error inesperado: {e}")
        return jsonify({
            "error": str(e)
        }), 500


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        # Verifica si el email ya está registrado
        if User.query.filter_by(email=form.email.data).first():
            flash('El email ya está registrado. Por favor, usa otro.', 'danger')
            return render_template('register.html', form=form)

        # Crear el nuevo usuario
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
            db_type=form.db_type.data,  # Tipo de base de datos seleccionado
            port=form.port.data if form.port.data else None,
            ssl_enabled=(form.ssl_enabled.data == 'true'),
            charset=form.charset.data
        )

        # Encripta la contraseña del usuario
        new_user.set_password(form.password.data)

        # Encripta la contraseña de la base de datos si se proporciona
        if form.passwordDB.data:
            new_user.set_password_db(form.passwordDB.data)

        # Generar la URI de conexión
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
            # Aquí podrías usar la URI para establecer una conexión o hacer otras verificaciones

        except ValueError as e:
            flash(f"Error al generar la URI de conexión: {str(e)}", 'danger')
            return render_template('register.html', form=form)

        # Generar y asignar la clave de API
        new_user.generate_api_key()

        # Guardar el nuevo usuario en la base de datos
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
            print(f"Error inesperado: {e}")  # Imprime el error para depuración

    return render_template('register.html', form=form)


@app.route('/validate-api-key', methods=['POST'])
def validate_api_key():
    data = request.get_json()
    api_key = data.get('api_key')

    # Verifica si la clave API falta
    if not api_key:
        return jsonify({'error': 'Clave API faltante'}), 400

    # Verifica el formato de la clave API (esto es un ejemplo, ajústalo según tu implementación)
    # Aquí un ejemplo de longitud para Fernet
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
        logging.exception(f"Error en la validación de la clave API: {e}")
        return jsonify({'error': 'Ocurrió un error al validar la clave API'}), 500


@app.route('/clear-cache', methods=['POST'])
def clear_cache():
    global cache
    cache.clear()  # Limpiar el caché
    logging.info("Caché limpiado manualmente.")
    return jsonify({"message": "Caché limpiado exitosamente."}), 200


DATABASE_URIS = {
    'mysql': 'mysql+pymysql://{user}:{password}@{host}{port_part}/{database}',
    'postgresql': 'postgresql://{user}:{password}@{host}{port_part}/{database}',
    'sqlserver': 'mssql+pyodbc://{user}:{password}@{host}{port_part}/{database}?driver=SQL+Server',
    'sqlite': 'sqlite:///{database}',  # SQLite no requiere host ni puerto
    'oracle': 'oracle+cx_oracle://{user}:{password}@{host}{port_part}/?service_name={database}'
}


def generate_database_uri(db_type, user, password, host, port, database, ssl_enabled):
    if not user or not password or not host or not database:
        raise ValueError(
            "Faltan parámetros críticos para generar la URI de conexión.")

    # Para bases de datos que no requieren puerto, dejamos el campo vacío
    port_part = f':{port}' if port else ''

    if db_type in DATABASE_URIS:
        return DATABASE_URIS[db_type].format(
            user=user,
            password=password,
            host=host,
            port_part=port_part,  # Se añade el puerto solo si existe
            database=database
        )
    else:
        raise ValueError(f"Tipo de base de datos '{db_type}' no soportado.")


def create_tables_if_not_exist():
    # Inspecciona la base de datos para verificar si ya existen tablas
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()

    if not tables:
        # Si no hay tablas, las creamos
        db.create_all()
        logging.info("Tablas creadas exitosamente.")
    else:
        logging.info("Las tablas ya existen, no es necesario crearlas.")


if __name__ == '__main__':
    with app.app_context():
        # Ejecutar solo una vez al iniciar la aplicación
        create_tables_if_not_exist()
    app.run(debug=True, port=5010)
