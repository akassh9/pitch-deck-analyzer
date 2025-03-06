"""
Centralized LLM prompt builder module for generating investment memos.
This module consolidates all prompt definitions to avoid duplicates.
"""

from .utils.memo_templates import TEMPLATES

def build_memo_prompt(input_text: str, template_key: str = "default") -> dict:
    """
    Build the prompt payload for LLM calls used in investment memo generation.
    
    Args:
        input_text (str): The pitch deck content to analyze.
        template_key (str): The key of the template to use (default is 'default').
        
    Returns:
        dict: A dictionary with two keys:
            - "system": A fixed system message.
            - "user": The detailed user prompt including template instructions and the input text.
    """
    # Get the appropriate template based on the provided key; fallback to default if key not found
    template = TEMPLATES.get(template_key, TEMPLATES["default"])
    
    # Format the sections from the template with section numbers
    sections = "\n".join(f"{i+1}. {section}" for i, section in enumerate(template["sections_order"]))
    
    # Define the fixed system message for the VC analyst role
    system_message = "You are an expert venture capital analyst specializing in creating detailed investment memos."
    
    # Construct the user message by combining template instructions, sections, and input content
    user_message = (
        f"{template['instructions']}\n\n"
        f"Please structure the memo with the following sections:\n{sections}\n\n"
        f"Pitch Deck Content: {input_text}"
    )
    
    return {
        "system": system_message,
        "user": user_message
    }

def build_text_refinement_prompt(text: str) -> dict:
    """
    Build the prompt payload for LLM calls used in text refinement.
    
    Args:
        text (str): The text to refine.
        
    Returns:
        dict: A dictionary with two keys:
            - "system": A fixed system message for text refinement.
            - "user": The text to be refined.
    """
    system_message = (
        "Remove only unnecessary whitespace, extra newlines, and redundant paragraph breaks. "
        "Return the text with improved formatting without altering its content. "
        "Only return the improved text, do not add any instructions/confirmations/comments."
    )
    
    return {
        "system": system_message,
        "user": text
    }

