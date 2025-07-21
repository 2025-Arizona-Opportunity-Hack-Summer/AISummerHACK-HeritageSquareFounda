from typing import List
from langchain.embeddings import HuggingFaceEmbeddings
from dotenv import load_dotenv

load_dotenv()

class EmbeddingGenerator:
    def __init__(self):
        self.embedding_model = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2", #"sentence-transformers/all-mpnet-base-v2"
            model_kwargs = {'device': 'cpu'},
            encode_kwargs = {'normalize_embeddings': False}
        )

    def generate(self, texts: List[str]) -> List[List[float]]:
        return self.embedding_model.embed_documents(texts)

    def generate_single(self, text: str) -> List[float]:
        return self.embedding_model.embed_query(text)
