# Bill Text Storage

This directory contains the raw text of congressional bills in individual text files.

## File Naming Convention
- Name each file as `{BILL_ID}.txt` where BILL_ID is a unique identifier like 'HR1234' or 'S789'
- Use only alphanumeric characters and underscores in the bill ID
- Example: `HR1234.txt`, `S789.txt`

## File Format
- Save bills as plain text files (.txt)
- Use UTF-8 encoding
- Include the full text of the bill, including title, sections, and any metadata

## Example Usage
1. Copy the full text of a bill
2. Create a new .txt file with the bill's ID as the filename
3. Paste the bill text into the file and save

You can also use the `BillLoader` class in `data_ingestion.py` to programmatically add bills:

```python
from data_ingestion import BillLoader

loader = BillLoader()
loader.add_bill("HR1234", "Full text of the bill here...")
```