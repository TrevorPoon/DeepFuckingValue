# 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

from openai import OpenAI
import openai
import os
from dotenv import load_dotenv

load_dotenv()
openai.api_base = "https://flag.smarttrot.com/"

client = OpenAI()



completion = client.chat.completions.create(
  model="gpt-3.5-turbo",
  messages=[
    {"role": "system", "content": "You are a poetic assistant, skilled in explaining complex programming concepts with creative flair."},
    {"role": "user", "content": "Compose a poem that explains the concept of recursion in programming."}
  ]
)

print(completion.choices[0].message)