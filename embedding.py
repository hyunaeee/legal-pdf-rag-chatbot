from langchain_chroma import Chroma
from langchain_upstage import UpstageEmbeddings

def create_vectorstore(pages):
    vectorstore = Chroma.from_documents(pages, UpstageEmbeddings(model="solar-embedding-1-large"))
    return vectorstore.as_retriever(k=2)