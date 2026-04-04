# for start server : uvicorn api.main:app --reload 
from fastapi import FastAPI
from brain.brain import process_text
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # allow everything (for now)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],)
@app.get("/")
def home():
    return {"status": "Jarvis API running"}

@app.get("/ask")
def ask(query: str):
    response = process_text(query)
    return {"response": response}