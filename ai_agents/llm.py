from dotenv import load_dotenv
import os
from langchain_groq import ChatGroq

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    raise ValueError("❌ GROQ_API_KEY not found in environment")

print("GROQ KEY LOADED ✔")

llm = ChatGroq(
    api_key=api_key,
    model="llama-3.1-8b-instant",
    temperature=0.3,
    max_tokens=800
)