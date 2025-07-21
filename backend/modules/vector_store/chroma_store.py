import os
from typing import List, Tuple
from langchain.vectorstores import Chroma
from langchain.embeddings.base import Embeddings
from langchain.docstore.document import Document
from dotenv import load_dotenv

# Load .env for CHROMA persistence config if needed
load_dotenv()

class ChromaVectorStore:
    def __init__(self, embedding_model: Embeddings, persist_directory: str = "chroma_db"):
        self.embedding_model = embedding_model
        self.persist_directory = persist_directory
        self.vectorstore = None

    def create_index(self, texts: List[str], metadatas: List[dict] = None) -> None:
        """Creates a Chroma index from the given texts and metadata."""
        documents = [Document(page_content=texts[i], metadata=metadatas[i] if metadatas else {}) for i in range(len(texts))]
        self.vectorstore = Chroma.from_documents(
            documents=documents,
            embedding=self.embedding_model,
            persist_directory=self.persist_directory
        )
        self.vectorstore.persist()

    def load_index(self) -> None:
        """Loads an existing Chroma index from disk."""
        self.vectorstore = Chroma(
            embedding_function=self.embedding_model,
            persist_directory=self.persist_directory
        )

    def retrieve(self, query: str, k: int = 5) -> List[Tuple[str, dict]]:
        """Retrieves top-k most similar chunks to a given query."""
        if self.vectorstore is None:
            self.load_index()
        results = self.vectorstore.similarity_search(query, k=k)
        return [(doc.page_content, doc.metadata) for doc in results]
