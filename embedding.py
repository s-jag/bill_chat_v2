from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct, Filter, FieldCondition, MatchValue
import re
import json
import os
from glob import glob

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

    def load_chunks_from_directory(self, chunks_dir="data/chunks"):
        """
        Load chunks from the data/chunks directory for a bill.
        Returns a list of dictionaries containing chunk information.
        """
        chunks = []
        
        # Find all metadata files
        metadata_files = glob(os.path.join(chunks_dir, "*_metadata.json"))
        
        for metadata_file in metadata_files:
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
                bill_id = metadata['bill_id']
                
                # Load each chunk file
                for chunk_file in metadata['chunk_files']:
                    chunk_path = os.path.join(chunks_dir, chunk_file)
                    if os.path.exists(chunk_path):
                        with open(chunk_path, 'r') as cf:
                            text = cf.read().strip()
                            chunks.append({
                                "id": f"{bill_id}::{chunk_file}",
                                "bill_id": bill_id,
                                "text": text
                            })
        
        return chunks

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

    def retrieve_chunks(self, bill_id, query, top_k=5):
        """
        Retrieve relevant chunks for a query from a specific bill.
        Includes special handling for section-specific queries.
        """
        # Create the filter condition for bill_id
        bill_filter = Filter(
            must=[
                FieldCondition(
                    key="bill_id",
                    match=MatchValue(value=bill_id)
                )
            ]
        )

        # Check if query references a specific section number
        sec_match = re.search(r'\b[Ss]ection\s+(\d+)\b', query)
        explicit_section_chunk = None
        
        if sec_match:
            sec_num = sec_match.group(1)
            # Search for the specific section
            section_hits = self.qdrant.search(
                collection_name="bill_chunks",
                query_vector=self.embedder.encode(f"Section {sec_num}").tolist(),
                query_filter=bill_filter,
                limit=1
            )
            if section_hits:
                explicit_section_chunk = (
                    section_hits[0].payload.get("text"),
                    section_hits[0].score
                )
        
        # Perform normal semantic search
        query_vec = self.embedder.encode(query).tolist()
        hits = self.qdrant.search(
            collection_name="bill_chunks",
            query_vector=query_vec,
            query_filter=bill_filter,
            limit=top_k
        )
        
        # Combine results, avoiding duplicates
        results = []
        seen_texts = set()
        
        # Add section-specific result first if found
        if explicit_section_chunk and explicit_section_chunk[0] not in seen_texts:
            results.append(explicit_section_chunk)
            seen_texts.add(explicit_section_chunk[0])
        
        # Add semantic search results
        for hit in hits:
            text = hit.payload.get("text")
            if text not in seen_texts:
                results.append((text, hit.score))
                seen_texts.add(text)
        
        return results[:top_k]

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
    
    # Load and index actual chunks from the data directory
    chunks = embedder.load_chunks_from_directory()
    print(f"\nFound {len(chunks)} chunks to index.")
    
    # Index the chunks
    num_indexed = embedder.embed_and_index_chunks(chunks)
    print(f"Successfully indexed {num_indexed} chunks.")
    
    # Test retrieval
    print("\nTesting retrieval:")
    
    # Get the bill ID from the first chunk for testing
    test_bill_id = chunks[0]["bill_id"] if chunks else "hr-3334-118"
    
    # Test general query
    query1 = "What is the short title of this bill?"
    results1 = embedder.retrieve_chunks(test_bill_id, query1, top_k=2)
    print(f"\nResults for query: '{query1}'")
    for text, score in results1:
        print(f"Score {score:.3f}: {text[:200]}...")
    
    # Test section-specific query
    query2 = "What is in Section 1?"
    results2 = embedder.retrieve_chunks(test_bill_id, query2, top_k=2)
    print(f"\nResults for query: '{query2}'")
    for text, score in results2:
        print(f"Score {score:.3f}: {text[:200]}...")