from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct

class BillEmbedder:
    def __init__(self):
        # Initialize the embedding model
        self.embedder = SentenceTransformer('sentence-transformers/all-mpnet-base-v2')
        
        # Initialize in-memory Qdrant instance
        self.qdrant = QdrantClient(":memory:")
        
        # Create a collection for bill chunks
        self.vector_size = self.embedder.get_sentence_embedding_dimension()
        collection_name = "bill_chunks"
        
        # Check if collection exists, if not create it (fixing deprecation warning)
        if not self.qdrant.collection_exists(collection_name):
            self.qdrant.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=self.vector_size, distance=Distance.COSINE)
            )

    def embed_and_index_chunks(self, bill_chunks):
        """
        Embeds and indexes a list of bill chunks into the vector database.
        Each chunk should be a dict with 'id', 'bill_id', and 'text' keys.
        """
        # Prepare points to upload
        points = []
        for idx, chunk in enumerate(bill_chunks):
            vec = self.embedder.encode(chunk["text"])
            # Create point using PointStruct with integer ID
            point = PointStruct(
                id=idx,  # Use simple integer ID
                vector=vec.tolist(),  # Convert numpy array to list
                payload={
                    "original_id": chunk["id"],  # Store original string ID in payload
                    "bill_id": chunk["bill_id"],
                    "text": chunk["text"]
                }
            )
            points.append(point)
        
        # Upsert in batches
        batch_size = 100
        for i in range(0, len(points), batch_size):
            batch = points[i:i+batch_size]
            self.qdrant.upsert(collection_name="bill_chunks", points=batch)
        
        return len(points)

    def test_embedding(self):
        """
        Simple test to verify embedding functionality
        """
        test_vec = self.embedder.encode("Test embedding for a chunk of text.")
        print(f"Vector dimension: {len(test_vec)}")
        return len(test_vec)

# Example usage:
if __name__ == "__main__":
    # Create an instance of BillEmbedder
    embedder = BillEmbedder()
    
    # Test the embedding
    vector_dim = embedder.test_embedding()
    print(f"Embedding model initialized successfully. Vector dimension: {vector_dim}")
    
    # Example of how to use with actual chunks
    example_chunks = [
        {
            "id": "bill1::chunk0",
            "bill_id": "bill1",
            "text": "This Act may be cited as the 'Example Act of 2024'"
        },
        {
            "id": "bill1::chunk1",
            "bill_id": "bill1",
            "text": "Section 1. The purpose of this Act is to provide an example."
        }
    ]
    
    num_indexed = embedder.embed_and_index_chunks(example_chunks)
    print(f"Successfully indexed {num_indexed} chunks.") 