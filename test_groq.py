# test_groq.py
# A minimal, isolated test to confirm the Groq API key + connection work,
# with NO LangGraph/tools involved — helps us isolate whether the problem
# is the key/network (this file) or something in agent.py's logic.

import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

response = client.chat.completions.create(
    model="llama-3.1-8b-instant",
    messages=[{"role": "user", "content": "Say hello in one sentence."}]
)

print(response.choices[0].message.content)