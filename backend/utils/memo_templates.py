"""
Defines the structure and content of different investment memo templates.
Each template specifies the order of sections and specific instructions for the LLM.
"""

TEMPLATES = {
    "default": {
        "sections_order": [
            "Executive Summary",
            "Market Opportunity",
            "Competitive Landscape",
            "Financial Highlights",
            "Investment Thesis",
            "Risks and Mitigations"
        ],
        "instructions": (
            "Generate a detailed investment memo using the following sections. "
            "For each section, if critical information is missing from the pitch deck, "
            "explicitly note the gaps and what additional information would be needed."
        )
    },
    "seed": {
        "sections_order": [
            "Executive Summary",
            "Market Opportunity",
            "Team and Vision",
            "Product and Technology",
            "Go-to-Market Strategy",
            "Risks and Mitigations"
        ],
        "instructions": (
            "Generate a seed-stage investment memo that emphasizes the founding team's capabilities, "
            "market potential, and early product validation. Focus on qualitative insights "
            "and early market signals rather than extensive financial metrics."
        )
    },
    "seriesA": {
        "sections_order": [
            "Executive Summary",
            "Market Opportunity",
            "Financial Highlights",
            "Growth Metrics",
            "Competitive Landscape",
            "Unit Economics",
            "Investment Thesis",
            "Risks and Mitigations"
        ],
        "instructions": (
            "Generate a Series A investment memo with emphasis on growth metrics, unit economics, "
            "and market validation. Include detailed analysis of financial performance, customer "
            "acquisition costs, and market penetration strategy."
        )
    },
    "growth": {
        "sections_order": [
            "Executive Summary",
            "Financial Performance",
            "Market Leadership",
            "Expansion Strategy",
            "Competitive Moat",
            "Team Assessment",
            "Investment Thesis",
            "Risk Analysis"
        ],
        "instructions": (
            "Generate a growth-stage investment memo focusing on market leadership position, "
            "scaling metrics, and operational excellence. Emphasize historical performance, "
            "market share, and potential for continued growth."
        )
    }
} 