# Chunked Bill Storage

This directory contains the chunked versions of congressional bills, split into semantically meaningful pieces using LLM-based chunking.

## Directory Structure
For each bill, you'll find:
- Multiple chunk files named `{BILL_ID}_chunk_XXX.txt` (where XXX is a zero-padded number)
- A metadata file named `{BILL_ID}_metadata.json` containing information about the chunks

## File Naming Convention
- Chunk files: `HR1234_chunk_000.txt`, `HR1234_chunk_001.txt`, etc.
- Metadata files: `HR1234_metadata.json`

## Metadata Format
Each metadata file contains:
```json
{
    "bill_id": "HR1234",
    "num_chunks": 42,
    "chunk_files": [
        "HR1234_chunk_000.txt",
        "HR1234_chunk_001.txt",
        ...
    ]
}
```

## Chunking Properties
- Each chunk is semantically coherent
- Sections are kept together when possible
- Long sections are split at logical boundaries
- No splits occur mid-sentence
- Target chunk length is configurable (default: 800 words)
- Section headers are always kept with their content