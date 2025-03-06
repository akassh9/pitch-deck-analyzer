"""
Investment memo generation service.
This module provides functionality to generate investment memos from pitch deck text.
"""

import logging
import requests
from ..utils.error_handling import ProcessingError
from ..infrastructure.job_manager import update_job
from ..utils.text_processing import prepare_text
from ..prompts import build_memo_prompt  # New import for consolidated prompts

logger = logging.getLogger(__name__)

class MemoService:
    """Service for generating investment memos."""
    
    def __init__(self, config):
        """Initialize the memo service with configuration."""
        self.config = config
        logger.info("Initialized MemoService")
    
    def generate_memo(self, text, refine=False, template_key="default"):
        """
        Generate an investment memo from the provided text.
        
        Args:
            text (str): The pitch deck text
            refine (bool): Whether the text is already refined
            template_key (str): The template to use for memo generation
            
        Returns:
            str: The generated investment memo
            
        Raises:
            ProcessingError: If memo generation fails
        """
        try:
            # Preprocess the text if needed
            input_text = text if refine else prepare_text(text, refine=False)
            logger.info(f"Generating memo from {len(input_text)} chars of text using template '{template_key}'")
            
            # Try with primary service (Groq)
            if self.config.GROQ_API_KEY:
                try:
                    logger.info("Attempting to generate memo with Groq API")
                    return self._call_groq_api(input_text, template_key)
                except Exception as e:
                    logger.warning(f"Groq API failed: {str(e)}, falling back to OpenRouter")
            else:
                logger.info("No Groq API key configured, using OpenRouter")
            
            # Fallback to secondary service
            return self._call_openrouter_api(input_text, template_key)
                
        except Exception as e:
            logger.error(f"Failed to generate memo: {str(e)}", exc_info=True)
            raise ProcessingError(f"Failed to generate memo: {str(e)}")
    
    def _call_groq_api(self, input_text, template_key):
        """
        Call the Groq API to generate a memo.
        
        Args:
            input_text (str): The preprocessed text
            template_key (str): The key of the template to use
            
        Returns:
            str: The generated memo
            
        Raises:
            Exception: If the API call fails
        """
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.config.GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        
        # Use the consolidated prompt builder to get the system and user messages
        prompt = build_memo_prompt(input_text, template_key)
        
        data = {
            "model": "deepseek-r1-distill-llama-70b",
            "messages": [
                {"role": "system", "content": prompt["system"]},
                {"role": "user", "content": prompt["user"]}
            ],
            "temperature": 0.7,
            "max_tokens": 16384
        }
        
        logger.debug("Sending request to Groq API")
        response = requests.post(url, headers=headers, json=data, timeout=60)
        
        if response.ok:
            result = response.json()
            if result.get("choices"):
                memo = result["choices"][0]["message"]["content"].strip()
                logger.info(f"Successfully generated memo with Groq API ({len(memo)} chars)")
                return memo
            else:
                logger.error(f"Unexpected Groq API response format: {result}")
        
        error_message = f"Groq API error: {response.status_code}"
        if response.text:
            try:
                error_data = response.json()
                if "error" in error_data:
                    error_message += f" - {error_data['error'].get('message', '')}"
            except:
                error_message += f" - {response.text[:100]}"
        
        logger.error(error_message)
        raise Exception(error_message)
    
    def _call_openrouter_api(self, input_text, template_key):
        """
        Call the OpenRouter API to generate a memo.
        
        Args:
            input_text (str): The preprocessed text
            template_key (str): The key of the template to use
            
        Returns:
            str: The generated memo
            
        Raises:
            Exception: If the API call fails
        """
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.config.HF_API_KEY}",
            "Content-Type": "application/json",
        }
        
        # Use the consolidated prompt builder to get the system and user messages
        prompt = build_memo_prompt(input_text, template_key)
        
        data = {
            "model": "deepseek/deepseek-r1:free",
            "messages": [
                {"role": "system", "content": prompt["system"]},
                {"role": "user", "content": prompt["user"]}
            ],
            "temperature": 0.7,
            "max_tokens": 16384
        }
        
        logger.debug("Sending request to OpenRouter API")
        response = requests.post(url, headers=headers, json=data, timeout=60)
        
        if response.ok:
            result = response.json()
            if result.get("choices"):
                memo = result["choices"][0]["message"]["content"].strip()
                logger.info(f"Successfully generated memo with OpenRouter API ({len(memo)} chars)")
                return memo
            else:
                logger.error(f"Unexpected OpenRouter API response format: {result}")
        
        error_message = f"OpenRouter API error: {response.status_code}"
        if response.text:
            try:
                error_data = response.json()
                if "error" in error_data:
                    error_message += f" - {error_data['error'].get('message', '')}"
            except:
                error_message += f" - {response.text[:100]}"
        
        logger.error(error_message)
        raise Exception(error_message)
    
    def validate_memo(self, memo, query=None):
        try:
            # Use the provided query if available; otherwise, use the entire memo text.
            query = query or memo
            
            # Perform validation using Google Custom Search
            return self._google_custom_search(query)
                
        except Exception as e:
            logger.error(f"Failed to validate memo: {str(e)}", exc_info=True)
            raise ProcessingError(f"Failed to validate memo: {str(e)}")

    
    def _google_custom_search(self, query):
        """
        Perform a Google Custom Search to validate claims.
        
        Args:
            query (str): The query to search for
            
        Returns:
            list: Search results
        """
        if not self.config.GOOGLE_API_KEY or not self.config.GOOGLE_CSE_ID:
            logger.warning("Google API key or CSE ID not configured, skipping validation")
            return []
        
        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            "key": self.config.GOOGLE_API_KEY,
            "cx": self.config.GOOGLE_CSE_ID,
            "q": query
        }
        
        logger.debug(f"Performing Google Custom Search for: {query[:50]}...")
        response = requests.get(url, params=params, timeout=10)
        
        if response.ok:
            result = response.json()
            items = result.get("items", [])
            
            validation_results = []
            for item in items[:5]:  # Limit to top 5 results
                validation_results.append({
                    "title": item.get("title", ""),
                    "snippet": item.get("snippet", ""),
                    "link": item.get("link", "")
                })
            
            logger.info(f"Found {len(validation_results)} validation results")
            return validation_results
        
        logger.error(f"Google Custom Search error: {response.status_code}")
        return []

# Create a singleton instance
_memo_service = None

def get_memo_service(config=None):
    """Get the singleton MemoService instance."""
    global _memo_service
    
    if _memo_service is None:
        from ..config import Config
        _memo_service = MemoService(config or Config)
        
    return _memo_service 

def generate_memo(text: str, job_id: str = None, template_key: str = None, refine: bool = True) -> dict:
    """
    Generate an investment memo from the given text.
    
    Args:
        text (str): The input text to generate the memo from
        job_id (str): Optional job ID for tracking progress
        template_key (str): Optional template key to use
        refine (bool): Whether to refine the input text
        
    Returns:
        dict: Dictionary containing the generated memo and metadata
    """
    try:
        if job_id:
            update_job(job_id, {"status": "preparing"})
            
        # Prepare the input text
        result = prepare_text(text, refine=refine)
        cleaned_text = result["cleaned_text"]
        
        # If no template specified, use the predicted stage
        if not template_key:
            template_key = result["startup_stage"]
            
        if job_id:
            update_job(job_id, {"status": "generating"})
            
        # Generate the memo using the template
        memo = get_memo_service().generate_memo(cleaned_text, refine=True, template_key=template_key)
        
        if job_id:
            update_job(job_id, {
                "status": "completed",
                "result": {
                    "memo": memo,
                    "template_used": template_key,
                    "startup_stage": result["startup_stage"]
                }
            })
            
        return {
            "success": True,
            "memo": memo,
            "template_used": template_key,
            "startup_stage": result["startup_stage"]
        }
        
    except Exception as e:
        logger.error(f"Error generating memo: {str(e)}")
        if job_id:
            update_job(job_id, {
                "status": "error",
                "error": str(e)
            })
        raise 