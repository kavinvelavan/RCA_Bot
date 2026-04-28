from langchain_community.document_loaders import TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings

# Load document
loader = TextLoader("src/data/banking_workflow.txt")
documents = loader.load()

# Split text
splitter = RecursiveCharacterTextSplitter(
    chunk_size=800,
    chunk_overlap=100
)

docs = splitter.split_documents(documents)

# Embeddings
embedding_model = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

# Vector DB
vectorstore = FAISS.from_documents(docs, embedding_model)

# Save locally
vectorstore.save_local("faiss_index")

print("✅ FAISS index created successfully!")
