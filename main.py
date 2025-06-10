from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv
import os, glob
import pdfplumber
import openai

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY가 설정되지 않았습니다.")

openai.api_key = OPENAI_API_KEY

documents = []
for path in glob.glob("data/*.pdf"):
    with pdfplumber.open(path) as pdf:
        text = "\n".join(page.extract_text() or "" for page in pdf.pages)
    documents.append(text)

def search_in_pdfs(query: str) -> str | None:
    ql = query.lower()
    for text in documents:
        if ql in text.lower():
            i = text.lower().index(ql)
            start = max(i - 100, 0)
            end = min(len(text), i + len(ql) + 100)
            return text[start:end].replace("\n", " ")
    return None

app = FastAPI()

class KakaoRequest(BaseModel):
    userRequest: dict

@app.post("/kakao")
async def kakao_webhook(req: KakaoRequest):
    user_msg = req.userRequest["utterance"]


    snippet = search_in_pdfs(user_msg)
    if snippet:
        answer = f"📄 자료 발췌:\n…{snippet}…"
    else:

        resp = openai.ChatCompletion.create(
            model="o4-mini",
            messages=[{"role": "user", "content": user_msg}]
        )
        answer = resp.choices[0].message.content

    return {
        "version": "2.0",
        "template": {
            "outputs": [
                {"simpleText": {"text": answer}}
            ]
        }
    }

