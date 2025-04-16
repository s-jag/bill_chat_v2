from flask import Flask, jsonify, request
from flask_cors import CORS
import os
from dotenv import load_dotenv
from openai import OpenAI
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# Initialize clients
openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY', "default"))
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