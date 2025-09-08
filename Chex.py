# %%
from dotenv import load_dotenv
import os
load_dotenv()

groq_api_key = os.getenv("GROQ_API_KEY")
exa_api_key = os.getenv("EXA_API_KEY")

# %%
from langchain_groq import ChatGroq

# Replace with your actual Groq API key
groq_api_key = groq_api_key

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=groq_api_key,
    temperature=0.7
)

# %%
from exa_py import Exa
from pydantic import BaseModel, Field
from typing import List

# Define schema for structured output
class FactCheck(BaseModel):
    verdict: str = Field(..., description="Estimated truth verdict (e.g. 'True', 'False', 'Uncertain')")
    response: str = Field(..., description="Concise summary of the fact check based on evidence")
    sources: List[str] = Field(..., description="List of source URLs or references used")

# Init Groq
llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=groq_api_key,
    temperature=0
)

# Example pipeline
Claim = "There is a video of a fish poking it's head out of water, opening it's mouth to eat egg yolk. Is this natural fish behaviour?"


exa = Exa(api_key=exa_api_key)
Exa_answer = ""
# Then, use stream_answer with your original query
result = exa.stream_answer(
    "is it true that " + Claim,
)

# Process the streaming response
for chunk in result:
    if chunk.content:
        Exa_answer  += chunk.content

# Create structured output chain
structured_llm = llm.with_structured_output(FactCheck)

input_text = f"Question: is it true that {Claim}\nEvidence:\n{Exa_answer}"
fact_check = structured_llm.invoke(input_text)


# %%
print(fact_check)

# %%



