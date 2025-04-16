from flask import Flask, jsonify, request
from flask_cors import CORS
import os
from dotenv import load_dotenv
from openai import OpenAI
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from datetime import datetime

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# Initialize clients
openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
embedder = SentenceTransformer('sentence-transformers/all-mpnet-base-v2')
qdrant = QdrantClient(
    url=os.getenv('QDRANT_URL'),
    api_key=os.getenv('QDRANT_API_KEY')
)

@app.route('/')
def home():
    return jsonify({"message": "Welcome to the Bill Q&A API"})

@app.route('/ask', methods=['POST'])
def ask():
    data = request.get_json()
    if not data or 'bill_id' not in data or 'question' not in data:
        return jsonify({"error": "bill_id and question are required"}), 400

    # Get relevant chunks
    query_vector = embedder.encode(data['question']).tolist()
    search_result = qdrant.search(
        collection_name="bill_chunks",
        query_vector=query_vector,
        query_filter={"must": [{"key": "bill_id", "match": {"value": data['bill_id']}}]},
        limit=data.get('top_k', 3)
    )

    # Format chunks for GPT
    chunks_text = "\n\n".join([
        f"Excerpt {i+1}:\n{hit.payload['text']}"
        for i, hit in enumerate(search_result)
    ])

    # Get answer from GPT
    completion = openai_client.chat.completions.create(
        model=os.getenv("OPENAI_MODEL", "gpt-4"),
        messages=[
            {"role": "system", "content": "Answer questions about bills based only on the provided excerpts. Be direct and concise."},
            {"role": "user", "content": f"Bill ID: {data['bill_id']}\n\nRelevant excerpts:\n{chunks_text}\n\nQuestion: {data['question']}"}
        ],
        temperature=0
    )

    return jsonify({
        "answer": completion.choices[0].message.content,
        "excerpts": [hit.payload["text"] for hit in search_result]
    })

@app.route('/ask_executive_order', methods=['POST'])
def ask_executive_order():
    data = request.get_json()
    if not data or 'order_id' not in data or 'question' not in data:
        return jsonify({"error": "order_id and question are required"}), 400

    # Get relevant chunks
    query_vector = embedder.encode(data['question']).tolist()
    search_result = qdrant.search(
        collection_name="executive_order_chunks",
        query_vector=query_vector,
        query_filter={"must": [{"key": "order_id", "match": {"value": data['order_id']}}]},
        limit=data.get('top_k', 3)
    )

    # Format chunks for GPT
    chunks_text = "\n\n".join([
        f"Excerpt {i+1}:\n{hit.payload['text']}"
        for i, hit in enumerate(search_result)
    ])

    # Get answer from GPT
    completion = openai_client.chat.completions.create(
        model=os.getenv("OPENAI_MODEL", "gpt-4"),
        messages=[
            {"role": "system", "content": "Answer questions about executive orders based only on the provided excerpts. Be direct and concise."},
            {"role": "user", "content": f"Executive Order ID: {data['order_id']}\n\nRelevant excerpts:\n{chunks_text}\n\nQuestion: {data['question']}"}
        ],
        temperature=0
    )

    return jsonify({
        "answer": completion.choices[0].message.content,
        "excerpts": [hit.payload["text"] for hit in search_result]
    })

@app.route('/search_all_executive_orders', methods=['POST'])
def search_all_executive_orders():
    data = request.get_json()
    if not data or 'question' not in data:
        return jsonify({"error": "question is required"}), 400

    # Get relevant chunks across all executive orders
    query_vector = embedder.encode(data['question']).tolist()
    search_result = qdrant.search(
        collection_name="executive_order_chunks",
        query_vector=query_vector,
        limit=data.get('top_k', 5),
        with_payload=True
    )

    # Format results
    results = []
    for hit in search_result:
        results.append({
            "order_id": hit.payload.get("order_id"),
            "text": hit.payload.get("text"),
            "score": hit.score
        })

    return jsonify({
        "results": results
    })

@app.route('/list_executive_orders', methods=['GET'])
def list_executive_orders():
    try:
        # Use scroll to retrieve all points with order_id in payload
        scroll_result = qdrant.scroll(
            collection_name="executive_order_chunks",
            scroll_filter={},
            limit=10000,
            with_payload=["order_id"],
            with_vectors=False
        )
        
        # Extract unique order_ids
        order_ids = set()
        for point in scroll_result[0]:
            order_id = point.payload.get("order_id")
            if order_id:
                order_ids.add(order_id)
        
        return jsonify({
            "order_ids": sorted(list(order_ids))
        })
    except Exception as e:
        return jsonify({"error": f"Error listing executive orders: {str(e)}"}), 500

@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "bill-chat-api"
    }) 