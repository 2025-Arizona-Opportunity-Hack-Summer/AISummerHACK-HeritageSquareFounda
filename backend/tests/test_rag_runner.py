import os
import asyncio
import sys

scriptpath = "../"
sys.path.append(os.path.abspath(scriptpath))

from modules.vector_store.vector_pipeline import process_and_store_documents
from modules.ai_agent.agentv2 import RAGAgent
from modules.vector_store.chunker import chunk_text

def load_all_pdfs_from_directory(directory: str) -> list:
    """
    Recursively read all .pdf files from the given directory
    and return a list of their paths.
    """
    pdf_paths = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".pdf"):
                pdf_paths.append(os.path.join(root, file))
    return pdf_paths

async def run_test_query():
    agent = RAGAgent()
    print("[INFO] Agent initialized")

    pdf_folder_path = "testPdfs/"  # Adjust path as needed
    print(f"[INFO] Loading PDFs from: {pdf_folder_path}")
    pdf_paths = load_all_pdfs_from_directory(pdf_folder_path)

    print(f"[INFO] Found {len(pdf_paths)} PDFs to process...")
    for path in pdf_paths:
        print(f" → Processing: {path}")
        agent.process_documents(path)
    
    # question = "What are the restoration techniques mentioned in the documents?"
    question = "Umm...i had interview with Mayor John Driggs, where did he say he was born? and could you give his date of birth too?"
    print(f"[QUERY] {question}")
    response = await agent.answer_question(question)

    print("\n=== Answer ===")
    print(response["answer"])
    
    print("\n=== Source Documents ===")
    for idx, src in enumerate(response["source_documents"]):
        print(f"[{idx+1}] {src['metadata']}")

if __name__ == "__main__":
    asyncio.run(run_test_query())
