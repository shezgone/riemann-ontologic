import sys
import os

# Add the project root to sys.path to resolve imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from src.inference.custom_retriever import TypeDBHybridRetriever

def ask(question):
    print(f"🤔 질문: {question}")
    
    retriever = TypeDBHybridRetriever()
    nodes = retriever.retrieve(question)
    
    print(f"\n✅ 검색 결과 ({len(nodes)}건):")
    for i, node in enumerate(nodes):
        print(f"\n[결과 {i+1}]")
        print(node.node.get_text())

if __name__ == "__main__":
    current_query = "Alice가 작성한 문서는?"
    ask(current_query)
