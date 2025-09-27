import os
import google.generativeai as genai
from dotenv import load_dotenv
load_dotenv()

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

model = genai.GenerativeModel("gemini-2.5-flash")
response = model.generate_content("Hello Gemini, say hi!")
print("DEBUG GOOGLE_API_KEY:", os.getenv("GOOGLE_API_KEY"))


print(response.text) 
