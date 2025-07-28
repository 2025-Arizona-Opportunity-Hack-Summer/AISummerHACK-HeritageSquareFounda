import os
import sys
import asyncio

# Adjust path to your backend root
scriptpath = "../"
sys.path.append(os.path.abspath(scriptpath))

from modules.ai_agent.agentv2 import RAGAgent

async def test_retriever():
    agent = RAGAgent()

    query = "What historical restoration methods were used?"
    print(f"\n[TEST QUERY] {query}")

    relevant_chunks = agent.get_relevant_chunks(query, k=5)

    print("\n=== Retrieved Chunks ===")
    for idx, chunk in enumerate(relevant_chunks):
        print(f"\n--- Chunk {idx + 1} ---")
        print(f"Metadata: {chunk['metadata']}")
        print(f"Content: {chunk['content'][:500]}")  # Limit output length
        print("------------------------")

if __name__ == "__main__":
    asyncio.run(test_retriever())
