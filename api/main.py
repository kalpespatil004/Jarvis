# for start server : uvicorn api.main:app --reload 
from concurrent.futures import ThreadPoolExecutor
import asyncio
from body.speak import speak, _internet_available
from fastapi import FastAPI, BackgroundTasks
from brain.brain import process_text
from memory.sync_manager import start_sync
from fastapi.middleware.cors import CORSMiddleware
import threading
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()
executor = ThreadPoolExecutor(max_workers=2)
ASK_TIMEOUT_SECONDS = 120


@app.on_event("startup")
def startup_sync():
    """Initialize everything at server startup."""
    logger.info("=" * 50)
    logger.info("JARVIS SERVER STARTING")
    logger.info("=" * 50)
    
    # Start Firebase sync only if internet is available
   
    # Initialize offline TTS in background
    def init_tts_background():
        try:
            from body.speak_TTS import initialize as init_offline_tts
            logger.info("Initializing offline TTS in background...")
            success = init_offline_tts()
            if success:
                logger.info("✓ Offline TTS initialized successfully")
            else:
                logger.warning("⚠ Offline TTS initialization failed (will fallback to online)")
        except ImportError as e:
            logger.warning(f"⚠ Offline TTS not available: {e}")
        except Exception as e:
            logger.error(f"✗ Offline TTS initialization error: {e}")
    
    tts_thread = threading.Thread(target=init_tts_background, daemon=True)
    tts_thread.start()
    
    logger.info("✓ Server startup complete")
    logger.info("=" * 50)


@app.on_event("shutdown")
def shutdown_sync():
    """Clean shutdown."""
    logger.info("=" * 50)
    logger.info("JARVIS SERVER SHUTTING DOWN")
    logger.info("=" * 50)
    
    try:
        from body.speak_TTS import shutdown
        shutdown()
        logger.info("✓ TTS shutdown complete")
    except ImportError:
        pass
    except Exception as e:
        logger.error(f"✗ TTS shutdown error: {e}")
    
    executor.shutdown(wait=False)
    logger.info("✓ Server shutdown complete")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def home():
    return {"status": "Jarvis API running"}


@app.get("/ask")
async def ask(query: str, background_tasks: BackgroundTasks):
    """
    Process query and return response immediately.
    Speech happens in background.
    """
    loop = asyncio.get_running_loop()
    start_time = time.time()

    try:
        response = await asyncio.wait_for(
            loop.run_in_executor(executor, process_text, query),
            timeout=ASK_TIMEOUT_SECONDS,
        )
        
        elapsed = time.time() - start_time
        logger.info(f"[ROUTER] {int(elapsed * 1000)}ms")

    except asyncio.TimeoutError:
        response = "Jarvis took too long to respond. Please try a shorter command."
        logger.warning("[ROUTER] TIMEOUT")
    except Exception as e:
        logger.error(f"[SERVER] Error processing query: {e}")
        response = "I encountered an error processing your request."

    # Speak in background to not block the response
    background_tasks.add_task(speak, response)

    return {"response": response}