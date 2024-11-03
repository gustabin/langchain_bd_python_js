import os
import logging

from flask import Flask, jsonify, render_template, request
from flask_cors import CORS
from dotenv import load_dotenv
from langchain_openai import OpenAI
from langchain.prompts import PromptTemplate
from langchain_community.document_loaders import TextLoader
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import Annoy
from langchain.chains import RetrievalQA

# Cargar variables de entorno desde un archivo .env
load_dotenv()

# Configuraciones globales
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Inicializar la aplicación Flask
app = Flask(__name__)
CORS(app)  # Permitir solicitudes CORS

# Variables de configuración
db_chain = None

# Plantilla de prompt base para consultas
base_prompt = PromptTemplate(
    input_variables=["query"],
    template="Responde a '{query}' únicamente con la información proporcionada en el contenido disponible, sin agregar detalles adicionales."
)

def create_index_from_content(content_text):
    """
    Crea un índice de Annoy a partir del contenido proporcionado.

    :param content_text: Texto del contenido que se utilizará para crear el índice.
    :return: Instancia de vectorstore de Annoy.
    """
    documents = [content_text]  # Convertir el contenido en una lista de un solo documento
    embeddings = OpenAIEmbeddings(api_key=OPENAI_API_KEY)  # Inicializar embeddings de OpenAI
    vectorstore = Annoy.from_texts(documents, embeddings)  # Crear el índice Annoy
    return vectorstore

@app.route('/setup-db', methods=['POST'])
def setup_content():
    """
    Ruta para configurar el contenido que será usado en el sistema de consulta.

    :return: Mensaje de éxito o error en la configuración del contenido.
    """
    global db_chain

    data = request.json
    content_text = data.get('contenido')

    if not content_text:
        return jsonify({'error': 'El campo contenido es requerido'}), 400

    try:
        # Crear el índice de Annoy con el contenido proporcionado
        vectorstore = create_index_from_content(content_text)
        
        # Crear el chatbot para consultas usando el modelo de lenguaje
        llm = ChatOpenAI(api_key=OPENAI_API_KEY, temperature=0)
        db_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=vectorstore.as_retriever()
        )

        return jsonify({'message': 'Contenido configurado con éxito'}), 200

    except Exception as e:
        logging.error(f"Error en setup_content: {str(e)}")
        return jsonify({'error': f'Error al configurar el contenido: {str(e)}'}), 500

def execute_langchain_query(query):
    """
    Ejecuta una consulta usando LangChain y el contenido configurado.

    :param query: La consulta del usuario.
    :return: Resultado de la consulta.
    """
    if not db_chain:
        raise ValueError("El contenido no está configurado correctamente")

    result = db_chain.invoke({"query": query})  # Invocar la consulta
    return result.get('result', '').strip()  # Devolver el resultado formateado

@app.route('/')
def index():
    """
    Ruta principal que renderiza la página de inicio.
    """
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    """
    Ruta para manejar las consultas del usuario.

    :return: Respuesta del chatbot con la consulta y su respuesta.
    """
    user_message = request.json.get('message')
    logging.info("Mensaje del usuario: %s", user_message)

    try:
        result = execute_langchain_query(user_message)  # Ejecutar la consulta
        return jsonify({"question": user_message, "response": result.strip()})

    except Exception as e:
        logging.exception("Error inesperado: %s", e)
        return jsonify({"error": str(e)}), 500

# Ejecutar la aplicación en el puerto especificado
if __name__ == '__main__':
    app.run(debug=False, port=5010)
