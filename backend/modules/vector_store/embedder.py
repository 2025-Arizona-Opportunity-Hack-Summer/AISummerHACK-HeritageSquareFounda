import os
import torch

from typing import List
from langchain_huggingface import HuggingFaceEmbeddings
from dotenv import load_dotenv


load_dotenv()

class EmbeddingGenerator:
    def __init__(self):
        self.embedding_model = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",  # Small and fast
            model_kwargs={'device': 'cuda' if torch.cuda.is_available() else 'cpu'},  # Use GPU if available
            encode_kwargs={'normalize_embeddings': False}
        )

    def generate(self, texts: List[str]) -> List[List[float]]:
        return self.embedding_model.embed_documents(texts)

    def generate_single(self, text: str) -> List[float]:
        return self.embedding_model.embed_query(text)

def load_embedding_model():
    return EmbeddingGenerator()
