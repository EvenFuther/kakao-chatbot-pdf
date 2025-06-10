@"
from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv
import os, glob, pdfplumber
from openai import OpenAI

# 1) 환경변수 로드
load_dotenv()
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
if not OPENAI_API_KEY:
    raise RuntimeError('OPENAI_API_KEY가 설정되지 않았습니다.')

# 2) OpenAI 클라이언트 초기화
client = OpenAI(api_key=OPENAI_API_KEY)

# 3) PDF 전부 읽어서 메모리 로드
documents = []
foreach ($path in Get-ChildItem -Path 'data' -Filter '*.pdf') {
    $text = ''
    $pdf = [pdfplumber.PDF]::open($path.FullName)
    foreach ($page in $pdf.pages) {
        $text += ($page.extract_text() + "`n")
    }
    $pdf.close()
    $documents += $text
}

function Search-InPdfs($query) {
    $ql = $query.ToLower()
    foreach ($txt in $documents) {
        if ($txt.ToLower().Contains($ql)) {
            $i = $txt.ToLower().IndexOf($ql)
            $start = [Math]::Max($i - 100, 0)
            $end   = [Math]::Min($i + $ql.Length + 100, $txt.Length)
            return $txt.Substring($start, $end - $start).Replace('`n',' ')
        }
    }
    return $null
}

# 4) FastAPI 앱 정의
app = FastAPI()

class KakaoRequest(BaseModel):
    userRequest: dict

@app.post("/kakao")
async def kakao_webhook(req: KakaoRequest):
    user_msg = req.userRequest["utterance"]

    # PDF 검색 우선
    snippet = search_in_pdfs(user_msg)
    if snippet:
        answer = f"📄 자료 발췌:\n…{snippet}…"
    else:
        # PDF 검색 결과 없으면 OpenAI 호출
        resp = client.chat.completions.create(
            model="o4-mini",               # ← 여기만 o4-mini로 변경
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

# 위 코드는 예시입니다. 실제 main.py는 Python 스크립트이므로 VSCode 같은 에디터로 붙여넣으세요.
"@ | Out-File -Encoding UTF8 main.py
