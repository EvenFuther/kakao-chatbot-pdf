import os
import glob
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel
import pdfplumber
import openai

env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY가 설정되지 않았습니다.")

openai.api_key = OPENAI_API_KEY

def search_in_pdfs(query: str) -> str | None:
    ql = query.lower()

    for path in glob.glob("data/*.pdf"):
        with pdfplumber.open(path) as pdf:
            # 첫 페이지만 읽어서 속도 개선
            text = pdf.pages[0].extract_text() or ""
            lower = text.lower()
            if ql in lower:
                i = lower.index(ql)
                start = max(i - 100, 0)
                end = min(i + len(ql) + 100, len(text))
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

        resp = openai.chat.completions.create(
            model="gpt-o4-mini",
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

