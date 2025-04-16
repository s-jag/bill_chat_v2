# Bill Chat API Documentation

This document outlines the endpoints available in the Bill Chat RAG (Retrieval Augmented Generation) system and provides examples for testing using curl commands.

## API Endpoints

### 1. Health Check

Check if the API is running properly.

**Endpoint:** `GET /health`

**Example:**
```bash
curl http://localhost:5001/health
```

### 2. Ask Question

Submit a question about a specific bill.

**Endpoint:** `POST /ask`

**Parameters:**
- `bill_id` (required): ID of the bill to query (e.g. "hr-22-119")
- `question` (required): The question to ask about the bill
- `top_k` (optional): Number of chunks to retrieve (default: 3)

**Example Response:**
```json
{
  "answer": "The short title of this bill is...",
  "excerpts": [
    "Text from the first relevant chunk...",
    "Text from the second relevant chunk...",
    "Text from the third relevant chunk..."
  ]
}
```

## Test Commands

### Basic Information Queries

```bash
# Get short title of a bill
curl -X POST http://localhost:5001/ask \
  -H "Content-Type: application/json" \
  -d '{"bill_id": "hr-22-119", "question": "What is the short title of this bill?"}'

# Get purpose of a resolution
curl -X POST http://localhost:5001/ask \
  -H "Content-Type: application/json" \
  -d '{"bill_id": "hconres-14-119", "question": "What is the purpose of this concurrent resolution?"}'

# Find out when a bill takes effect
curl -X POST http://localhost:5001/ask \
  -H "Content-Type: application/json" \
  -d '{"bill_id": "hr-1228-119", "question": "When does this bill take effect?"}'
```

### Specific Content Queries

```bash
# Key provisions of a Senate joint resolution
curl -X POST http://localhost:5001/ask \
  -H "Content-Type: application/json" \
  -d '{"bill_id": "sjres-18-119", "question": "What are the key provisions of this joint resolution?"}'

# Funding details in a House bill
curl -X POST http://localhost:5001/ask \
  -H "Content-Type: application/json" \
  -d '{"bill_id": "hr-586-119", "question": "What funding appropriations are mentioned in this bill?"}'

# Amendments in a resolution
curl -X POST http://localhost:5001/ask \
  -H "Content-Type: application/json" \
  -d '{"bill_id": "hres-294-119", "question": "What amendments does this resolution make?"}'
```

### Section-Specific Queries

```bash
# Section 1 of a bill
curl -X POST http://localhost:5001/ask \
  -H "Content-Type: application/json" \
  -d '{"bill_id": "hr-1039-119", "question": "What is in Section 1 of this bill?"}'

# Definitions section
curl -X POST http://localhost:5001/ask \
  -H "Content-Type: application/json" \
  -d '{"bill_id": "hr-1526-119", "question": "What terms are defined in this bill?"}'
```

### Comparative/Advanced Queries

```bash
# Compare two sections
curl -X POST http://localhost:5001/ask \
  -H "Content-Type: application/json" \
  -d '{"bill_id": "hr-22-119", "question": "What is the difference between Section 1 and Section 2 of this bill?"}'

# Find specific requirements
curl -X POST http://localhost:5001/ask \
  -H "Content-Type: application/json" \
  -d '{"bill_id": "hjres-20-119", "question": "What requirements does this joint resolution impose?"}'

# Look for agencies mentioned
curl -X POST http://localhost:5001/ask \
  -H "Content-Type: application/json" \
  -d '{"bill_id": "sjres-28-119", "question": "What government agencies are mentioned in this resolution?"}'
```

### Increase Result Count

```bash
# Get more context with 5 chunks instead of default 3
curl -X POST http://localhost:5001/ask \
  -H "Content-Type: application/json" \
  -d '{"bill_id": "hconres-14-119", "question": "Summarize the key budget provisions", "top_k": 5}'
```

## Executive Order Endpoints

### 1. Query Specific Executive Order

Submit a question about a specific executive order.

**Endpoint:** `POST /ask_executive_order`

**Parameters:**
- `order_id` (required): ID of the executive order to query (e.g. "2021-01753")
- `question` (required): The question to ask about the executive order
- `top_k` (optional): Number of chunks to retrieve (default: 3)

**Example Response:**
```json
{
  "answer": "This executive order requires...",
  "excerpts": [
    "Text from the first relevant chunk...",
    "Text from the second relevant chunk...",
    "Text from the third relevant chunk..."
  ]
}
```

### 2. Search Across All Executive Orders

Search for information across all executive orders.

**Endpoint:** `POST /search_all_executive_orders`

**Parameters:**
- `question` (required): The search query
- `top_k` (optional): Number of results to retrieve (default: 5)

**Example Response:**
```json
{
  "results": [
    {
      "order_id": "2021-01753",
      "text": "Text from the relevant chunk...",
      "score": 0.85
    },
    {
      "order_id": "2021-05087",
      "text": "Text from another relevant chunk...",
      "score": 0.82
    }
  ]
}
```

### 3. List Available Executive Orders

Get a list of all executive orders available in the system.

**Endpoint:** `GET /list_executive_orders`

**Example Response:**
```json
{
  "order_ids": [
    "2021-01753",
    "2021-01755",
    "2021-01759",
    "..."
  ]
}
```

## Executive Order Test Commands

### Basic Information Queries

```bash
# Get purpose of an executive order
curl -X POST http://localhost:5001/ask_executive_order \
  -H "Content-Type: application/json" \
  -d '{"order_id": "2021-01753", "question": "What is the purpose of this executive order?"}'

# Find key requirements in an executive order
curl -X POST http://localhost:5001/ask_executive_order \
  -H "Content-Type: application/json" \
  -d '{"order_id": "2021-05087", "question": "What are the key requirements established by this order?"}'

# Find when an executive order takes effect
curl -X POST http://localhost:5001/ask_executive_order \
  -H "Content-Type: application/json" \
  -d '{"order_id": "2022-05471", "question": "When does this executive order take effect?"}'
```

### Executive Order Advanced Queries

```bash
# Get information about specific sections in an executive order
curl -X POST http://localhost:5001/ask_executive_order \
  -H "Content-Type: application/json" \
  -d '{"order_id": "2021-02177", "question": "What does Section 3 of this executive order require?"}'

# Find out about agencies mentioned in an executive order
curl -X POST http://localhost:5001/ask_executive_order \
  -H "Content-Type: application/json" \
  -d '{"order_id": "2021-10460", "question": "Which federal agencies are mentioned in this executive order?"}'

# Get information about amendments or revocations
curl -X POST http://localhost:5001/ask_executive_order \
  -H "Content-Type: application/json" \
  -d '{"order_id": "2025-01956", "question": "Does this executive order amend or revoke any previous orders?"}'
```

### Searching Across Executive Orders

```bash
# Find all executive orders related to climate change
curl -X POST http://localhost:5001/search_all_executive_orders \
  -H "Content-Type: application/json" \
  -d '{"question": "Climate change policies and initiatives"}'

# Find executive orders related to immigration
curl -X POST http://localhost:5001/search_all_executive_orders \
  -H "Content-Type: application/json" \
  -d '{"question": "Immigration reform and border security"}'

# Find executive orders related to economic policy with more results
curl -X POST http://localhost:5001/search_all_executive_orders \
  -H "Content-Type: application/json" \
  -d '{"question": "Economic policy and financial regulations", "top_k": 8}'

# Find executive orders related to national security
curl -X POST http://localhost:5001/search_all_executive_orders \
  -H "Content-Type: application/json" \
  -d '{"question": "National security and defense measures"}'

# Find executive orders related to healthcare
curl -X POST http://localhost:5001/search_all_executive_orders \
  -H "Content-Type: application/json" \
  -d '{"question": "Healthcare policy and initiatives"}'

# Find executive orders related to education
curl -X POST http://localhost:5001/search_all_executive_orders \
  -H "Content-Type: application/json" \
  -d '{"question": "Education reform and student loans"}'
```

### List Available Executive Orders

```bash
# Get the list of all available executive orders
curl http://localhost:5001/list_executive_orders

# Process the output with jq (if installed) to get a cleaner display
curl http://localhost:5001/list_executive_orders | jq '.order_ids | length'

# Extract the first 5 executive orders using jq
curl http://localhost:5001/list_executive_orders | jq '.order_ids[0:5]'
```

### Combining Multiple Executive Order Queries

You can build more complex workflows by combining multiple queries. For example:

```bash
# 1. First, get a list of all executive orders
ORDER_IDS=$(curl -s http://localhost:5001/list_executive_orders | jq -r '.order_ids[0:3] | join(" ")')

# 2. Then, for each order, query its purpose
for ORDER_ID in $ORDER_IDS; do
  echo "Getting info about $ORDER_ID..."
  curl -s -X POST http://localhost:5001/ask_executive_order \
    -H "Content-Type: application/json" \
    -d "{\"order_id\": \"$ORDER_ID\", \"question\": \"What is the main purpose of this executive order?\"}" | jq '.answer'
done
```

## Available Bills

The system currently has the following bills indexed:

### House Bills (HR)
- hr-1039-119: House Bill 1039 (119th Congress) 
- hr-1048-119: House Bill 1048 (119th Congress)
- hr-1156-119: House Bill 1156 (119th Congress)
- hr-1228-119: House Bill 1228 (119th Congress)
- hr-1326-119: House Bill 1326 (119th Congress)
- hr-144-119: House Bill 144 (119th Congress)
- hr-1491-119: House Bill 1491 (119th Congress)
- hr-1526-119: House Bill 1526 (119th Congress)
- hr-1534-119: House Bill 1534 (119th Congress)
- hr-165-119: House Bill 165 (119th Congress)
- hr-186-119: House Bill 186 (119th Congress)
- hr-187-119: House Bill 187 (119th Congress)
- hr-1968-119: House Bill 1968 (119th Congress)
- hr-21-119: House Bill 21 (119th Congress)
- hr-22-119: House Bill 22 (119th Congress)
- hr-23-119: House Bill 23 (119th Congress)
- hr-26-119: House Bill 26 (119th Congress)
- hr-27-119: House Bill 27 (119th Congress)
- hr-30-119: House Bill 30 (119th Congress)
- hr-33-119: House Bill 33 (119th Congress)
- hr-35-119: House Bill 35 (119th Congress)
- hr-359-119: House Bill 359 (119th Congress)
- hr-375-119: House Bill 375 (119th Congress)
- hr-43-119: House Bill 43 (119th Congress)
- hr-471-119: House Bill 471 (119th Congress)
- hr-495-119: House Bill 495 (119th Congress)
- hr-517-119: House Bill 517 (119th Congress)
- hr-586-119: House Bill 586 (119th Congress)
- hr-692-119: House Bill 692 (119th Congress)
- hr-695-119: House Bill 695 (119th Congress)
- hr-736-119: House Bill 736 (119th Congress)
- hr-758-119: House Bill 758 (119th Congress)
- hr-77-119: House Bill 77 (119th Congress)
- hr-776-119: House Bill 776 (119th Congress)
- hr-788-119: House Bill 788 (119th Congress)
- hr-804-119: House Bill 804 (119th Congress)
- hr-818-119: House Bill 818 (119th Congress)
- hr-825-119: House Bill 825 (119th Congress)
- hr-832-119: House Bill 832 (119th Congress)
- hr-856-119: House Bill 856 (119th Congress)
- hr-901-119: House Bill 901 (119th Congress)
- hr-993-119: House Bill 993 (119th Congress)
- hr-997-119: House Bill 997 (119th Congress)

### House Resolutions (HRES)
- hres-122-119: House Resolution 122 (119th Congress)
- hres-161-119: House Resolution 161 (119th Congress)
- hres-177-119: House Resolution 177 (119th Congress)
- hres-189-119: House Resolution 189 (119th Congress)
- hres-211-119: House Resolution 211 (119th Congress)
- hres-242-119: House Resolution 242 (119th Congress)
- hres-282-119: House Resolution 282 (119th Congress)
- hres-294-119: House Resolution 294 (119th Congress)
- hres-313-119: House Resolution 313 (119th Congress)
- hres-53-119: House Resolution 53 (119th Congress)
- hres-93-119: House Resolution 93 (119th Congress)

### House Joint Resolutions (HJRES)
- hjres-20-119: House Joint Resolution 20 (119th Congress)
- hjres-24-119: House Joint Resolution 24 (119th Congress)
- hjres-25-119: House Joint Resolution 25 (119th Congress)
- hjres-35-119: House Joint Resolution 35 (119th Congress)
- hjres-42-119: House Joint Resolution 42 (119th Congress)
- hjres-61-119: House Joint Resolution 61 (119th Congress)
- hjres-75-119: House Joint Resolution 75 (119th Congress)

### House Concurrent Resolutions (HCONRES)
- hconres-14-119: House Concurrent Resolution 14 (119th Congress)

### Senate Bills (S)
- s-331-119: Senate Bill 331 (119th Congress)
- s-5-119: Senate Bill 5 (119th Congress)
- s-6-119: Senate Bill 6 (119th Congress)
- s-9-119: Senate Bill 9 (119th Congress)

### Senate Joint Resolutions (SJRES)
- sjres-10-119: Senate Joint Resolution 10 (119th Congress)
- sjres-11-119: Senate Joint Resolution 11 (119th Congress)
- sjres-12-119: Senate Joint Resolution 12 (119th Congress)
- sjres-18-119: Senate Joint Resolution 18 (119th Congress)
- sjres-26-119: Senate Joint Resolution 26 (119th Congress)
- sjres-28-119: Senate Joint Resolution 28 (119th Congress)
- sjres-3-119: Senate Joint Resolution 3 (119th Congress)
- sjres-33-119: Senate Joint Resolution 33 (119th Congress)
- sjres-37-119: Senate Joint Resolution 37 (119th Congress)

### Senate Concurrent Resolutions (SCONRES)
- sconres-7-119: Senate Concurrent Resolution 7 (119th Congress) 