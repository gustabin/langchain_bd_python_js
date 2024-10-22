from langchain_community.vectorstores import FAISS
from langchain.chains import RetrievalQA
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, Integer, String

# Configuración de la base de datos
# DATABASE_URL = "sqlite:///datasources/inventario.db"
DATABASE_URL = f'mysql://root:@localhost:3306/echoDB'
Base = declarative_base()

# Definición del modelo


class Document(Base):
    __tablename__ = 'user'  # Nombre de tu tabla
    id = Column(Integer, primary_key=True)
    contenido = Column(String)  # Cambia el tipo según tu necesidad

# Clase para el documento que utiliza Langchain


class DocumentLangchain:
    def __init__(self, content, metadata=None):
        self.page_content = content
        self.metadata = metadata or {}


# Crear motor y sesión
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

# Cargar documentos desde la base de datos


def load_documents():
    documents = session.query(Document).all()
    # Devuelve una lista de objetos DocumentLangchain
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


if __name__ == "__main__":
    chatbot = create_chatbot()

    # Ejemplo de uso del chatbot
    while True:
        query = input("Pregunta al chatbot: ")
        response = chatbot.invoke({"query": query})
        print("Respuesta:", response['result'])
