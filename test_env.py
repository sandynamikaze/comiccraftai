from dotenv import load_dotenv
import os

load_dotenv()

print("HF:", "OK" if os.getenv("HF_TOKEN") else "MISSING")
print("Gemini:", "OK" if os.getenv("GEMINI_API_KEY") else "MISSING")