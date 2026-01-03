"""
LLM Client for integrating with OpenAI, Anthropic, or other LLM providers.
Supports GPT-4, Claude, and other models for enhanced analysis.
"""
from __future__ import annotations
import os
from typing import Optional, List
from enum import Enum

from backend.config import settings


class LLMProvider(str, Enum):
    """Supported LLM providers"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"


class LLMClient:
    """
    Base LLM client supporting multiple providers.
    Abstracts away provider-specific API differences.
    """
    
    def __init__(
        self,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
    ):
        self.provider = provider or settings.llm_provider
        self.model = model or settings.llm_model
        self.api_key = api_key or settings.llm_api_key
        
        # Initialize provider-specific client
        if self.provider == LLMProvider.OPENAI:
            self._init_openai()
        elif self.provider == LLMProvider.ANTHROPIC:
            self._init_anthropic()
        elif self.provider == LLMProvider.GOOGLE:
            self._init_google()
        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}")
    
    def _init_openai(self):
        """Initialize OpenAI client"""
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=self.api_key)
            print(f"[LLMClient] Initialized OpenAI with model: {self.model}")
        except ImportError:
            raise ImportError("openai package not installed. Install with: pip install openai")
    
    def _init_anthropic(self):
        """Initialize Anthropic (Claude) client"""
        try:
            from anthropic import Anthropic
            self.client = Anthropic(api_key=self.api_key)
            print(f"[LLMClient] Initialized Anthropic with model: {self.model}")
        except ImportError:
            raise ImportError("anthropic package not installed. Install with: pip install anthropic")
    
    def _init_google(self):
        """Initialize Google Generative AI client"""
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            print(f"[LLMClient] Initialized Google Generative AI with model: {self.model}")
        except ImportError:
            raise ImportError("google-generativeai package not installed")
    
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> str:
        """
        Generate text using the configured LLM.
        
        Args:
            prompt: User prompt/query
            system_prompt: System message for context
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens in response
            
        Returns:
            Generated text
        """
        try:
            if self.provider == LLMProvider.OPENAI:
                return self._generate_openai(prompt, system_prompt, temperature, max_tokens)
            elif self.provider == LLMProvider.ANTHROPIC:
                return self._generate_anthropic(prompt, system_prompt, temperature, max_tokens)
            elif self.provider == LLMProvider.GOOGLE:
                return self._generate_google(prompt, system_prompt, temperature, max_tokens)
        except Exception as e:
            raise RuntimeError(f"LLM generation failed: {str(e)}")
    
    def _generate_openai(
        self,
        prompt: str,
        system_prompt: Optional[str],
        temperature: float,
        max_tokens: int,
    ) -> str:
        """Generate using OpenAI API"""
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({"role": "user", "content": prompt})
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        
        return response.choices[0].message.content
    
    def _generate_anthropic(
        self,
        prompt: str,
        system_prompt: Optional[str],
        temperature: float,
        max_tokens: int,
    ) -> str:
        """Generate using Anthropic (Claude) API"""
        response = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=system_prompt or "",
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=temperature,
        )
        
        return response.content[0].text
    
    def _generate_google(
        self,
        prompt: str,
        system_prompt: Optional[str],
        temperature: float,
        max_tokens: int,
    ) -> str:
        """Generate using Google Generative AI"""
        import google.generativeai as genai
        
        # Build full prompt with system message
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"
        
        model = genai.GenerativeModel(self.model)
        response = model.generate_content(
            full_prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
            ),
        )
        
        return response.text


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
