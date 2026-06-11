# DocProcessor

A financial document processing tool for extracting key terms from credit agreements, term sheets, LPAs, and earnings releases.

## Prerequisites

- [Ollama](https://ollama.com) installed locally
- PostgreSQL running locally
- Python 3.10+
- Node.js 18+

---

## Setup

### 1. Install Ollama and pull Llama 3

```bash
ollama pull llama3
```

### 2. Create the PostgreSQL database

```sql
CREATE DATABASE docprocessor;
```

### 3. Create the tables

```sql
CREATE TABLE documents (
    id SERIAL PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    file_type VARCHAR(10) NOT NULL,
    file_path VARCHAR(500),
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE terms (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    term VARCHAR(255) NOT NULL,
    value TEXT NOT NULL
);
```

### 4. Configure backend environment

Create `backend/.env`:

```env
DB_HOST=localhost
DB_NAME=docprocessor
DB_USER=postgres
DB_PASSWORD=postgres
DB_PORT=5432
OLLAMA_URL=http://localhost:11434
```

### 5. Install backend dependencies

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux
pip install -r requirements.txt
```

### 6. Install frontend dependencies

```bash
cd frontend
npm install
```

---

## Running

### Backend

```bash
cd backend
venv\Scripts\activate
uvicorn main:app --reload
```

### Frontend

```bash
cd frontend
npm run dev
```

The app will be available at http://localhost:5173

---

## Features

- **Upload** PDF, DOCX, or TXT financial documents
- **Extract** key terms automatically using Llama 3 via Ollama
- **View** extracted terms in a structured two-column grid
- **Export** results to CSV or formatted Excel
- **Compare** two documents side by side
- **Cancel** processing at any time
