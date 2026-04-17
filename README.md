# 🎙️ VoiceAgent — Talk to Your NYC Taxi Data

## Setup
1. Clone the repo and cd into it
2. Install dependencies: `pip install -r requirements.txt`
3. Add your OpenAI key to `.env`
4. Place CSV in `data/` folder

## Run
Terminal 1 - Backend:
uvicorn backend.main:app --reload

Terminal 2 - Frontend:
streamlit run frontend/app.py

## Example Questions
- "What is the average fare amount?"
- "Which vendor has more trips?"
- "What percentage of payments are cash?"
- "What is the average tip for credit card payments?"
- "How many trips had more than 5 passengers?"