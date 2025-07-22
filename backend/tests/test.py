import asyncio
from backend.modules.ai_agent.agent import RAGAgent

async def test_rag_agent():
    # Initialize the RAG agent with your Google Cloud project ID
    agent = RAGAgent(project_id="your-project-id")
    
    # Example documents
    documents = [
        """Heritage Square Foundation is a historic preservation organization dedicated to 
        preserving and promoting cultural heritage. Founded in 1985, we maintain several 
        historic buildings and organize educational programs.""",
        
        """Our annual fundraising gala in 2023 raised $250,000 for restoration projects. 
        The event was attended by 300 donors and community leaders."""
    ]
    
    # Process the documents
    agent.process_documents(documents)
    
    # Test question answering
    question = "When was Heritage Square Foundation founded and what do they do?"
    result = await agent.answer_question(question)
    
    print("Question:", question)
    print("\nAnswer:", result["answer"])
    print("\nSource Documents:")
    for doc in result["source_documents"]:
        print(f"\n- Content: {doc['content']}")
        print(f"  Metadata: {doc['metadata']}")

if __name__ == "__main__":
    asyncio.run(test_rag_agent())
