# I'll create a simple data ingestion system with the following structure:
# A data directory to store bill texts
# A Python script to load and process these bills
# A function to load bills from the data directory
# A function to add new bills to the data directory

import os
import json
from pathlib import Path
from typing import Dict, Optional

class BillLoader:
    def __init__(self, data_dir: str = "data/bills"):
        """Initialize the bill loader with path to data directory."""
        self.data_dir = Path(data_dir)
        self.bills: Dict[str, str] = {}
        
    def load_bills(self) -> Dict[str, str]:
        """Load all bills from the data directory.
        
        Returns:
            Dict mapping bill_id to bill text
        """
        if not self.data_dir.exists():
            print(f"Creating data directory at {self.data_dir}")
            self.data_dir.mkdir(parents=True, exist_ok=True)
            return {}
            
        for file in self.data_dir.glob("*.txt"):
            bill_id = file.stem  # filename without extension becomes bill_id
            self.bills[bill_id] = file.read_text(encoding='utf-8')
            print(f"Loaded bill {bill_id} with {len(self.bills[bill_id])} characters")
            
        return self.bills
    
    def get_bill(self, bill_id: str) -> Optional[str]:
        """Get text of a specific bill by ID."""
        return self.bills.get(bill_id)
    
    def add_bill(self, bill_id: str, text: str) -> None:
        """Add a new bill or update existing one.
        
        Args:
            bill_id: Unique identifier for the bill (e.g. 'HR1234')
            text: Full text content of the bill
        """
        # Save to file
        bill_path = self.data_dir / f"{bill_id}.txt"
        bill_path.write_text(text, encoding='utf-8')
        # Update in-memory dict
        self.bills[bill_id] = text
        print(f"Saved bill {bill_id} ({len(text)} characters)")

if __name__ == "__main__":
    # Example usage
    loader = BillLoader()
    bills = loader.load_bills()
    print(f"\nLoaded {len(bills)} bills from disk")

    # Add a new bill
    loader.add_bill("HR1234", "Full text of the bill here...")

    # Get a specific bill
    bill_text = loader.get_bill("HR1234")