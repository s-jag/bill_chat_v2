#!/usr/bin/env python3

import os
import re
import uuid
import logging
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.models import Distance, VectorParams, PointStruct
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Configure chunking parameters
CHUNK_SIZE = int(os.getenv('CHUNK_SIZE', '1000'))  # Character window size
CHUNK_OVERLAP = int(os.getenv('CHUNK_OVERLAP', '200'))  # Overlap between chunks
QDRANT_URL = os.getenv('QDRANT_URL')
QDRANT_API_KEY = os.getenv('QDRANT_API_KEY')
COLLECTION_NAME = "executive_order_chunks"  # Different collection from bills

class EOChunker:
    def __init__(self, chunk_size: int = CHUNK_SIZE, chunk_overlap: int = CHUNK_OVERLAP):
        """Initialize the executive order window chunker.
        
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
        logger.info(f"Connecting to Qdrant at {QDRANT_URL}")
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
                logger.info(f"Created collection '{COLLECTION_NAME}' in Qdrant")
            else:
                logger.info(f"Collection '{COLLECTION_NAME}' already exists in Qdrant")
        except Exception as e:
            logger.error(f"Error checking/creating collection: {e}")
    
    def preprocess_text(self, text: str) -> str:
        """Clean and normalize executive order text before chunking.
        
        Args:
            text: Raw executive order text
            
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
            text: Text to split into chunks
            
        Returns:
            List of text chunks
        """
        chunks = []
        start = 0
        text_length = len(text)
        
        while start < text_length:
            # Calculate end position with overlap
            end = min(start + self.chunk_size, text_length)
            
            # If we're not at the end of the text, try to find a good breaking point
            if end < text_length:
                # Look for a paragraph break within the last 20% of the chunk
                last_fifth_start = max(start, end - int(self.chunk_size * 0.2))
                last_paragraph_break = text.rfind("\n\n", last_fifth_start, end)
                
                if last_paragraph_break != -1:
                    end = last_paragraph_break
                else:
                    # If no paragraph break, look for sentence end (period, question mark, exclamation mark)
                    last_sentence_end = max(
                        text.rfind(". ", last_fifth_start, end),
                        text.rfind("? ", last_fifth_start, end),
                        text.rfind("! ", last_fifth_start, end)
                    )
                    
                    if last_sentence_end != -1:
                        end = last_sentence_end + 1  # Include the period
                    else:
                        # If no good breaking point, just break at a space
                        last_space = text.rfind(" ", last_fifth_start, end)
                        if last_space != -1:
                            end = last_space
            
            # Extract the chunk and add to list
            chunk = text[start:end].strip()
            if chunk:  # Only add non-empty chunks
                chunks.append(chunk)
            
            # Calculate the next start position with overlap
            next_start = min(end, text_length)
            if end < text_length:
                # Move back by overlap characters, but not before the current start
                next_start = max(start + 1, end - self.chunk_overlap)
            
            # Prevent infinite loop if we couldn't move forward
            if next_start <= start:
                next_start = start + 1
                
            start = next_start
            
        return chunks
    
    def process_and_embed_order(self, order_id: str, text: str) -> Tuple[int, int]:
        """Process, chunk, and embed an executive order directly to Qdrant.
        
        Args:
            order_id: Executive order identifier
            text: Executive order text
            
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
            chunk_id = f"{order_id}_chunk_{idx}"
            
            # Create a numeric ID by hashing the chunk_id string
            point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, chunk_id))
            
            # Embed the chunk text
            embedding = self.embedder.encode(chunk_text)
            
            # Create a point
            point = PointStruct(
                id=point_id,
                vector=embedding.tolist(),
                payload={
                    "order_id": order_id,
                    "chunk_index": idx,
                    "text": chunk_text,
                    "chunk_id": chunk_id
                }
            )
            points.append(point)
        
        # Upsert all points to Qdrant
        if points:
            try:
                # Delete existing chunks for this order to avoid duplicates
                logger.info(f"Removing previous chunks for order {order_id}...")
                self.qdrant.delete(
                    collection_name=COLLECTION_NAME,
                    points_selector=models.FilterSelector(
                        filter=models.Filter(
                            must=[
                                models.FieldCondition(
                                    key="order_id",
                                    match=models.MatchValue(value=order_id)
                                )
                            ]
                        )
                    )
                )
                
                # Upsert new chunks in batches of 100
                logger.info(f"Uploading {len(points)} chunks for order {order_id}...")
                batch_size = 100
                for i in range(0, len(points), batch_size):
                    batch = points[i:i+batch_size]
                    self.qdrant.upsert(
                        collection_name=COLLECTION_NAME,
                        points=batch,
                        wait=True
                    )
                
                logger.info(f"Successfully embedded and stored {len(chunks)} chunks for order {order_id}")
            except Exception as e:
                logger.error(f"Error while uploading to Qdrant: {e}")
                import traceback
                traceback.print_exc()
        
        return len(chunks), sum(len(chunk) for chunk in chunks)

def load_executive_orders(data_dir: str = "data/executive_orders") -> Dict[str, str]:
    """Load all executive orders from the data directory.
    
    Args:
        data_dir: Path to directory containing executive order files
    
    Returns:
        Dict mapping order_id to order text
    """
    orders = {}
    data_path = Path(data_dir)
    
    if not data_path.exists():
        logger.warning(f"Directory {data_dir} does not exist")
        return orders
    
    for file in data_path.glob("*.txt"):
        order_id = file.stem  # filename without extension
        orders[order_id] = file.read_text(encoding='utf-8')
        logger.info(f"Loaded order {order_id} with {len(orders[order_id])} characters")
    
    return orders

def process_all_orders():
    """Process all executive orders in the data directory and embed them to Qdrant."""
    chunker = EOChunker()
    orders = load_executive_orders()
    
    if not orders:
        logger.warning("No executive orders found in data/executive_orders directory")
        return
    
    total_chunks = 0
    total_chars = 0
    
    for order_id, text in orders.items():
        logger.info(f"Processing order {order_id}...")
        num_chunks, num_chars = chunker.process_and_embed_order(order_id, text)
        total_chunks += num_chunks
        total_chars += num_chars
    
    logger.info(f"Processing complete!")
    logger.info(f"Total orders processed: {len(orders)}")
    logger.info(f"Total chunks created: {total_chunks}")
    logger.info(f"Total characters processed: {total_chars}")

if __name__ == "__main__":
    process_all_orders() 