import os
import re
import uuid
from typing import List, Dict, Tuple
from pathlib import Path
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.models import Distance, VectorParams, PointStruct
from dotenv import load_dotenv
from data_ingestion import BillLoader

# Load environment variables
load_dotenv()

# Configure chunking parameters
CHUNK_SIZE = int(os.getenv('CHUNK_SIZE', '1000'))  # Character window size
CHUNK_OVERLAP = int(os.getenv('CHUNK_OVERLAP', '200'))  # Overlap between chunks
QDRANT_URL = os.getenv('QDRANT_URL')
QDRANT_API_KEY = os.getenv('QDRANT_API_KEY')
COLLECTION_NAME = "bill_chunks"

class WindowChunker:
    def __init__(self, chunk_size: int = CHUNK_SIZE, chunk_overlap: int = CHUNK_OVERLAP):
        """Initialize the bill window chunker.
        
        Args:
            chunk_size: Size of each chunk in characters
            chunk_overlap: Overlap between chunks in characters
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        # Initialize embedding model
        self.embedder = SentenceTransformer('sentence-transformers/all-mpnet-base-v2')
        self.vector_size = self.embedder.get_sentence_embedding_dimension()
        
        # Initialize Qdrant client with cloud configuration
        print(f"Connecting to Qdrant at {QDRANT_URL}")
        self.qdrant = QdrantClient(
            url=QDRANT_URL,
            api_key=QDRANT_API_KEY,
        )
        
        # Create collection if it doesn't exist
        self._ensure_collection_exists()
        
    def _ensure_collection_exists(self):
        """Ensure the Qdrant collection exists."""
        try:
            if not self.qdrant.collection_exists(COLLECTION_NAME):
                self.qdrant.create_collection(
                    collection_name=COLLECTION_NAME,
                    vectors_config=VectorParams(size=self.vector_size, distance=Distance.COSINE)
                )
                print(f"Created collection '{COLLECTION_NAME}' in Qdrant")
            else:
                print(f"Collection '{COLLECTION_NAME}' already exists in Qdrant")
        except Exception as e:
            print(f"Error checking/creating collection: {e}")
    
    def preprocess_text(self, text: str) -> str:
        """Clean and normalize bill text before chunking.
        
        Args:
            text: Raw bill text
            
        Returns:
            Preprocessed text
        """
        # Remove form feeds and other special characters
        text = text.replace("\f", " ")
        
        # Normalize whitespace
        text = re.sub(r'\n\s*\n+', '\n\n', text)
        
        return text.strip()
    
    def chunk_by_window(self, text: str) -> List[str]:
        """Split text into chunks using a sliding window approach.
        
        Args:
            text: Preprocessed bill text
            
        Returns:
            List of text chunks
        """
        chunks = []
        # If text is shorter than chunk size, return as single chunk
        if len(text) <= self.chunk_size:
            return [text]
        
        # Split by sliding window with overlap
        start = 0
        while start < len(text):
            end = start + self.chunk_size
            
            if end >= len(text):
                # Last chunk
                chunk = text[start:]
            else:
                # Find a good boundary (sentence or paragraph end)
                # Try to find a paragraph end
                boundary = text.rfind('\n\n', start, end)
                if boundary == -1 or boundary < start + self.chunk_size // 2:
                    # Try to find a sentence end
                    for punct in ['. ', '! ', '? ', '.\n', '!\n', '?\n']:
                        boundary = text.rfind(punct, start, end)
                        if boundary != -1 and boundary > start + self.chunk_size // 2:
                            boundary += 1  # Include the punctuation
                            break
                
                if boundary == -1 or boundary < start + self.chunk_size // 2:
                    # If no good boundary, just use the window
                    boundary = end
                
                chunk = text[start:boundary]
            
            if chunk.strip():  # Only add non-empty chunks
                chunks.append(chunk.strip())
            
            # Move start position for next chunk, with overlap
            next_start = start + self.chunk_size - self.chunk_overlap
            
            # Avoid getting stuck in the same position
            if next_start <= start:
                next_start = start + 1
                
            start = next_start
            
        return chunks
    
    def process_and_embed_bill(self, bill_id: str, text: str) -> Tuple[int, int]:
        """Process, chunk, and embed a bill directly to Qdrant.
        
        Args:
            bill_id: Bill identifier
            text: Bill text
            
        Returns:
            Tuple of (number of chunks, number of characters)
        """
        # Preprocess the text
        cleaned_text = self.preprocess_text(text)
        
        # Split into chunks
        chunks = self.chunk_by_window(cleaned_text)
        
        # Create points for Qdrant
        points = []
        for idx, chunk_text in enumerate(chunks):
            # Generate a unique ID for this chunk
            chunk_id = f"{bill_id}_chunk_{idx}"
            
            # Create a numeric ID by hashing the chunk_id string
            # Use UUID to ensure uniqueness across all bills
            point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, chunk_id))
            
            # Embed the chunk text
            embedding = self.embedder.encode(chunk_text)
            
            # Create a point
            point = PointStruct(
                id=point_id,  # Use UUID as the point ID
                vector=embedding.tolist(),
                payload={
                    "bill_id": bill_id,
                    "chunk_index": idx,
                    "text": chunk_text,
                    "chunk_id": chunk_id
                }
            )
            points.append(point)
        
        # Upsert all points to Qdrant
        if points:
            try:
                # Delete existing chunks for this bill to avoid duplicates
                print(f"Removing previous chunks for bill {bill_id}...")
                self.qdrant.delete(
                    collection_name=COLLECTION_NAME,
                    points_selector=models.FilterSelector(
                        filter=models.Filter(
                            must=[
                                models.FieldCondition(
                                    key="bill_id",
                                    match=models.MatchValue(value=bill_id)
                                )
                            ]
                        )
                    )
                )
                
                # Upsert new chunks in batches of 100
                print(f"Uploading {len(points)} chunks for bill {bill_id}...")
                batch_size = 100
                for i in range(0, len(points), batch_size):
                    batch = points[i:i+batch_size]
                    self.qdrant.upsert(
                        collection_name=COLLECTION_NAME,
                        points=batch,
                        wait=True
                    )
                
                print(f"Successfully embedded and stored {len(chunks)} chunks for bill {bill_id}")
            except Exception as e:
                print(f"Error while uploading to Qdrant: {e}")
                # Print more detailed error information
                import traceback
                traceback.print_exc()
        
        return len(chunks), sum(len(chunk) for chunk in chunks)

def process_all_bills():
    """Process all bills in the data directory and embed them to Qdrant."""
    chunker = WindowChunker()
    loader = BillLoader()
    bills = loader.load_bills()
    
    if not bills:
        print("No bills found in data/bills directory")
        return
    
    total_chunks = 0
    total_chars = 0
    
    for bill_id, text in bills.items():
        print(f"\nProcessing bill {bill_id}...")
        num_chunks, num_chars = chunker.process_and_embed_bill(bill_id, text)
        total_chunks += num_chunks
        total_chars += num_chars
    
    print(f"\nProcessing complete!")
    print(f"Total bills processed: {len(bills)}")
    print(f"Total chunks created: {total_chunks}")
    print(f"Total characters processed: {total_chars}")

if __name__ == "__main__":
    process_all_bills() 