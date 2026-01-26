from llama_index.core import VectorStoreIndex, get_response_synthesizer
from llama_index.core.query_engine import RetrieverQueryEngine
from src.inference.custom_retriever import TypeDBHybridRetriever
import os

# Mock OpenAI Key if not set (for demo purposes without hitting API if we mock the synthesizer too, 
# but LlamaIndex needs a key usually. We will rely on user having one or just demonstrating the retrieval part).
# os.environ["OPENAI_API_KEY"] = "sk-..." 

def run_agent_demo():
    print("🤖 Initializing Riemann AI Agent...")
    
    # 1. Initialize Custom Retriever
    retriever = TypeDBHybridRetriever()
    
    # 2. Configure Response Synthesizer (The part that generates the final answer)
    # Using 'compact' mode to just concatenate the retrieved texts for now if direct LLM call is tricky without key.
    # In a real scenario: synthesizer = get_response_synthesizer(response_mode="compact")
    
    # 3. Create Query Engine
    # query_engine = RetrieverQueryEngine(retriever=retriever, response_synthesizer=synthesizer)
    
    # For this demo, let's just run the retrieval manually to show it working within the LlamaIndex structure
    # since we might not have a valid OpenAI key in this environment.
    
    query_str = "Alice가 작성한 문서들에 대해 알려줘"
    print(f"\n🗣️ User Query: {query_str}")
    
    nodes = retriever.retrieve(query_str)
    
    print(f"\n📝 [Agent Response Generation]")
    print(f"Retrieved {len(nodes)} context chunks for LLM synthesis.")
    for i, node in enumerate(nodes):
        print(f"\n--- Context Chunk {i+1} ---")
        print(node.node.get_text()[:200] + "...")

    # Simulated Final Answer
    if nodes:
        print("\n💡 [Simulated LLM Output]:")
        print(f"Alice Engineer님은 총 {len(nodes)}개의 문서를 작성했습니다.")
        print("첫 번째는 'Project Riemann Architecture Overview'로, TypeDB와 Postgres를 결합한 하이브리드 아키텍처를 설명하고 있습니다.")
        print("두 번째는 'Q1 2026 Roadmap'이며, LlamaIndex 통합 및 Airflow 파이프라인 구축 계획을 담고 있습니다.")

if __name__ == "__main__":
    run_agent_demo()
