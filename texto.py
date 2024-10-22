from langchain_community.document_loaders import TextLoader
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain.chains import RetrievalQA

# Cargar documentos desde un archivo de texto


def load_documents(file_path):
    loader = TextLoader(file_path, encoding='utf-8')
    documents = loader.load()
    return documents

# Crear un índice de los documentos


def create_index(documents):
    embeddings = OpenAIEmbeddings()
    vectorstore = FAISS.from_documents(documents, embeddings)
    return vectorstore

# Crear el chatbot


def create_chatbot(file_path):
    documents = load_documents(file_path)
    vectorstore = create_index(documents)
    qa = RetrievalQA.from_chain_type(
        llm=ChatOpenAI(temperature=0),
        chain_type="stuff",
        retriever=vectorstore.as_retriever()
    )
    return qa


if __name__ == "__main__":
    file_path = 'datasources/data.txt'  # Reemplaza con la ruta a tu archivo de texto
    chatbot = create_chatbot(file_path)

    # Ejemplo de uso del chatbot
    while True:
        query = input("Pregunta al chatbot: ")
        response = chatbot.invoke({"query": query})

        print("Respuesta:", response['result'])
