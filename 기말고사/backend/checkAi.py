from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI()

response = client.responses.create(
    model='gpt-5-mini',
    input='hello, how can i use openapi\'s chatGPT with API Key?'
)

print(response.output_text)