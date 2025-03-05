# backend/services/investment_memo_service.py

import requests
from backend.config import Config
from backend.utils import prepare_text

def _call_groq_api(input_text: str) -> str:
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {Config.GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "deepseek-r1-distill-llama-70b",
        "messages": [
            {
                "role": "system",
                "content": """You are an expert venture capital analyst specializing in creating detailed investment memos. 
                Maintain a professional, objective tone and be transparent about any information gaps in the pitch deck.
                Do not make assumptions or fill in missing information - instead, highlight what information would be needed for a complete analysis."""
            },
            {
                "role": "user",
                "content": f"""Generate a structured investment memo based on the following pitch deck content.
                For each section, if critical information is missing from the pitch deck, explicitly note the gaps 
                and what additional information would be needed for a thorough analysis.

                # Investment Memo: [Company Name]

                ## 1. Executive Summary
                - Company overview and core value proposition
                - Current stage and traction
                - Investment ask (if specified)

                ## 2. Market Opportunity
                - Market size (if provided)
                - Target customer segments
                - Market trends (if discussed)

                ## 3. Competitive Landscape
                - Known competitors
                - Stated differentiators
                - Competitive advantages (if demonstrated)

                ## 4. Financial Highlights
                - Current financials (if provided)
                - Projections (if included)
                - Key metrics and unit economics (if available)

                ## 5. Investment Thesis
                - Demonstrated strengths
                - Growth potential based on available information
                - Key areas requiring further due diligence

                ## 6. Risks and Information Gaps
                - Identified risks from available information
                - Critical missing information
                - Key questions for follow-up

                Analyze this pitch deck content, clearly indicating where information is missing or incomplete:
                {input_text}"""
            }
        ],
        "temperature": 0.7,
        "max_tokens": 16384
    }
    response = requests.post(url, headers=headers, json=data)
    if response.ok:
        result = response.json()
        if result.get("choices"):
            return result["choices"][0]["message"]["content"].strip()
    raise Exception(f"Groq API error: {response.status_code}")

def _call_openrouter_api(input_text: str) -> str:
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {Config.HF_API_KEY}",
        "Content-Type": "application/json",
    }
    data = {
        "model": "deepseek/deepseek-r1:free",
        "messages": [
            {
                "role": "user",
                "content": (
                    "Generate a detailed investment memo based on the following pitch deck content. "
                    "Your memo should include these sections:\n\n"
                    "1. Executive Summary\n2. Market Opportunity\n3. Competitive Landscape\n4. Financial Highlights\n\n"
                    f"Pitch Deck Content: {input_text}"
                )
            }
        ]
    }
    response = requests.post(url, headers=headers, json=data)
    if response.ok:
        result = response.json()
        if result.get("choices"):
            return result["choices"][0]["message"]["content"].strip()
    raise Exception(f"OpenRouter API error: {response.status_code}")

def generate_memo(text: str, refine: bool = False) -> str:
    """
    Generate an investment memo for a given pitch deck text.
    
    :param text: The raw pitch deck text.
    :param refine: Whether the text is pre-processed.
    :return: The investment memo.
    """
    # Preprocess the text if needed.
    input_text = text if refine else prepare_text(text, refine=False)

    # Choose the API based on available configuration.
    if Config.GROQ_API_KEY:
        try:
            return _call_groq_api(input_text)
        except Exception as e:
            # You can log the error here or print it for debugging.
            print(f"Groq API failed: {e}")
    
    try:
        return _call_openrouter_api(input_text)
    except Exception as e:
        print(f"OpenRouter API failed: {e}")
        raise Exception("Failed to generate memo using both external services.")
