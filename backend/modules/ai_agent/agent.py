#agent.py
import os
from typing import List, Dict, Any
from dotenv import load_dotenv

from langchain_google_vertexai import VertexAI
from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA

from modules.vector_store.embedder import load_embedding_model
from modules.vector_store.chunker import chunk_text
from modules.vector_store.chroma_store import ChromaVectorStore

from vertexai import init
load_dotenv()
project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")

init(project=project_id, location=location)

class RAGAgent:
    """
    RAG Agent using Vertex AI for LLM and Embeddings.
    ChromaDB is used as the vector store backend.
    """

    def __init__(self, project_id: str, location: str = "us-central1"):
        # Load embedding model (Vertex AI)
        self.embedder = load_embedding_model()

        # Load LLM (Vertex Gemini)
        self.llm = VertexAI(
            model_name="gemini-pro",
            project=project_id,
            location=location,
            max_output_tokens=1024,
            temperature=0.3,
            top_p=0.8,
            top_k=40
        )

        # Initialize Chroma vector store
        self.vector_store = ChromaVectorStore(self.embedder)
        self.vector_store.load_index()

        # Will be initialized after indexing
        self.qa_chain = None

    def _setup_qa_chain(self):
        """Set up the RAG chain with custom prompt template"""
        prompt_template = """
        You are an AI assistant for Heritage Square Foundation.
        Use the following pieces of context to answer the question at the end. 
        If you don't know the answer, just say that you don't know, don't try to make up an answer.
        
        Context: {context}
        
        Question: {question}
        
        Please provide a detailed answer based on the context above. 
        If the context doesn't contain enough information to fully answer the question, mention this in your response. 
        Always cite specific documents or sources from the context when possible.
        
        Answer:"""

        prompt = PromptTemplate(
            template=prompt_template,
            input_variables=["context", "question"]
        )

        self.qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=self.vector_store.as_retriever(
                search_type="similarity",
                search_kwargs={"k": 4}
            ),
            chain_type_kwargs={
                "prompt": PROMPT
            },
            return_source_documents=True
        )

    def process_documents(self, documents: List[str], chunk_size: int = 500, chunk_overlap: int = 50):
        """
        Splits raw documents into chunks, embeds them, and creates a vector index.
        Then sets up the RAG retrieval chain.
        """
        all_chunks = []
        for doc in documents:
            chunks = chunk_text(doc)
            all_chunks.extend(chunks)

        metadatas = [{"source": f"doc_{i}"} for i in range(len(all_chunks))]
        self.vector_store.create_index(texts=all_chunks, metadatas=metadatas)

        self._setup_qa_chain()

    async def answer_question(self, question: str) -> Dict[str, Any]:
        """
        Answers a user question using the RAG pipeline.
        """
        if not self.qa_chain:
            raise ValueError("QA Chain not initialized. Please process documents first.")
        
        result = self.qa_chain({"query": question})

        return {
            "answer": result["result"],
            "source_documents": [
                {
                    "content": doc.page_content,
                    "metadata": doc.metadata
                }
                for doc in result["source_documents"]
            ]
        }

    def get_relevant_chunks(self, query: str, k: int = 4) -> List[Dict[str, Any]]:
        """
        Returns top-k most relevant chunks from vector store without answering.
        """
        if not self.vector_store:
            raise ValueError("Vector store not initialized. Please process documents first.")
        
        chunks = self.vector_store.retrieve(query, k=k)
        return [{"content": doc.page_content, "metadata": doc.metadata} for doc in chunks]
