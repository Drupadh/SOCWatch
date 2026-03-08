import os
import json
from google import genai
from google.genai import types
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Gemini Client
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    print("WARNING: No GEMINI_API_KEY found in .env")

def call_llm(prompt: str, system_message: str = "You are a helpful AI.", response_format="text"):
    """
    Helper to call the Gemini LLM and return the string content.
    """
    try:
        if not api_key:
            return None
            
        client = genai.Client(api_key=api_key)
        
        config_kwargs = {
            "temperature": 0.1,
            "system_instruction": system_message
        }
        
        if response_format == "json_object":
             config_kwargs["response_mime_type"] = "application/json"

        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(**config_kwargs)
        )
        
        return response.text
        
    except Exception as e:
        print(f"Error calling Gemini LLM: {str(e)}")
        return None
