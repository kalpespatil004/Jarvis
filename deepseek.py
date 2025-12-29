from openai import OpenAI
model="provider-3/Deepseek-r1-0528",

a4f_api_key = "ddc-a4f-70cdf918e1564cd1bb8ee6db63518f61"
import requests
import json

response = requests.post(
  url="https://api.a4f.co/v1/chat/completions",
  headers={
    "Authorization":f"Bearer {a4f_api_key}",
  },
  data=json.dumps({
    "model": "provider-3/Deepseek-r1-0528",
    "messages": [
      {"role": "user", "content": "What is the meaning of life?"}
    ]
  })
)

print(response.json())