#vector.py
import os
from typing import List

from modules.vector_store.embedder import load_embedding_model
from modules.vector_store.chunker import chunk_text
from modules.vector_store.chroma_store import ChromaVectorStore

from markitdown import MarkItDown


def load_pdf_text_with_markitdown(file_path: str) -> List[str]:
    """Extracts clean text blocks from a PDF using Markitdown."""

    md = MarkItDown()
    result = md.convert(file_path)
    # print(result.text_content)
    # result = pipeline_from_file(file_path)
    text_blocks = result.text_content
    return text_blocks


def process_and_store_documents(file_path: str, metadata: dict = None):
    """Pipeline to process a PDF using Markitdown: load, chunk, embed, and store."""
    text_blocks = load_pdf_text_with_markitdown(file_path)

    # basic PLACEHOLDER now....have to check the text_blocks structure
    all_chunks = []
    for block in text_blocks:
        chunks = chunk_text(block)
        all_chunks.extend(chunks)
    #PLACEHOLDER FOR LOADING embedding model...have to write it in embedder.py
    embedding_model = load_embedding_model()#have to strore in chromaDB now
    vector_store = ChromaVectorStore(embedding_model)

    vector_store.create_index(
        texts=all_chunks,
        metadatas=[metadata or {"source": os.path.basename(file_path)}] * len(all_chunks)
    )
