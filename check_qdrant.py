#!/usr/bin/env python3

import os
from dotenv import load_dotenv
from qdrant_client import QdrantClient

# Load environment variables
load_dotenv()

def check_qdrant_collections():
    """Check which collections exist in Qdrant"""
    # Initialize Qdrant client
    qdrant = QdrantClient(
        url=os.getenv('QDRANT_URL'),
        api_key=os.getenv('QDRANT_API_KEY')
    )
    
    # List all collections
    collections = qdrant.get_collections()
    print(f"Found {len(collections.collections)} collections in Qdrant:")
    
    for collection in collections.collections:
        print(f"- {collection.name}")
        
        # Get detailed collection info
        collection_info = qdrant.get_collection(collection.name)
        points_count = qdrant.count(collection.name).count
        print(f"  Vector size: {collection_info.config.params.vectors.size}")
        print(f"  Points count: {points_count}")
        
        # Get some sample payloads to see the structure
        if points_count > 0:
            samples = qdrant.scroll(
                collection_name=collection.name,
                limit=1,
                with_payload=True
            )[0]
            
            if samples:
                print(f"  Sample payload keys: {list(samples[0].payload.keys())}")
                
                # If it's the executive_order_chunks collection, check order_ids
                if collection.name == "executive_order_chunks" and "order_id" in samples[0].payload:
                    order_ids = set()
                    offset = None
                    limit = 100
                    
                    while True:
                        scroll_result = qdrant.scroll(
                            collection_name=collection.name,
                            limit=limit,
                            with_payload=["order_id"],
                            with_vectors=False,
                            offset=offset
                        )
                        
                        batch = scroll_result[0]
                        if not batch:
                            break
                            
                        for point in batch:
                            order_id = point.payload.get("order_id")
                            if order_id:
                                order_ids.add(order_id)
                        
                        offset = scroll_result[1]
                        
                        if len(batch) < limit:
                            break
                    
                    print(f"  Total unique order_ids: {len(order_ids)}")
                    if order_ids:
                        print(f"  Sample order_ids: {list(order_ids)[:5]}")
        
        print()

if __name__ == "__main__":
    check_qdrant_collections() 