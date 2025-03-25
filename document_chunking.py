import os
import re
import json
from typing import List, Dict, Optional
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
from data_ingestion import BillLoader

# Load environment variables
load_dotenv()

# Configure OpenAI
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4')
MAX_CHUNK_LENGTH = int(os.getenv('MAX_CHUNK_LENGTH', '800'))

class BillChunker:
    def __init__(self, model: str = OPENAI_MODEL):
        """Initialize the bill chunker.
        
        Args:
            model: OpenAI model to use for chunking
        """
        self.model = model
        self.delimiter = "§§"  # Special delimiter unlikely to appear in bills
        
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
        
        # Ensure section headers are on their own lines
        text = re.sub(r'([^\n])(SEC\. \d+\.)', r'\1\n\2', text)
        
        return text.strip()
    
    def chunk_with_gpt(self, text: str) -> List[str]:
        """Use GPT to insert chunk delimiters at semantic boundaries.
        
        Args:
            text: Preprocessed bill text
            
        Returns:
            List of chunks
        """
        system_prompt = (
            "You are a document chunking assistant specialized in U.S. congressional bills. "
            f"Insert the token '{self.delimiter}' at points where the text can be naturally split "
            "into self-contained, semantically coherent chunks. Follow these rules:\n"
            "1. Keep sections together when possible\n"
            "2. If a section is very long, split at logical subsection boundaries\n"
            "3. Never split in the middle of a sentence\n"
            "4. Try to keep related concepts together\n"
            "5. Aim for chunks of roughly similar length\n"
            f"6. Target chunk length is around {MAX_CHUNK_LENGTH} words\n"
            "7. Always keep section headers with their content\n"
            "8. Keep enumerated lists together when possible"
        )
        
        try:
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": text}
                ],
                temperature=0.0  # Use deterministic output
            )
            chunked_text = response.choices[0].message.content
            
            # Split by delimiter and clean chunks
            chunks = [chunk.strip() for chunk in chunked_text.split(self.delimiter)]
            chunks = [chunk for chunk in chunks if chunk]  # Remove empty chunks
            
            return chunks
            
        except Exception as e:
            print(f"Error during GPT chunking: {e}")
            # Fallback: split by sections if GPT fails
            return self.fallback_chunking(text)
    
    def fallback_chunking(self, text: str) -> List[str]:
        """Fallback method: split by sections if GPT fails.
        
        Args:
            text: Preprocessed bill text
            
        Returns:
            List of chunks
        """
        # Split by section headers
        chunks = re.split(r'\n(?=SEC\. \d+\.)', text)
        return [chunk.strip() for chunk in chunks if chunk.strip()]
    
    def process_bill(self, bill_id: str, text: str) -> Dict[str, List[str]]:
        """Process a single bill into chunks.
        
        Args:
            bill_id: Unique identifier for the bill
            text: Raw bill text
            
        Returns:
            Dictionary with bill_id and its chunks
        """
        # Preprocess the text
        cleaned_text = self.preprocess_text(text)
        
        # If text is very long, split into major sections first
        sections = re.split(r'\n(?=SEC\. \d+\.)', cleaned_text)
        
        all_chunks = []
        for section in sections:
            if not section.strip():
                continue
                
            # If section is small enough, keep it as one chunk
            if len(section.split()) <= MAX_CHUNK_LENGTH:
                all_chunks.append(section.strip())
            else:
                # Use GPT to chunk larger sections
                section_chunks = self.chunk_with_gpt(section)
                all_chunks.extend(section_chunks)
        
        return {
            "bill_id": bill_id,
            "chunks": all_chunks
        }

def save_chunks(chunks_data: Dict[str, List[str]], output_dir: str = "data/chunks") -> None:
    """Save chunks to disk.
    
    Args:
        chunks_data: Dictionary with bill_id and chunks
        output_dir: Directory to save chunks
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    bill_id = chunks_data["bill_id"]
    chunks = chunks_data["chunks"]
    
    # Save each chunk with index
    for i, chunk in enumerate(chunks):
        chunk_file = output_path / f"{bill_id}_chunk_{i:03d}.txt"
        chunk_file.write_text(chunk, encoding='utf-8')
    
    # Save metadata
    metadata = {
        "bill_id": bill_id,
        "num_chunks": len(chunks),
        "chunk_files": [f"{bill_id}_chunk_{i:03d}.txt" for i in range(len(chunks))]
    }
    metadata_file = output_path / f"{bill_id}_metadata.json"
    metadata_file.write_text(json.dumps(metadata, indent=2), encoding='utf-8')

if __name__ == "__main__":
    # Example usage
    if not os.getenv('OPENAI_API_KEY'):
        print("Error: OPENAI_API_KEY not found in environment variables")
        print("Please create a .env file based on .env.example")
        exit(1)
    
    # Load bills
    loader = BillLoader()
    bills = loader.load_bills()
    
    if not bills:
        print("No bills found in data/bills directory")
        exit(1)
    
    # Initialize chunker
    chunker = BillChunker()
    
    # Process each bill
    for bill_id, text in bills.items():
        print(f"\nProcessing bill {bill_id}...")
        chunks_data = chunker.process_bill(bill_id, text)
        save_chunks(chunks_data)
        print(f"Created {len(chunks_data['chunks'])} chunks for bill {bill_id}")