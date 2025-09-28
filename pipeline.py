from dotenv import load_dotenv
import os

from google import genai
from google.genai import types

import re, json
import time

from Gsheets import save_to_google_sheets

google_genai_api_key = os.getenv("GEMINI_API_KEY")

load_dotenv()


from google import genai
from google.genai import types
# ============================Pipeline function==========================
def classify_claim(claim):
    start_time = time.time()  # Start timer
        
    client_gemini = genai.Client(api_key=google_genai_api_key) 

    sys_prompt = (
            "You are a fact checker fact checking posts on X. You are to determine the claims in the post and determine if it is true, false, or uncertain. ALWAYS search the web for relevant information to support your verdict. "
            "Return a structured JSON object with the fields: "
            "verdict (string: 'True', 'False', or 'Uncertain'), "
            "confidence (integer 0–99, never 100), "
            "response (string, explaining the reasoning behind the verdict briefly)," 
            "sources (list of URLs)."
            "For 'sources', always return the grounded citations provided by the search tool "
            "(they will look like 'https://vertexaisearch.cloud.google.com/grounding-api-redirect/...'). "
            "Never fabricate or shorten these links, and never return raw guessed URLs."
            "Return ONLY the JSON."
            "here is an example of a valid output: ```JSON {\"verdict\": \"True\", \"confidence\": 85, \"explanation\": \"The claim is supported by multiple reputable sources that confirm the event occurred as described.\", \"sources\": [\"https://vertexaisearch.cloud.google.com/grounding-api-redirect/...\", \"https://vertexaisearch.cloud.google.com/grounding-api-redirect/...\"]}```"
            "again, you MUST return ONLY the JSON."
        )

    grounding_tool = types.Tool(
        google_search=types.GoogleSearch()
    )

    config = types.GenerateContentConfig(
        tools=[grounding_tool],
        thinking_config=types.ThinkingConfig(thinking_budget=512),
        system_instruction=sys_prompt,
    )


    response = client_gemini.models.generate_content(
        model="gemini-2.5-flash-lite",
        contents=("Is it true that: " + claim),
        config=config,
    )
        
    elapsed = time.time() - start_time  # End timer
    # Save to Google Sheets (Raw post,Exa_searched claim,LLM response,Verdict,ElapsedTime)
    save_to_google_sheets([[claim, response.text, round(elapsed, 3)]])

    print(f"Query took {elapsed:.3f} seconds")
    return response.text

