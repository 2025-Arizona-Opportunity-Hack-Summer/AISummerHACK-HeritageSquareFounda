import os
from typing import List, Dict, Any
from dotenv import load_dotenv



from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import RetrievalQA

from modules.vector_store.embedder import load_embedding_model
from modules.vector_store.chunker import chunk_text
from modules.vector_store.chroma_store import ChromaVectorStore

from markitdown import MarkItDown

load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

class RAGAgent:
    """
    RAG Agent using Google Gemini via LangChain and ChromaDB for vector search.
    """

    def __init__(self):
        self.embedder = load_embedding_model()
        self.vector_store = ChromaVectorStore(self.embedder)
        self.vector_store.load_index()

        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-pro",
            google_api_key=GOOGLE_API_KEY,
            temperature=0.3,
            convert_system_message_to_human=True
        )

        self.qa_chain = None

    def _setup_qa_chain(self):
        """Set up the RAG chain with prompt and document retriever."""
        prompt_template = """
        You are an AI assistant for Heritage Square Foundation.
        Use the following context to answer the user's question.
        If unsure, say you don't know and avoid guessing.

        Context: {context}

        Question: {question}

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

    def load_pdf_text_with_markitdown(self,file_path: str) -> List[str]:
        md = MarkItDown()
        result = md.convert(file_path)
        text_blocks = result.text_content
        return [text_blocks]

    def process_documents(self, documents: List[str]):
        """Splits and indexes documents in Chroma, then builds QA chain."""
        file_text_blocks = self.load_pdf_text_with_markitdown(documents)
        all_chunks = []
        for block in file_text_blocks:
            chunks = chunk_text(block)
            all_chunks.extend(chunks)

        metadatas = [{"source": f"doc_{i}"} for i in range(len(all_chunks))]
        self.vector_store.create_index(texts=all_chunks, metadatas=metadatas)
        self._setup_qa_chain()

    async def answer_question(self, question: str) -> Dict[str, Any]:
        """Runs RAG pipeline to get an answer with sources."""
        if not self.qa_chain:
            raise ValueError("QA chain not initialized. Run process_documents first.")
        
        response = self.qa_chain.invoke({"query": question})
        # print(result)
        # assert(False)
        return {
            "answer": response['result'],
            "source_documents": [
                {"content": doc.page_content, "metadata": doc.metadata}
                for doc in response["source_documents"]
            ]
        }

    def get_relevant_chunks(self, query: str, k: int = 4) -> List[Dict[str, Any]]:
        """Returns top-k relevant chunks from vector DB without generating an answer."""
        if not self.vector_store:
            raise ValueError("Vector store not initialized.")
        
        chunks = self.vector_store.retrieve(query, k=k)
        return [{"content": type(doc), "metadata": doc} for doc in chunks]
