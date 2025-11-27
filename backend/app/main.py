# backend/app/main.py
from fastapi import FastAPI
from .api import router as api_router
import nltk
import asyncio
import concurrent.futures

# --------------------------
# NLTK Data Download on Startup
# --------------------------
def _blocking_download():
    """This is a synchronous function to be run in a thread pool."""
    nltk.download('stopwords', quiet=True)
    nltk.download('punkt', quiet=True)

async def download_nltk_data():
    """
    Asynchronously downloads NLTK data if not found, with a timeout
    to prevent the server from hanging.
    """
    try:
        nltk.data.find('corpora/stopwords')
        nltk.data.find('tokenizers/punkt')
        print("NLTK data already available.")
    except LookupError:
        print("Downloading NLTK data (stopwords, punkt)...")
        loop = asyncio.get_running_loop()
        with concurrent.futures.ThreadPoolExecutor() as pool:
            try:
                # Run the blocking download in a separate thread with a timeout
                await asyncio.wait_for(loop.run_in_executor(pool, _blocking_download), timeout=60.0)
                print("NLTK data downloaded successfully.")
            except asyncio.TimeoutError:
                print("\n--- NLTK Download Timed Out ---")
                print("The server couldn't download necessary NLTK data.")
                print("Please check your internet connection and firewall settings.")
                print("You can also try downloading manually by running these commands in your terminal:")
                print("python -c \"import nltk; nltk.download('stopwords')\"")
                print("python -c \"import nltk; nltk.download('punkt')\"")
                print("---------------------------------\n")

# Create FastAPI app
app = FastAPI(
    title="Marthanote AI Assistant",
    description="Upload documents and ask questions powered by Gemini AI embeddings",
    version="1.0.0",
)

# Add startup event to download NLTK data
@app.on_event("startup")
async def startup_event():
    await download_nltk_data()

# Include API router
app.include_router(api_router, prefix="/api")
