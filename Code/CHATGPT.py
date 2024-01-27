import poe
import json
client = poe.Client("TOKEN_HERE")

print(json.dumps(client.bot_names, indent=2))
"""
{
  "chinchilla": "ChatGPT",
  "a2": "Claude-instant",
  "capybara": "Assistant",
  "a2_100k": "Claude-instant-100k",
  "llama_2_7b_chat": "Llama-2-7b",
  "llama_2_13b_chat": "Llama-2-13b",
  "a2_2": "Claude-2-100k",
  "llama_2_70b_chat": "Llama-2-70b",
  "agouti": "ChatGPT-16k",
  "beaver": "GPT-4",
  "vizcacha": "GPT-4-32k",
  "acouchy": "Google-PaLM"
}
"""