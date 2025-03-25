import os
from openai import OpenAI
from typing import List, Tuple, Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class BillQA:
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the QA system with OpenAI API key.
        If api_key is None, it will try to use the OPENAI_API_KEY environment variable.
        """
        # Use provided API key or fall back to environment variable
        api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OpenAI API key must be provided either through initialization or OPENAI_API_KEY environment variable")
        
        self.client = OpenAI(api_key=api_key)
        
        self.system_prompt = """You are an expert assistant for answering questions about U.S. congressional bills.
Your task is to answer questions based ONLY on the provided bill excerpts.
Follow these rules strictly:
1. Only use information from the provided excerpts
2. If the answer isn't in the excerpts, say "I cannot find this information in the provided excerpts"
3. When quoting the bill, use exact quotes and cite the relevant section if available
4. If multiple excerpts are relevant, synthesize them but maintain accuracy
5. If a section number is mentioned in the question, prioritize information from that section
6. Be direct and concise in your answers
7. If there's ambiguity in the bill text, acknowledge it
8. Do not make assumptions beyond what's explicitly stated
9. If you quote text, use quotation marks and cite the section if available"""

    def format_chunks_for_prompt(self, chunks: List[Tuple[str, float]]) -> str:
        """
        Format the retrieved chunks into a clear prompt format.
        chunks: List of (text, score) tuples
        """
        formatted_chunks = []
        for i, (text, score) in enumerate(chunks, 1):
            # Clean up the text
            clean_text = text.replace('\n', ' ').strip()
            clean_text = ' '.join(clean_text.split())  # Normalize whitespace
            formatted_chunks.append(f"Excerpt {i} (relevance: {score:.2f}):\n{clean_text}\n")
        
        return "\n".join(formatted_chunks)

    def answer_question(self, 
                       question: str, 
                       bill_id: str, 
                       chunks: List[Tuple[str, float]], 
                       model: str = "gpt-4") -> str:
        """
        Generate an answer to the question using the provided chunks.
        
        Args:
            question: The user's question
            bill_id: The ID of the bill being queried
            chunks: List of (text, score) tuples from retrieval
            model: The OpenAI model to use
        
        Returns:
            str: The generated answer
        """
        # Format the chunks
        context = self.format_chunks_for_prompt(chunks)
        
        # Construct the user message
        user_message = f"""Bill ID: {bill_id}

Relevant excerpts from the bill:
{context}

Question: {question}"""

        # Call the API
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0,  # Keep it factual
                max_tokens=500  # Limit response length
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"Error generating answer: {str(e)}"

# Example usage and testing
if __name__ == "__main__":
    from embedding import BillEmbedder
    
    # Initialize the QA system
    qa = BillQA()
    
    # Initialize the embedding system
    embedder = BillEmbedder()
    
    # Load and index chunks
    chunks = embedder.load_chunks_from_directory()
    num_indexed = embedder.embed_and_index_chunks(chunks)
    print(f"Indexed {num_indexed} chunks.")
    
    # Get the bill ID from the first chunk
    test_bill_id = chunks[0]["bill_id"] if chunks else "hr-3334-118"
    
    # Test questions
    test_questions = [
        "What is the short title of this bill?",
        "What is the purpose of this bill?",
        "What sanctions are mentioned in this bill?",
        "When does this act take effect?",
        "What is in Section 1 of this bill?"
    ]
    
    print("\nTesting QA System:")
    for question in test_questions:
        print(f"\nQuestion: {question}")
        
        # Retrieve relevant chunks
        relevant_chunks = embedder.retrieve_chunks(test_bill_id, question, top_k=3)
        
        # Generate answer
        answer = qa.answer_question(question, test_bill_id, relevant_chunks)
        print(f"Answer: {answer}\n")
        print("-" * 80) 