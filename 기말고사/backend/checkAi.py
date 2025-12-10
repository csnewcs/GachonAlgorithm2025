from openai import OpenAI
from dotenv import load_dotenv
import queue

load_dotenv()
client = OpenAI()

# check the 'text' is written by AI or human. gpt will return a score between 0 and 1
def checkGPT(text: str, q: queue.Queue):
    messages = [
        {
            "role": 'system',
            "content": '''
            - 당신은 주어진 글을 사람이 썼는지 AI가 썼는지 판별하는 시스템입니다
            - 주어지는 텍스트는 공백 제거를 위한 일부 가공이 들어간 상태입니다. 따라서 맞춤법 등을 이유로 사람이라 판별하지 마세요
            - 글이 AI가 쓴 것 같으면 100에 가까운 점수를, 사람이 쓴 것 같으면 0에 가까운 점수를 반환합니다
            - 점수는 0과 100 사이의 정수로 반환합니다
            - 반환은 오직 숫자로만 한정합니다. 다른 설명이나 문장은 포함하지 마세요
            '''
        },
        {
            "role": "user",
            "content": text
        }
    ]
    response = client.responses.create(
        model='gpt-5-mini',
        input=messages
    )
    # 반환된 것에서 숫자를 제외한 모든 문자 제거
    percent = int(''.join(filter(str.isdigit, response.output_text)))

    q.put(percent)