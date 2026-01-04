"""
OLLAMA Local LLM Client for using local models via OLLAMA API.
Supports local models for reasoning, chat, and analysis without API dependencies.
"""
from __future__ import annotations
import os
import requests
import json
from typing import Optional
from enum import Enum

from backend.config import settings


class LLMProvider(str, Enum):
    """Supported LLM providers"""
    OLLAMA = "ollama"


class LLMClient:
    """
    OLLAMA LLM client for local model inference.
    Uses OLLAMA API endpoints for generating text without external API costs.
    """
    
    def __init__(
        self,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        api_url: Optional[str] = None,
    ):
        self.provider = provider or settings.llm_provider
        self.model = model or settings.llm_model
        self.api_url = api_url or settings.llm_api_url
        
        # Verify OLLAMA provider
        if self.provider != LLMProvider.OLLAMA:
            raise ValueError(f"Only OLLAMA provider is supported. Got: {self.provider}")
        
        print(f"[LLMClient] Initialized OLLAMA with model: {self.model} at {self.api_url}")
        self._verify_connection()
    
    def _verify_connection(self) -> bool:
        """Verify OLLAMA is running and accessible"""
        try:
            # Try a simple health check with a very short prompt
            response = requests.post(
                self.api_url,
                json={
                    "model": self.model,
                    "prompt": "ok",
                    "stream": False,
                },
                timeout=5
            )
            if response.status_code == 200:
                print(f"[LLMClient] OLLAMA connection verified")
                return True
        except Exception as e:
            print(f"[LLMClient] Warning: Could not verify OLLAMA connection: {str(e)}")
        return False
    
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> str:
        """
        Generate text using OLLAMA local model.
        
        Args:
            prompt: User prompt/query
            system_prompt: System message for context
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens in response
            
        Returns:
            Generated text
        """
        try:
            # Build the full prompt with system message if provided
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"{system_prompt}\n\n{prompt}"
            
            response = requests.post(
                self.api_url,
                json={
                    "model": self.model,
                    "prompt": full_prompt,
                    "stream": False,
                    "temperature": temperature,
                    "num_predict": max_tokens,
                },
                timeout=300  # 5 minute timeout for long generations
            )
            
            if response.status_code != 200:
                raise RuntimeError(f"OLLAMA API error: {response.status_code} - {response.text}")
            
            result = response.json()
            return result.get("response", "").strip()
        except Exception as e:
            raise RuntimeError(f"LLM generation failed: {str(e)}")


# ============================================================================
# PROMPT TEMPLATES FOR ANALYSIS
# ============================================================================

SYSTEM_PROMPT_ANALYSIS = """You are an expert research analyst specializing in AI, machine learning, and computer science. 
Your task is to analyze academic papers and provide insightful analysis.

Guidelines:
- Be specific and cite concepts from the papers
- Use clear, academic language
- Provide actionable insights
- Focus on implications and connections between papers"""

PROMPT_TEMPLATE_GAP_ANALYSIS = """
Based on the following research papers, identify research gaps and unexplored areas:

{papers_context}

Please analyze and provide:
1. **Identified Research Gaps**: Specific areas not well-covered in the current literature
2. **Research Areas**: Domains or subfields that lack sufficient coverage
3. **Missing Benchmarks**: Standard evaluation metrics that are absent or insufficient
4. **Underexplored Topics**: Topics mentioned but not thoroughly investigated

Format your response as a JSON object with keys: identified_gaps, research_areas, missing_benchmarks, underexplored_topics
Each value should be a list of strings."""

PROMPT_TEMPLATE_DESIGN_SUGGESTION = """
Based on the following research papers, suggest architectural improvements and design approaches:

{papers_context}

Please analyze and provide:
1. **Suggested Approaches**: Specific implementation strategies that could be adopted
2. **Architectural Improvements**: Ways to structure systems more effectively
3. **Implementation Strategies**: Practical development guidelines
4. **Trade-offs**: Important trade-offs to consider when designing solutions

Format your response as a JSON object with keys: suggested_approaches, architectural_improvements, implementation_strategies, trade_offs
Each value should be a list of strings."""

PROMPT_TEMPLATE_PATTERN_DETECTION = """
Based on the following research papers, detect patterns and emerging trends:

{papers_context}

Please analyze and provide:
1. **Patterns Found**: Common patterns across the papers
2. **Trend Analysis**: Current trends and directions in the field
3. **Emerging Methods**: New methodologies gaining traction

Format your response as a JSON object with keys: patterns_found, trend_analysis, emerging_methods
Each value should be a list of strings."""

PROMPT_TEMPLATE_FUTURE_DIRECTIONS = """
Based on the following research papers, project future research directions:

{papers_context}

Please analyze and provide:
1. **Next Steps**: Recommended next steps for research
2. **Open Questions**: Fundamental questions still unanswered
3. **Future Applications**: Potential real-world applications

Format your response as a JSON object with keys: next_steps, open_questions, future_applications
Each value should be a list of strings."""

# ============================================================================
# SINGLETON LLM CLIENT INSTANCE
# ============================================================================

_llm_client: Optional[LLMClient] = None


def get_llm_client() -> LLMClient:
    """Get or create the global LLM client (singleton)"""
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client


def set_llm_client(client: LLMClient) -> None:
    """Set the global LLM client (for testing)"""
    global _llm_client
    _llm_client = client
