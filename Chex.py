import re, json

from pipeline import classify_claim


# %%
from pydantic import BaseModel
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

app = FastAPI()

app.add_middleware(
CORSMiddleware,
allow_origins=["*"],   # you can restrict later e.g. ["https://x.com"]
allow_credentials=True,
allow_methods=["*"],
allow_headers=["*"],
)

class FactCheckRequest(BaseModel):
    claim: str

@app.get("/")
def home():
    return {"message": "API is live"}

CheckCount = 0

from fastapi.responses import StreamingResponse
from fastapi.responses import Response

@app.head("/")
def healthcheck():
    return Response(status_code=200)

@app.post("/factcheck/stream")
def factcheck_stream(req: FactCheckRequest):
    claim_text = (req.claim or "").strip()
    if not claim_text:
        return JSONResponse(content={
            "verdict": "Uncertain",
            "confidence": 0,
            "response": "⚠️ No text to be fact checked",
            "sources": []
        })

    json_result = classify_claim(claim_text)
    print("Fact-check completed.", json_result)

    # If json_result is a string, clean and parse it
    if isinstance(json_result, str):
        # Remove code fences
        cleaned = re.sub(r"^```(?:json)?", "", json_result.strip())
        cleaned = re.sub(r"```$", "", cleaned)
        # Extract first JSON object
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if match:
            cleaned = match.group(0)
        try:
            json_result = json.loads(cleaned)
        except Exception as e:
            print("JSON parse failed:", e)
            json_result = {
                "verdict": "Uncertain",
                "confidence": 0,
                "response": "⚠️ Failed to parse model output as JSON.",
                "sources": []
            }
    print(f"FACTCHECK RESULT TYPE: {type(json_result)}")
    return JSONResponse(content=json_result)
