from langchain.prompts import PromptTemplate
from flask import render_template, Flask, request, jsonify
from dotenv import load_dotenv
from langchain_community.utilities import SQLDatabase
from langchain_openai import OpenAI
from langchain_experimental.sql import SQLDatabaseChain

# Cargar variables de entorno
load_dotenv()

app = Flask(__name__)

# Conectar a la base de datos SQLite
db = SQLDatabase.from_uri("sqlite:///datasources/inventario.db")

# Configurar el modelo de lenguaje para LangChain
llm = OpenAI(temperature=0, verbose=True)
db_chain = SQLDatabaseChain.from_llm(llm, db, verbose=True)


@app.route('/')
def index():
    return render_template('index.html')


# Define un prompt que se usará en cada consulta
base_prompt = PromptTemplate(
    input_variables=["query"],
    template="Responde en español y evita añadir frases innecesarias como 'Final answer here': {query}"
)


@app.route('/langchain-db', methods=['POST'])
def langchain_db():
    data = request.get_json()
    query = data.get('query')

    # Procesar la consulta utilizando el prompt configurado
    try:
        modified_query = base_prompt.format(query=query)
        result = db_chain.run(modified_query)
        return jsonify({'result': result.strip()}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, port=5010)
