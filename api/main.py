# for start server : uvicorn api.main:app --reload 
from concurrent.futures import ThreadPoolExecutor
import asyncio
from body.speak import speak
from fastapi import FastAPI
from brain.brain import process_text
from memory.sync_manager import start_sync
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI()
executor = ThreadPoolExecutor(max_workers=1)
ASK_TIMEOUT_SECONDS = 25


@app.on_event("startup")
def startup_sync():
    start_sync()

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
async def ask(query: str):
    loop = asyncio.get_running_loop()

    try:
        response = await asyncio.wait_for(
            loop.run_in_executor(executor, process_text, query),
            timeout=ASK_TIMEOUT_SECONDS,
        )

    except asyncio.TimeoutError:
        response = "Jarvis took too long to respond. Please try a shorter command."

    # Speak using Python TTS
    speak(response)

    return {"response": response}