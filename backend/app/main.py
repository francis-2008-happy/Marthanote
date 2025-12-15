# backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api_v2 import router as api_router
from .database import init_db
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
    # A recent NLTK update causes a lookup error for 'punkt_tab'.
    # The error message suggests downloading it directly.
    nltk.download('punkt_tab', quiet=True)

async def download_nltk_data():
    """look
    Asynchronously downloads NLTK data if not found, with a timeout
    to prevent the server from hanging.
    """
    try:
        nltk.data.find('corpora/stopwords')
        nltk.data.find('tokenizers/punkt')
        # Also check for 'punkt_tab' which causes issues in recent NLTK versions.
        nltk.data.find('tokenizers/punkt_tab')
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

# --------------------------
# CORS (Cross-Origin Resource Sharing) Middleware
# --------------------------
# This allows your React frontend to communicate with the backend.
# Browsers block requests from a different "origin" (domain, protocol, port)
# unless the server explicitly allows it by sending CORS headers.

origins = [
    "http://localhost:3000",      # Default for Create React App
    "http://localhost:5173",      # Default for Vite
    "http://localhost:8501",      # Default for Streamlit local dev
    # IMPORTANT: Add the URL of your deployed React frontend here. For example:
    # "https://your-react-app-on-vercel.com", 
    "https://<YOUR_REACT_APP_URL_GOES_HERE>", # <-- REPLACE THIS WITH YOUR ACTUAL DEPLOYED URL
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers, including custom ones like X-Device-Id
)


# Add startup event to download NLTK data
@app.on_event("startup")
async def startup_event():
    await download_nltk_data()
    # Initialize the SQLite database and tables
    try:
        init_db()
    except Exception as e:
        print(f"Warning: could not initialize database: {e}")

# Include API router
app.include_router(api_router, prefix="/api")


# Root and health endpoints to help with deployments and health checks
@app.get("/", include_in_schema=False)
async def root():
    return {
        "message": "Marthanote API",
        "api_prefix": "/api",
        "docs": "/docs",
    }


@app.get("/health", include_in_schema=False)
async def health():
    return {"status": "ok"}
