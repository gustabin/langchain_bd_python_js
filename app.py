# Para manejar la aplicación web
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
import os

# Cargar variables de entorno desde el archivo .env
load_dotenv()

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
# SECRET_KEY = b'3TJMTSurWkYSIK0Bo98K4-BX8XZn2H4KPmouNZeIq7Q='
# Asegúrate de que esta clave sea secreta y segura
app.config['SECRET_KEY'] = b'3TJMTSurWkYSIK0Bo98K4-BX8XZn2H4KPmouNZeIq7Q='


# Definición del modelo de usuario

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(128))  # Contraseña del usuario encriptada
    website = db.Column(db.String(100), nullable=False)
    api_key = db.Column(db.String(128), unique=True,
                        nullable=False)  # Clave de API
    # Campos para la conexión a la base de datos
    hostDB = db.Column(db.String(100), nullable=False)
    userDB = db.Column(db.String(100), nullable=False)
    # Contraseña encriptada
    passwordDB = db.Column(db.String(100), nullable=True)
    databaseDB = db.Column(db.String(100), nullable=False)
    db_type = db.Column(db.String(50), nullable=False)
    port = db.Column(db.Integer, nullable=True)  # Puerto de la base de datos
    # Si SSL está habilitado
    ssl_enabled = db.Column(db.Boolean, default=False)
    charset = db.Column(db.String(50), nullable=True)  # Charset de la conexión

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
llm = OpenAI(temperature=0, verbose=True)
db_chain = SQLDatabaseChain.from_llm(llm, SQLDatabase.from_uri(
    "sqlite:///datasources/inventario.db"), verbose=True)

base_prompt = PromptTemplate(
    input_variables=["query"],
    template="Responde en español y evita añadir frases innecesarias como 'Final answer here': {query}"
)


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

    try:
        modified_query = base_prompt.format(query=query)
        result = db_chain.run(modified_query)
        return jsonify({'result': result.strip()}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.json.get('message')

    try:
        modified_query = base_prompt.format(query=user_message)
        result = db_chain.run(modified_query)
        return jsonify({"response": result.strip()})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        # Verifica si el email ya está registrado
        if User.query.filter_by(email=form.email.data).first():
            flash('El email ya está registrado. Por favor, usa otro.', 'danger')
            print('Mensaje flash agregado: El email ya está registrado.')  # Debug
            return render_template('register.html', form=form)

        # Aquí imprimes el valor del campo passwordDB
        # Imprime el valor recibido
        print(f"SSL Enabled Value: {form.passwordDB.data}")

        new_user = User(
            name=form.name.data,
            email=form.email.data,
            website=form.website.data,
            hostDB=form.hostDB.data,
            userDB=form.userDB.data,
            databaseDB=form.databaseDB.data,
            db_type=form.db_type.data,
            # Asignar None si el campo está vacío
            port=form.port.data if form.port.data else None,
            ssl_enabled=(form.ssl_enabled.data == 'true'),
            charset=form.charset.data
        )

        # Encripta la contraseña del usuario
        new_user.set_password(form.password.data)

        # Encripta la contraseña de la base de datos si se proporciona
        if form.passwordDB.data:
            # Encriptar la contraseña de la base de datos
            new_user.set_password_db(form.passwordDB.data)

         # Generar y asignar la clave de API
        new_user.generate_api_key()

        try:
            db.session.add(new_user)
            db.session.commit()
            flash('Usuario registrado exitosamente!', 'success')
            # Mostrar el script con la clave de API
            flash(f'Por favor, copia y pega este script en tu sitio web: '
                  f'<script src="https://echodb-rlca.onrender.com/static/js/chatbot.js" '
                  f'data-api-key="{new_user.api_key}"></script>', 'info')
            # Redirige o muestra un mensaje
            return redirect(url_for('register'))
        except Exception as e:
            db.session.rollback()  # Revierte la sesión si ocurre un error
            flash('Error al registrar el usuario. Inténtalo de nuevo.', 'danger')
            print(f'Error: {e}')  # Imprime el error para depuración

    return render_template('register.html', form=form)


@app.route('/validate-api-key', methods=['POST'])
def validate_api_key():
    data = request.get_json()
    api_key = data.get('api_key')

    if not api_key:
        return jsonify({'error': 'API key is missing'}), 400

    user = User.query.filter_by(api_key=api_key).first()

    if user:
        # Usuario encontrado, retornar los datos
        return jsonify({
            'access': True,
            'user': {
                'name': user.name,
                'email': user.email,
                'website': user.website,
                'password': user.password,
                'hostDB': user.hostDB,
                'userDB': user.userDB,
                'passwordDB': user.passwordDB,
                'databaseDB': user.databaseDB,
                'db_type': user.db_type,
                'port': user.port,
                'ssl_enabled': user.ssl_enabled,
                'charset': user.charset
                # Puedes incluir más campos si es necesario
            }
        }), 200
    else:
        # API key inválido
        return jsonify({'access': False, 'message': 'No tienes acceso al chatbot.'}), 403


if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Crear todas las tablas definidas en los modelos
    app.run(debug=True, port=5010)
