import google.generativeai as genai
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
GEN_API_KEY = os.getenv("GEN_API_KEY")

if not GEN_API_KEY:
    print("Error: GEN_API_KEY not found in .env file.")
else:
    genai.configure(api_key=GEN_API_KEY)

    print("Finding models available for 'generateContent':")
    for m in genai.list_models():
        # The 'generateContent' method is used for chat-like interactions
        if "generateContent" in m.supported_generation_methods:
            print(f"- {m.name}")
