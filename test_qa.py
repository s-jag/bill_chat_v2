import os
import uuid
from dotenv import load_dotenv
from openai import OpenAI
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue

# Load environment variables
load_dotenv()

# Initialize clients
openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
embedder = SentenceTransformer('sentence-transformers/all-mpnet-base-v2')
qdrant = QdrantClient(
    url=os.getenv('QDRANT_URL'),
    api_key=os.getenv('QDRANT_API_KEY')
)

COLLECTION_NAME = "bill_chunks"

def retrieve_chunks(bill_id, query, top_k=3):
    """Retrieve relevant chunks for a query from a specific bill."""
    try:
        # Create query vector
        query_vector = embedder.encode(query).tolist()
        
        # Create the filter condition for bill_id
        bill_filter = Filter(
            must=[
                FieldCondition(
                    key="bill_id",
                    match=MatchValue(value=bill_id)
                )
            ]
        )
        
        # Search Qdrant
        hits = qdrant.search(
            collection_name=COLLECTION_NAME,
            query_vector=query_vector,
            query_filter=bill_filter,
            limit=top_k,
            with_payload=True
        )
        
        # Format results
        results = []
        for hit in hits:
            results.append((hit.payload.get("text"), hit.score))
        
        return results
    except Exception as e:
        print(f"Error retrieving chunks: {e}")
        import traceback
        traceback.print_exc()
        return []

def answer_question(bill_id, question, chunks):
    """Generate an answer to the question using the provided chunks."""
    try:
        if not chunks:
            return "No relevant information found for this question."
            
        # Format chunks for prompt
        chunks_text = "\n\n".join([
            f"Excerpt {i+1} (relevance: {score:.2f}):\n{text}"
            for i, (text, score) in enumerate(chunks)
        ])
        
        # Create prompt
        prompt = f"""Bill ID: {bill_id}

Relevant excerpts from the bill:
{chunks_text}

Question: {question}"""

        # Call OpenAI
        response = openai_client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"),
            messages=[
                {"role": "system", "content": "You are an expert assistant for answering questions about U.S. congressional bills. Your task is to answer questions based ONLY on the provided bill excerpts. Be direct and concise."},
                {"role": "user", "content": prompt}
            ],
            temperature=0
        )
        
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error generating answer: {e}")
        import traceback
        traceback.print_exc()
        return f"Error generating answer: {str(e)}"

def test_bill_qa():
    """Test the Q&A functionality with different bills and questions."""
    # Get list of available bills (first check if collection exists)
    try:
        if not qdrant.collection_exists(COLLECTION_NAME):
            print(f"Collection '{COLLECTION_NAME}' doesn't exist in Qdrant")
            return
        
        # Get list of unique bill_ids
        print("Retrieving available bill IDs from Qdrant...")
        
        # Use scroll to get all unique bill_ids
        points = []
        offset = None
        limit = 100  # Batch size
        
        while True:
            scroll_result = qdrant.scroll(
                collection_name=COLLECTION_NAME,
                limit=limit,
                with_payload=["bill_id"],
                with_vectors=False,
                offset=offset
            )
            
            batch = scroll_result[0]
            if not batch:
                break
                
            points.extend(batch)
            
            # Update offset for the next iteration
            offset = scroll_result[1]
            
            # If returned less than the limit, we've reached the end
            if len(batch) < limit:
                break
        
        # Extract unique bill_ids
        bill_ids = set()
        for point in points:
            bill_id = point.payload.get("bill_id")
            if bill_id:
                bill_ids.add(bill_id)
        
        bill_ids = sorted(list(bill_ids))
        
        if not bill_ids:
            print("No bills found in the Qdrant collection")
            return
            
        print(f"Found {len(bill_ids)} bills in Qdrant: {', '.join(bill_ids)}")
        
        # Test questions for each bill
        test_questions = [
            "What is the short title of this bill?",
            "What is the purpose of this bill?",
            "When does this act take effect?",
            "What are the key provisions of this bill?"
        ]
        
        # Test the first bill with all questions
        test_bill = bill_ids[0]
        print(f"\nTesting Q&A with bill: {test_bill}")
        
        for question in test_questions:
            print(f"\nQuestion: {question}")
            
            # Get relevant chunks
            chunks = retrieve_chunks(test_bill, question)
            print(f"Retrieved {len(chunks)} chunks")
            
            # If chunks were found, get an answer
            if chunks:
                answer = answer_question(test_bill, question, chunks)
                print(f"Answer: {answer}")
            else:
                print("No relevant chunks found")
                
        print("\nTesting complete!")
            
    except Exception as e:
        print(f"Error during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_bill_qa() 