#agent.py

from typing import List, Dict, Any
import os
from dotenv import load_dotenv
from langchain_google_vertexai import VertexAI
from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores.faiss import FAISS
from langchain_google_vertexai import VertexAIEmbeddings

class RAGAgent:
    def __init__(self, project_id: str, location: str = "us-central1"):
        """
        Initialize the RAG Agent with Google Cloud credentials
        
        Args:
            project_id: Google Cloud project ID
            location: Google Cloud region
        """
        load_dotenv()
        
        # Initialize Vertex AI
        os.environ["GOOGLE_CLOUD_PROJECT"] = project_id
        self.embeddings = VertexAIEmbeddings(
            model_name="textembedding-gecko",
            project=project_id,
            location=location
        )
        
        # Initialize Gemini Pro
        self.llm = VertexAI(
            model_name="gemini-pro",
            project=project_id,
            location=location,
            max_output_tokens=1024,
            temperature=0.3,
            top_p=0.8,
            top_k=40
        )
        
        self.vector_store = None
        self.qa_chain = None

    def initialize_vector_store(self, texts: List[str], metadatas: List[Dict[str, Any]] = None):
        """
        Initialize or update the FAISS vector store with new documents
        
        Args:
            texts: List of text chunks to be embedded
            metadatas: Optional metadata for each text chunk
        """
        if self.vector_store is None:
            self.vector_store = FAISS.from_texts(texts, self.embeddings, metadatas=metadatas)
        else:
            self.vector_store.add_texts(texts, metadatas=metadatas)
            
        # Initialize the QA chain after vector store is ready
        self._setup_qa_chain()

    def _setup_qa_chain(self):
        """Set up the RAG chain with custom prompt template"""
        prompt_template = """You are an AI assistant for Heritage Square Foundation. Use the following pieces of context to answer the question at the end. 
        If you don't know the answer, just say that you don't know, don't try to make up an answer.
        
        Context: {context}
        
        Question: {question}
        
        Please provide a detailed answer based on the context above. If the context doesn't contain enough information to fully answer the question, 
        mention this in your response. Always cite specific documents or sources from the context when possible.
        
        Answer:"""
        
        PROMPT = PromptTemplate(
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
        Process new documents by splitting them into chunks and updating the vector store
        
        Args:
            documents: List of document texts
            chunk_size: Size of text chunks
            chunk_overlap: Overlap between chunks
        """
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        
        chunks = text_splitter.create_documents(documents)
        texts = [chunk.page_content for chunk in chunks]
        metadatas = [{"source": f"doc_{i}"} for i in range(len(texts))]
        
        self.initialize_vector_store(texts, metadatas)

    async def answer_question(self, question: str) -> Dict[str, Any]:
        """
        Answer a question using the RAG system
        
        Args:
            question: User's question
            
        Returns:
            Dict containing answer and source documents
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
        Get the most relevant chunks for a query without generating an answer
        
        Args:
            query: Search query
            k: Number of chunks to retrieve
            
        Returns:
            List of relevant chunks with their metadata
        """
        if not self.vector_store:
            raise ValueError("Vector store not initialized. Please process documents first.")
            
        docs = self.vector_store.similarity_search(query, k=k)
        return [
            {
                "content": doc.page_content,
                "metadata": doc.metadata
            }
            for doc in docs
        ]
