#!/usr/bin/env python3

import os
import logging
from typing import List, Tuple
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class ExecutiveOrderQuerier:
    def __init__(self):
        """Initialize the executive order querier."""
        # Load environment variables
        qdrant_url = os.getenv('QDRANT_URL')
        qdrant_api_key = os.getenv('QDRANT_API_KEY')
        self.collection_name = "executive_order_chunks"

        # Initialize embedding model
        self.embedder = SentenceTransformer('sentence-transformers/all-mpnet-base-v2')
        
        # Initialize Qdrant client
        logger.info(f"Connecting to Qdrant at {qdrant_url}")
        self.qdrant = QdrantClient(
            url=qdrant_url,
            api_key=qdrant_api_key,
        )
        
    def query_order(self, order_id: str, query: str, top_k: int = 3) -> List[Tuple[str, float]]:
        """Query a specific executive order with a natural language query.
        
        Args:
            order_id: The ID of the executive order to query
            query: The natural language query
            top_k: Number of top chunks to return
            
        Returns:
            List of (chunk_text, relevance_score) tuples
        """
        try:
            # Embed the query
            query_vector = self.embedder.encode(query).tolist()
            
            # Create filter for the specific order
            order_filter = Filter(
                must=[
                    FieldCondition(
                        key="order_id",
                        match=MatchValue(value=order_id)
                    )
                ]
            )
            
            # Search for relevant chunks
            search_results = self.qdrant.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                query_filter=order_filter,
                limit=top_k,
                with_payload=True
            )
            
            # Format results
            results = []
            for hit in search_results:
                chunk_text = hit.payload.get("text", "")
                score = hit.score
                results.append((chunk_text, score))
            
            logger.info(f"Found {len(results)} relevant chunks in order {order_id}")
            return results
            
        except Exception as e:
            logger.error(f"Error querying executive order: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def list_all_orders(self) -> List[str]:
        """List all available executive order IDs in the collection.
        
        Returns:
            List of executive order IDs
        """
        try:
            # Execute an aggregation query to get unique order_ids
            aggregation_response = self.qdrant.scroll(
                collection_name=self.collection_name,
                scroll_filter=Filter(),
                limit=10000,  # Adjust as needed
                with_payload=["order_id"],
                with_vectors=False
            )
            
            # Extract unique order IDs
            order_ids = set()
            for point in aggregation_response[0]:
                order_id = point.payload.get("order_id")
                if order_id:
                    order_ids.add(order_id)
            
            logger.info(f"Found {len(order_ids)} executive orders in the collection")
            return sorted(list(order_ids))
            
        except Exception as e:
            logger.error(f"Error listing executive orders: {e}")
            return []
    
    def search_all_orders(self, query: str, top_k: int = 5) -> List[Tuple[str, str, float]]:
        """Search across all executive orders.
        
        Args:
            query: The natural language query
            top_k: Number of top chunks to return
            
        Returns:
            List of (order_id, chunk_text, relevance_score) tuples
        """
        try:
            # Embed the query
            query_vector = self.embedder.encode(query).tolist()
            
            # Search across all orders
            search_results = self.qdrant.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=top_k,
                with_payload=True
            )
            
            # Format results
            results = []
            for hit in search_results:
                order_id = hit.payload.get("order_id", "")
                chunk_text = hit.payload.get("text", "")
                score = hit.score
                results.append((order_id, chunk_text, score))
            
            logger.info(f"Found {len(results)} relevant chunks across all executive orders")
            return results
            
        except Exception as e:
            logger.error(f"Error searching executive orders: {e}")
            return []

if __name__ == "__main__":
    # Example usage
    querier = ExecutiveOrderQuerier()
    
    # List all available orders
    orders = querier.list_all_orders()
    if orders:
        print(f"Available orders: {', '.join(orders[:5])}...")
        
        # Example: query a specific order
        if orders:
            sample_order = orders[0]
            results = querier.query_order(
                sample_order, 
                "What are the main provisions of this order?"
            )
            
            print(f"\nQuery results for order {sample_order}:")
            for i, (text, score) in enumerate(results):
                print(f"Result {i+1} (score: {score:.4f}):")
                print(f"{text[:200]}...\n")
    
    # Example: search across all orders
    results = querier.search_all_orders("climate change initiatives")
    
    print("\nSearch results across all orders:")
    for i, (order_id, text, score) in enumerate(results):
        print(f"Result {i+1} from order {order_id} (score: {score:.4f}):")
        print(f"{text[:200]}...\n") 