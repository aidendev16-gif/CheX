from dotenv import load_dotenv
import os

from groq import Groq
from exa_py import Exa

import re, json
import time

from Gsheets import save_to_google_sheets

load_dotenv()
groq_api_key = os.getenv("GROQ_API_KEY")
exa_api_key = os.getenv("EXA_API_KEY")

client = Groq(api_key=groq_api_key)
exa = Exa(api_key=exa_api_key)

# ============================helper============================
def fact_check_search_endpoint(claim, sys_prompt, Exa_result_limit,Exa_num_results,Search_type="auto",category=None): 
    
    # Perform search and content retrieval with Exa
    if category is not None:
        search_results = exa.search_and_contents(
            claim,
            num_results=Exa_num_results,
            type=Search_type,
            category=category,
            text={
                "maxCharacters": Exa_result_limit,  # Limit to Exa_result_limit characters
                "includeHtmlTags": False  # Optional, defaults to False
            },
        )
    else: 
        search_results = exa.search_and_contents(
            claim,
            num_results=Exa_num_results,
            type=Search_type,
            text={
                "maxCharacters": Exa_result_limit,  # Limit to Exa_result_limit characters
                "includeHtmlTags": False  # Optional, defaults to False
            },
        )

    # Prepare context and sources for the LLM
    context = "\n\n".join([f"Source: {res.title}\n{res.url}\n{res.text}" for res in search_results.results])
    sources = [res.url for res in search_results.results]


    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": f"Claim: {claim}\n\nContext:\n{context}\n\nSources:\n{sources}"}
        ]
    )

    raw = response.choices[0].message.content.strip()

    # Remove Markdown fences if present
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?", "", raw)
        raw = re.sub(r"```$", "", raw)
        raw = raw.strip()

    try:
        result = json.loads(raw)
    except json.JSONDecodeError as e:
        print("JSON parse failed:", e)
        print("Raw output:\n", raw)
        result = None

    if result:
        #print(json.dumps(result, indent=2))
        return json.dumps(result, indent=2), search_results
    



    
# ============================Pipeline function==========================
def classify_claim(claim):
    start_time = time.time()  # Start timer

    prompt = (
        'Classify the following claim as one of: "entertainment", "science", "politics", or "news". '
        'Only classify as "entertainment" if the claim is unverifiable as in lacking context, or is incomprehensible, or very obviously satirical'
        'Shorten the claim to its core essence, removing any context that is not essential to the claim itself.'
        'Return ONLY a valid JSON object with two fields: category (string) and claim (string). Example: {"category": "science", "claim": "The sun is a star."}\n\n'
    )
    resp = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "user", "content": prompt + f"\n\nClaim: {claim}"},
        ],
    )
    result = resp.choices[0].message.content.strip()
    print("Raw LLM output:\n", result)

    # Parse the result as JSON
    try:
        data = json.loads(result)
        post_category = data.get("category", "").lower()
        claim_out = data.get("claim", "")
        print(f"Category: {post_category}\nClaim: {claim_out}")
        if post_category == 'entertainment':
            print('No action needed for entertainment posts.')
            elapsed = time.time() - start_time
            save_to_google_sheets([[claim, "", "", "", round(elapsed, 3),"entertainment"]])
            return ({
                "verdict": "Uncertain",
                "confidence": 100,
                "response": "⚠️ Claim classified as 'entertainment'; no fact-checking performed.",
                "sources": []
                }, None)

        elif post_category == 'science':
            #====================================SCIENCE====================================
            sys_prompt = (
                "You are a fact checker checking science. Use only the provided context. always mention if sources are not reputable. When there are no related sources, simply state that the search result came up empty."
                "Return a structured JSON object with the fields: "
                "verdict: (string: 'True', 'False', or 'Uncertain'), "
                "confidence: (integer 0–99, never 100), "
                "response: (string, make it detailed, include relevant context), "
                "sources: (list of URLs). "
                "Return ONLY the JSON."
            )

            soft_filter = (
                'site:nature.com OR site:sciencemag.org OR site:cell.com OR site:thelancet.com '
                'OR site:nejm.org OR site:jamanetwork.com OR site:pnas.org OR site:arxiv.org '
                'OR site:biorxiv.org OR site:medrxiv.org OR site:chemrxiv.org OR site:ncbi.nlm.nih.gov '
                'OR site:who.int OR site:cdc.gov OR site:un.org OR site:europa.eu OR site:royalsociety.org '
                'OR site:springer.com OR site:wiley.com OR site:nasa.gov OR "peer-reviewed study" OR "academic journal" OR "scientific report"'
            ) #Is this actually impactful?

            query = f"{claim_out}"
            category = "research paper"  # Override category for science claims

            #====================================SCIENCE====================================


        elif post_category == 'politics':
            #====================================POLITICS====================================
            sys_prompt = (
                "You are a fact checker fact checking politics. Use only the provided context."
                "Always mention that political issues may be complex and nuanced, and that sources may have biases."
                "Return a structured JSON object with the fields: "
                "verdict: (string: 'True', 'False', or 'Uncertain'), "
                "confidence: (integer 0–99, never 100), "
                "response: (string, make it detailed, include relevant context), "
                "sources: (list of URLs). "
                "Return ONLY the JSON."
            )

            query = f"{claim_out}"
            category = "news"  # Override category for politics claims
            #====================================POLITICS====================================
        elif post_category == 'news':
            #====================================NEWS====================================
            sys_prompt = (
                "You are a fact checker fact checking news. Use only the provided context. always mention if sources are not reputable. When there are no related sources, simply state that the search result came up empty."
                "When receiving a source from a social media platform, always indicate that the source may not be reputable."
                "Return a structured JSON object with the fields: "
                "verdict: (string: 'True', 'False', or 'Uncertain'), "
                "confidence: (integer 0–99, never 100), "
                "response: (string, make it detailed, include relevant context), "
                "sources: (list of URLs). "
                "Return ONLY the JSON."
            )

            query = f"{claim_out}"
            category = "news"  # Override category for news claims
            #====================================NEWS====================================
        else:
            sys_prompt = (
                "You are a fact checker. Use only the provided context. always mention if sources are not reputable. When there are no related sources, simply state that the search result came up empty."
                "Return a structured JSON object with the fields: "
                "verdict: (string: 'True', 'False', or 'Uncertain'), "
                "confidence: (integer 0–99, never 100), "
                "response: (string, make it detailed, include relevant context), "
                "sources: (list of URLs). "
                "Return ONLY the JSON."
            )

            query = f"{claim_out}"
            category = None

        json_result, Exa_search_results = fact_check_search_endpoint(
                claim=query,
                sys_prompt=sys_prompt,
                Exa_result_limit=2000,
                Exa_num_results=5,
                Search_type="keyword",
                category=category
            )
        
        elapsed = time.time() - start_time  # End timer
        # Save to Google Sheets (Raw post,Exa_searched claim,LLM response,Verdict,ElapsedTime)
        save_to_google_sheets([[claim, query, json_result, json.loads(json_result).get("verdict", ""), round(elapsed, 3),post_category]])

        print(f"Query took {elapsed:.3f} seconds")
        return json_result, Exa_search_results

    except Exception as e:
        print('Failed to parse LLM output as JSON:', e)
        elapsed = time.time() - start_time
        save_to_google_sheets([[claim, "", "", "", round(elapsed, 3),"parsing error"]])
        return None, None

