from typing import List
from langchain.text_splitter import RecursiveCharacterTextSplitter

class Chunker:
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ".", " ", ""]
        )

    def chunk_text(self, text: str) -> List[str]:
        return self.splitter.split_text(text)

    def chunk_documents(self, documents: List[str]) -> List[str]:
        all_chunks = []
        for doc in documents:
            chunks = self.chunk_text(doc)
            all_chunks.extend(chunks)
        return all_chunks
    
def chunk_text(text: str) -> List[str]:
    return Chunker().chunk_text(text)
