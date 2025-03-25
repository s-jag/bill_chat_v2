from flask import Flask, request, jsonify
from flask_cors import CORS
import openai
import os
from dotenv import load_dotenv
from embedding import BillEmbedder

# Load environment variables
load_dotenv()

# Set OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")

# Initialize the app
app = Flask(__name__)
CORS(app)

# Initialize the embedder with cloud Qdrant configuration if available
embedder = BillEmbedder(
    qdrant_url=os.getenv("QDRANT_URL"),
    qdrant_api_key=os.getenv("QDRANT_API_KEY")
)

@app.route("/api/health", methods=["GET"])
def health_check():
    """Simple health check endpoint"""
    return jsonify({"status": "healthy"})

@app.route("/api/query", methods=["POST"])
def query_bill():
    """Endpoint to query a bill with a question"""
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "No data provided"}), 400
        
    bill_id = data.get("bill_id")
    question = data.get("question")
    
    if not bill_id or not question:
        return jsonify({"error": "bill_id and question are required"}), 400
    
    # Retrieve relevant chunks
    chunks = embedder.retrieve_chunks(bill_id, question, top_k=5)
    
    # Format chunks for LLM
    system_msg = (
        "You are an expert assistant for answering questions about U.S. congressional bills.\n"
        "You will be given excerpts from a bill and a question. Answer the question based ONLY on the provided excerpts.\n"
        "If the answer is not in the excerpts, say you cannot find that information.\n"
        "If applicable, include the section number or quote from the excerpts in your answer."
    )
    
    user_msg = f"Bill ID: {bill_id}\n\nRelevant Excerpts:\n"
    
    for i, (chunk, score) in enumerate(chunks, start=1):
        user_msg += f"{i}. \"{chunk}\"\n"
    
    user_msg += f"\nQuestion: {question}"
    
    # Get answer from OpenAI
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_msg}
            ]
        )
        answer = response['choices'][0]['message']['content']
    except Exception as e:
        print(f"Error calling OpenAI API: {e}")
        answer = "Sorry, I encountered an error generating a response."
    
    return jsonify({
        "bill_id": bill_id,
        "question": question,
        "answer": answer
    })

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)