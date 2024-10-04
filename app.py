# Importar las librerías necesarias de LangChain y Flask
from langchain.prompts import PromptTemplate  # Para crear plantillas de prompts
# Para manejar la aplicación web
from flask import render_template, Flask, request, jsonify
# Para cargar variables de entorno desde un archivo .env
from dotenv import load_dotenv
# Para manejar la conexión a la base de datos
from langchain_community.utilities import SQLDatabase
# Para configurar el modelo de lenguaje OpenAI
from langchain_openai import OpenAI
# Para crear una cadena que maneje consultas SQL
from langchain_experimental.sql import SQLDatabaseChain

# Cargar variables de entorno desde el archivo .env
load_dotenv()

# Crear una instancia de la aplicación Flask
app = Flask(__name__)

# Conectar a la base de datos SQLite especificando la URI de la base de datos
db = SQLDatabase.from_uri("sqlite:///datasources/inventario.db")

# Configurar el modelo de lenguaje para LangChain con parámetros específicos
# Configura el modelo para que no sea aleatorio y que imprima información detallada
llm = OpenAI(temperature=0, verbose=True)
# Crear la cadena de base de datos utilizando el modelo y la conexión a la base de datos
db_chain = SQLDatabaseChain.from_llm(llm, db, verbose=True)

# Ruta principal que renderiza la plantilla 'index.html'


@app.route('/')
def index():
    # Devuelve la vista principal de la aplicación
    return render_template('index.html')


# Define un prompt que se usará en cada consulta
base_prompt = PromptTemplate(
    # Define las variables de entrada que usará el prompt
    input_variables=["query"],
    # Plantilla que formatea la consulta
    template="Responde en español y evita añadir frases innecesarias como 'Final answer here': {query}"
)

# Ruta para manejar las consultas a la base de datos


@app.route('/langchain-db', methods=['POST'])  # Acepta solicitudes POST
def langchain_db():
    data = request.get_json()  # Obtiene los datos JSON del cuerpo de la solicitud
    query = data.get('query')  # Extrae la consulta de los datos

    # Procesar la consulta utilizando el prompt configurado
    try:
        # Modifica la consulta utilizando la plantilla
        modified_query = base_prompt.format(query=query)
        # Ejecuta la consulta en la base de datos
        result = db_chain.run(modified_query)
        # Devuelve el resultado como JSON
        return jsonify({'result': result.strip()}), 200
    except Exception as e:
        # Manejo de errores, devuelve un mensaje de error como JSON
        return jsonify({'error': str(e)}), 500


# Ejecuta la aplicación Flask si este archivo es el principal
if __name__ == '__main__':
    # Inicia el servidor en modo debug en el puerto 5010
    app.run(debug=True, port=5010)
