# Setup Instructions

This document provides step-by-step instructions for setting up and running the Congressional Bill Q&A API.

## Prerequisites

- Python 3.9 or higher
- pip (Python package installer)
- Git (for cloning the repository)
- OpenAI API key
- Qdrant API key and URL

## Environment Setup

1. Clone the repository and navigate to the project directory:
```bash
git clone [your-repository-url]
cd bill_chat_v2
```

2. Create a virtual environment:
```bash
# Create a new virtual environment
python -m venv venv

# Activate the virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Configuration

1. Create a `.env` file in the root directory:
```bash
touch .env
```

2. Add the following environment variables to your `.env` file:
```env
# OpenAI API Configuration
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-3.5-turbo  # or gpt-4 if you have access

# Qdrant Configuration
QDRANT_URL=your_qdrant_url
QDRANT_API_KEY=your_qdrant_api_key
```

Replace `your_openai_api_key`, `your_qdrant_url`, and `your_qdrant_api_key` with your actual API credentials.

## Running the Application

1. Start the Flask application:
```bash
export FLASK_APP=app.py
flask run
```

The API will be available at `http://127.0.0.1:5000/`

## Testing the API

You can test the API using curl:

```bash
curl -X POST http://127.0.0.1:5000/ask \
  -H "Content-Type: application/json" \
  -d '{
    "bill_id": "/hr-3334-118",
    "question": "What is the main purpose of this bill?"
  }'
```

Or using Python requests:

```python
import requests

url = "http://127.0.0.1:5000/ask"
data = {
    "bill_id": "/hr-3334-118",
    "question": "What is the main purpose of this bill?"
}

response = requests.post(url, json=data)
print(response.json())
```

## API Endpoints

### POST /ask
Ask a question about a specific bill.

Request body:
```json
{
    "bill_id": "string",
    "question": "string",
    "top_k": "number (optional, default: 3)"
}
```

Response:
```json
{
    "answer": "string",
    "excerpts": ["string"]
}
```

## Troubleshooting

If you encounter any issues:

1. **Model Download Issues**: On first run, the sentence transformer model will download automatically. This might take a few minutes depending on your internet connection.

2. **Memory Issues**: If you encounter memory errors, ensure you have enough RAM available (at least 8GB recommended).

3. **API Key Issues**: Double-check your API keys in the `.env` file and ensure they have the correct permissions.

4. **Port Already in Use**: If port 5000 is already in use, you can specify a different port:
```bash
flask run --port 5001
```

## Additional Notes

- The application uses sentence-transformers for semantic search and OpenAI's GPT models for generating answers.
- Responses are based on the actual content of the bills stored in the Qdrant vector database.
- The system uses RAG (Retrieval Augmented Generation) to provide accurate, context-aware responses.

## Support

If you encounter any issues or have questions, please:
1. Check the troubleshooting section above
2. Review the error messages in the console
3. Open an issue in the repository with details about your problem 