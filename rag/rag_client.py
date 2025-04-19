import os

from knowledge import Knowledge
from dotenv import load_dotenv
from qdrant_client import models, QdrantClient
from sentence_transformers import SentenceTransformer, CrossEncoder

class RagClient:
    def __init__(self, collection_name) -> None:
        self.encoder = SentenceTransformer("all-MiniLM-L6-v2")
        self.reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L6-v2")
        self.client = QdrantClient(os.environ.get("QDRANT_URI"))
        self.collection_name = collection_name
    
    def __create_rag_db(self, knowledge: Knowledge) -> None:
        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config=models.VectorParams(
                size=self.encoder.get_sentence_embedding_dimension(),
                distance=models.Distance.COSINE,
            )
        )
        
        knowledge_base = knowledge.get_knowledge_base()
        
        self.client.upload_points(
            collection_name=self.collection_name,
            points=[
                models.PointStruct(
                    id=idx, vector=self.encoder.encode(data["content"]).tolist(), payload=data
                )
                for idx, data in enumerate(knowledge_base)
            ],
        )
    
    def get_semantic_search(self, query: str, limit: int = 500):
        hits = self.client.query_points(
            collection_name="owasp_db",
            query=self.encoder.encode(query).tolist(),
            limit=limit,
        ).points
        return [hit.payload for hit in hits]
    
    def rerank_passages(self, query: str, passages: list, top_k: int=20):
        ranks = self.reranker.rank(query, [data["content"] for data in passages])
        ranked_passages = []
        for idx in range(top_k):
            ranked_passages.append(passages[ranks[idx]['corpus_id']])
        return ranked_passages
    
    def get_context(self, query: str, semantic_limit: int = 500, ranked_limit: int = 50):
        semantic_passages = self.get_semantic_search(query=query, limit=semantic_limit)
        ranked_passages = self.rerank_passages(query=query, passages=semantic_passages, top_k=ranked_limit)
        return ranked_passages

if __name__ == "__main__":
    COLLECTION_NAME = "owasp_db"
    OUTPUT_DIR = "./assets/cheatsheets"
    rag = RagClient(collection_name=COLLECTION_NAME)
    knowledge_client = Knowledge(output_dir=OUTPUT_DIR)
    rag.__create_rag_db(knowledge=knowledge_client)