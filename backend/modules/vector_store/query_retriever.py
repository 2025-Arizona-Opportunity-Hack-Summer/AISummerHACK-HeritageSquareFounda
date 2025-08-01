from modules.vector_store.embedder import load_embedding_model
from modules.vector_store.chroma_store import ChromaVectorStore

class QueryRetriever:
    def __init__(self):
        self.embedding_model = load_embedding_model()
        self.vector_store = ChromaVectorStore(self.embedding_model)
        self.vector_store.load_index()

    def retrieve_relevant_chunks(self, query: str, top_k: int = 5):
        """
        Embed the query and retrieve the top-k most relevant document chunks.
        Returns a list of (content, metadata) tuples.
        """
        results = self.vector_store.retrieve(query, k=top_k)
        return results
