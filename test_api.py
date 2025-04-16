#!/usr/bin/env python3

import requests
import json
import time
import sys

# Configure the base URL for the API
BASE_URL = "http://localhost:5001"

def test_health():
    """Test the health check endpoint"""
    response = requests.get(f"{BASE_URL}/health")
    data = response.json()
    print(f"Health Check: {data['status']}")
    return response.status_code == 200

def list_executive_orders():
    """List available executive orders"""
    response = requests.get(f"{BASE_URL}/list_executive_orders")
    if response.status_code == 200:
        data = response.json()
        order_ids = data.get("order_ids", [])
        print(f"Found {len(order_ids)} executive orders")
        if order_ids:
            print(f"Sample orders: {', '.join(order_ids[:5])}...")
        return order_ids
    else:
        print(f"Error listing executive orders: {response.status_code}")
        return []

def test_executive_order_query(order_id, question):
    """Test querying a specific executive order"""
    print(f"\n--- Testing Executive Order Query ---")
    print(f"Order ID: {order_id}")
    print(f"Question: {question}")
    
    start_time = time.time()
    response = requests.post(
        f"{BASE_URL}/ask_executive_order",
        json={"order_id": order_id, "question": question}
    )
    elapsed = time.time() - start_time
    
    if response.status_code == 200:
        data = response.json()
        print(f"Response time: {elapsed:.2f} seconds")
        print(f"Answer: {data['answer']}")
        print(f"Found {len(data['excerpts'])} relevant excerpts")
        return True
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return False

def test_search_all_orders(query):
    """Test searching across all executive orders"""
    print(f"\n--- Testing Search Across Executive Orders ---")
    print(f"Query: {query}")
    
    start_time = time.time()
    response = requests.post(
        f"{BASE_URL}/search_all_executive_orders",
        json={"question": query, "top_k": 3}
    )
    elapsed = time.time() - start_time
    
    if response.status_code == 200:
        data = response.json()
        results = data.get("results", [])
        print(f"Response time: {elapsed:.2f} seconds")
        print(f"Found {len(results)} matching chunks")
        
        for i, result in enumerate(results):
            print(f"\nResult {i+1} from order {result['order_id']} (score: {result['score']:.4f}):")
            print(f"{result['text'][:100]}...")
        
        return True
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return False

def test_bill_query(bill_id, question):
    """Test querying a specific bill"""
    print(f"\n--- Testing Bill Query ---")
    print(f"Bill ID: {bill_id}")
    print(f"Question: {question}")
    
    start_time = time.time()
    response = requests.post(
        f"{BASE_URL}/ask",
        json={"bill_id": bill_id, "question": question}
    )
    elapsed = time.time() - start_time
    
    if response.status_code == 200:
        data = response.json()
        print(f"Response time: {elapsed:.2f} seconds")
        print(f"Answer: {data['answer']}")
        print(f"Found {len(data['excerpts'])} relevant excerpts")
        return True
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return False

def main():
    """Run all tests"""
    # Test health endpoint
    if not test_health():
        print("Health check failed, exiting")
        sys.exit(1)
    
    # Test executive order endpoints
    orders = list_executive_orders()
    if orders:
        # Test querying a specific executive order
        sample_order = orders[0]
        test_executive_order_query(
            sample_order, 
            "What is the purpose of this executive order?"
        )
        
        # Test searching across all executive orders
        test_search_all_orders("Climate change and environmental policy")
    
    # Test bill query endpoint with a known bill ID
    test_bill_query(
        "hr-22-119", 
        "What is the purpose of this bill?"
    )
    
    print("\nAll tests completed!")

if __name__ == "__main__":
    main() 