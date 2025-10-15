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
Evidence_collection_prompt = (
    "You are a meticulous fact-checker. Your task is to verify the accuracy of a given claim by searching the web for credible sources. "
    "Use the Google Search tool to find relevant information."
    "Ignore claims that are subjective or opinion-based, and focus only on factual claims."
    "For non-factual claims, respond with 'Unverifiable claim'."
)

def collect_evidence(claim):
    client = genai.Client(api_key=google_genai_api_key)
    tool = types.Tool(google_search=types.GoogleSearch())
    config = types.GenerateContentConfig(
        tools=[tool],
        thinking_config=types.ThinkingConfig(thinking_budget=512),
        system_instruction=Evidence_collection_prompt,
    )
    return client.models.generate_content(
        model="gemini-2.5-flash-lite",
        contents=f"Fact-check this claim and summarize findings:\n{claim}",
        config=config,
    )

def add_citations(response):
    text = response.text
    supports = getattr(response.candidates[0].grounding_metadata, "grounding_supports", None)
    chunks = getattr(response.candidates[0].grounding_metadata, "grounding_chunks", None)

    if not supports or not chunks:
        # No citations available, just return the text
        return text

    # Sort supports by end_index in descending order to avoid shifting issues when inserting.
    sorted_supports = sorted(supports, key=lambda s: s.segment.end_index, reverse=True)

    all_urls = set()
    for support in sorted_supports:
        end_index = support.segment.end_index
        if support.grounding_chunk_indices:
            # Create citation string like [1][2] (no links inline)
            citation_indices = []
            for i in support.grounding_chunk_indices:
                if i < len(chunks):
                    uri = chunks[i].web.uri
                    all_urls.add(uri)
                    citation_indices.append(f"[{i + 1}]")
            citation_string = "".join(citation_indices)
            text = text[:end_index] + citation_string + text[end_index:]

    # Add sources list at the end
    if all_urls:
        text += "\n\nsources: [" + ", ".join(all_urls) + "]"

    return text


response_schema = {
    "type": "object",
    "properties": {
        "verdict": {"type": "string"},
        "confidence": {"type": "integer"},
        "response": {"type": "string"},
        "sources": {
            "type": "array",
            "items": {"type": "string"}
        }
    },
    "required": ["verdict", "confidence", "response", "sources"]
}

sys_prompt = (
    "You are a fact-checking output formatter. "
    "You will be given a summary of evidence about a factual claim. "
    "From that summary, extract and return a JSON object with these fields:\n"
    " - verdict: one of 'True', 'False', or 'Uncertain', depending on whether the claim is supported, refuted, or unclear.\n"
    " - confidence: integer from 0 to 99 estimating confidence in the verdict.\n"
    " - response: 1–3 sentences summarizing the reasoning.\n"
    " - sources: a list of relevant citation URLs found in the text.\n"
    "Return only valid JSON, following the provided schema."
)

def structure_to_json(text):
    client = genai.Client(api_key=google_genai_api_key)
    config = types.GenerateContentConfig(
        system_instruction=sys_prompt,
        response_mime_type="application/json",
        response_schema=response_schema,
    )
    response = client.models.generate_content(
        model="gemini-2.5-flash-lite",
        contents=text,
        config=config,
    )
    # response.text will be JSON
    return json.loads(response.text)

def classify_claim(claim):
    start_time = time.time() 
    raw_summary = collect_evidence(claim)
    text_with_citations = add_citations(raw_summary)
    result_json = structure_to_json(text_with_citations)
    elapsed = time.time() - start_time  # End timer

    # Flatten result_json for Google Sheets
    row = [
        claim,
        result_json.get("verdict", ""),
        result_json.get("confidence", ""),
        result_json.get("response", ""),
        ", ".join(result_json.get("sources", [])),
        elapsed
    ]
    save_to_google_sheets([row])
    return result_json

