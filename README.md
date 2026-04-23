# 🎙️ VoiceAgent — Talk to Your Data

VoiceAgent is a conversational AI assistant that lets you query your NYC Taxi dataset using plain English no SQL, no code. Just ask a question and get an answer.

It combines a FastAPI backend with a Streamlit frontend, using LangGraph for agent orchestration, DuckDB for fast in-memory SQL queries, and OpenAI for natural language understanding.

## How It Works

You type (or speak) a question like *"What's the average fare amount?"* the agent figures out the right query, runs it against your CSV data using DuckDB, and gives you a clean answer back in plain English.

Under the hood:
- **LangGraph** manages the agent's reasoning loop
- **LangChain + OpenAI** handles the language model calls
- **DuckDB** runs SQL directly on your CSV file fast, no database setup needed
- **ChromaDB** handles any vector search needs
- **FastAPI** serves the backend API
- **Streamlit** powers the frontend UI

## Project Structure
    voiceagent/
    ├── backend/          # FastAPI app, agent logic, tools
    ├── frontend/         # Streamlit UI
    ├── data/             # Drop your CSV file here
    ├── .env.example      # Environment variable template
    ├── requirements.txt  # Python dependencies
    └── README.md

## Getting Started

**1. Clone the repo**

```bash
git clone https://github.com/shanmathy-ravisankaran/voiceagent.git
cd voiceagent
```

**2. Install dependencies**

```bash
pip install -r requirements.txt
```

**3. Set up your environment**

Copy `.env.example` to `.env` and add your OpenAI API key:

```bash
cp .env.example .env
```

OPENAI_API_KEY=your-key-here

**4. Add your data**

Place your NYC Taxi CSV file inside the `data/` folder.

---

## Running the App

You'll need two terminals.

**Terminal 1 — Start the backend:**

```bash
uvicorn backend.main:app --reload
```

**Terminal 2 — Start the frontend:**

```bash
streamlit run frontend/app.py
```

Then open your browser to `http://localhost:8501`.

---

## Example Questions

Once the app is running, try asking things like:

- "What is the average fare amount?"
- "Which vendor has more trips?"
- "What percentage of payments are made in cash?"
- "What is the average tip for credit card payments?"
- "How many trips had more than 5 passengers?"

---

## Tech Stack

| Layer | Technology |
|---|---|
| Language Model | OpenAI GPT |
| Agent Framework | LangGraph + LangChain |
| Query Engine | DuckDB |
| Vector Store | ChromaDB |
| Backend | FastAPI + Uvicorn |
| Frontend | Streamlit |
| Data | Pandas + NumPy |

---

## Requirements

- Python 3.9+
- An OpenAI API key
- NYC Taxi CSV dataset (or any tabular CSV you want to query)

---

## License
MIT
