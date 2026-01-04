"""
Answer quality assessment service.
Provides source tracking, confidence scoring, and faithfulness evaluation.
Uses RAGAS for faithfulness metrics and OLLAMA for scoring.
"""
from __future__ import annotations
import json
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
import re
import logging

from backend.config import settings
from backend.services.llm_client import LLMClient

logger = logging.getLogger(__name__)


@dataclass
class SourceReference:
    """Reference to a source used in the answer"""
    chunk_id: str
    paper_id: str
    section_id: str
    text_snippet: str = ""  # Relevant portion from source
    page_from: Optional[int] = None
    page_to: Optional[int] = None
    confidence: float = 0.0  # How relevant this source is to the answer
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "chunk_id": self.chunk_id,
            "paper_id": self.paper_id,
            "section_id": self.section_id,
            "text_snippet": self.text_snippet,
            "page_from": self.page_from,
            "page_to": self.page_to,
            "confidence": self.confidence,
            "metadata": self.metadata,
        }


@dataclass
class AnswerQuality:
    """Quality metrics for LLM-generated answer"""
    answer: str
    sources: List[SourceReference] = field(default_factory=list)
    confidence_score: float = 0.0  # 0-1, overall confidence in answer
    faithfulness_score: float = 0.0  # 0-1, how faithful to sources
    source_coverage: float = 0.0  # 0-1, how well sources cover the answer
    relevance_scores: Dict[str, float] = field(default_factory=dict)  # score per fact
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response"""
        return {
            "answer": self.answer,
            "sources": [s.to_dict() for s in self.sources],
            "confidence_score": round(self.confidence_score, 3),
            "faithfulness_score": round(self.faithfulness_score, 3),
            "source_coverage": round(self.source_coverage, 3),
            "quality_summary": {
                "has_sources": len(self.sources) > 0,
                "source_count": len(self.sources),
                "is_faithful": self.faithfulness_score >= 0.7,
                "is_confident": self.confidence_score >= 0.7,
            }
        }


class AnswerQualityAssessor:
    """Assesses quality of LLM-generated answers using multiple metrics"""
    
    def __init__(self):
        self.llm_client = LLMClient()
        self.max_sources = 5  # Show top 5 sources
    
    def assess_answer(
        self,
        answer: str,
        ranked_results: List[Dict[str, Any]],
        user_query: str,
    ) -> AnswerQuality:
        """
        Assess the quality of an LLM-generated answer.
        
        Args:
            answer: The LLM-generated answer text
            ranked_results: List of ranked retrieval results used for answer
            user_query: The original user query
            
        Returns:
            AnswerQuality object with all metrics
        """
        try:
            # Extract and score sources
            sources = self._extract_and_score_sources(answer, ranked_results, user_query)
            
            # Calculate confidence based on source quality
            confidence_score = self._calculate_confidence_score(sources, answer)
            
            # Calculate faithfulness using OLLAMA-based evaluation
            faithfulness_score = self._evaluate_faithfulness(answer, sources, user_query)
            
            # Calculate source coverage
            source_coverage = self._calculate_source_coverage(sources, answer)
            
            return AnswerQuality(
                answer=answer,
                sources=sources[:self.max_sources],  # Keep top sources
                confidence_score=confidence_score,
                faithfulness_score=faithfulness_score,
                source_coverage=source_coverage,
            )
        except Exception as e:
            logger.error(f"Error assessing answer quality: {str(e)}")
            # Return answer with minimal quality metrics on error
            return AnswerQuality(
                answer=answer,
                sources=[],
                confidence_score=0.5,
                faithfulness_score=0.5,
                source_coverage=0.0,
            )
    
    def _extract_and_score_sources(
        self,
        answer: str,
        ranked_results: List[Dict[str, Any]],
        user_query: str,
    ) -> List[SourceReference]:
        """Extract and score sources that contributed to the answer"""
        sources = []
        
        if not ranked_results:
            return sources
        
        # Score each source based on overlap with answer
        for result in ranked_results:
            relevance_score = self._calculate_relevance_score(
                answer, 
                result.get("text", ""),
                user_query
            )
            
            # Only include sources with meaningful relevance
            if relevance_score > 0.3:
                source = SourceReference(
                    chunk_id=result.get("chunk_id", "unknown"),
                    paper_id=result.get("paper_id", "unknown"),
                    section_id=result.get("section_id", "unknown"),
                    text_snippet=result.get("text", "")[:300],  # First 300 chars
                    page_from=result.get("page_from"),
                    page_to=result.get("page_to"),
                    confidence=float(result.get("combined_score", result.get("score", 0.5))),
                    metadata={
                        "relevance_to_answer": relevance_score,
                        "source_type": result.get("source", "qdrant"),
                        "rank": result.get("rank", 0),
                    }
                )
                sources.append(source)
        
        # Sort by relevance to answer
        sources.sort(
            key=lambda s: s.metadata.get("relevance_to_answer", 0),
            reverse=True
        )
        
        return sources
    
    def _calculate_relevance_score(
        self,
        answer: str,
        source_text: str,
        user_query: str,
    ) -> float:
        """
        Calculate how relevant a source is to the generated answer.
        Uses text overlap and keyword matching.
        """
        if not source_text or not answer:
            return 0.0
        
        # Extract key terms from answer (simple approach)
        answer_terms = set(answer.lower().split())
        source_terms = set(source_text.lower().split())
        
        # Calculate Jaccard similarity
        intersection = answer_terms & source_terms
        union = answer_terms | source_terms
        
        if not union:
            return 0.0
        
        jaccard_sim = len(intersection) / len(union)
        
        # Boost score if source contains query terms
        query_terms = set(user_query.lower().split())
        query_overlap = len(query_terms & source_terms) / len(query_terms) if query_terms else 0
        
        # Weighted combination
        relevance = (0.6 * jaccard_sim) + (0.4 * query_overlap)
        return min(1.0, max(0.0, relevance))
    
    def _calculate_confidence_score(
        self,
        sources: List[SourceReference],
        answer: str,
    ) -> float:
        """
        Calculate confidence score based on:
        - Number and quality of sources
        - Answer length (longer, more detailed answers are typically more confident)
        - Average source confidence
        """
        if not sources:
            # No sources → lower confidence
            base_score = 0.3
        else:
            # Average source confidence
            avg_source_confidence = sum(s.confidence for s in sources) / len(sources)
            # Number of sources (diminishing returns)
            source_count_factor = min(1.0, len(sources) / 5.0)
            base_score = (0.5 * avg_source_confidence) + (0.5 * source_count_factor)
        
        # Consider answer length (more detail = higher confidence)
        word_count = len(answer.split())
        length_factor = min(1.0, word_count / 500.0)  # 500 words = max length factor
        
        confidence = (0.7 * base_score) + (0.3 * length_factor)
        return min(1.0, max(0.0, confidence))
    
    def _evaluate_faithfulness(
        self,
        answer: str,
        sources: List[SourceReference],
        user_query: str,
    ) -> float:
        """
        Evaluate faithfulness of answer to sources using OLLAMA.
        
        Faithfulness = how well the answer is supported by the sources.
        
        High faithfulness: Answer directly quotes/paraphrases sources
        Low faithfulness: Answer contradicts or goes beyond sources
        """
        if not sources:
            # No sources to be faithful to
            return 0.5
        
        try:
            # Create evaluation prompt
            source_text = "\n\n".join([
                f"Source {i+1}: {s.text_snippet}"
                for i, s in enumerate(sources[:3])  # Use top 3 sources for evaluation
            ])
            
            eval_prompt = f"""Evaluate the faithfulness of the following answer to the provided sources.

Sources:
{source_text}

Answer:
{answer}

Question: How faithful is this answer to the sources? (0-10 scale)
- 10: Answer is directly supported by sources with no contradictions
- 7-9: Answer is mostly supported by sources with minor additions
- 4-6: Answer is partially supported; some facts from sources, some outside
- 1-3: Answer contradicts sources or is mostly unsupported
- 0: Answer is completely unsupported by sources

Respond with ONLY the score (0-10) on the first line, then brief explanation.
"""
            
            response = self.llm_client.generate(
                prompt=eval_prompt,
                temperature=0.3,  # Lower temperature for more consistent scoring
                max_tokens=100,
            )
            
            # Extract score from response
            lines = response.strip().split('\n')
            score_text = lines[0].strip()
            
            # Parse score (e.g., "8" or "8/10")
            score_match = re.search(r'(\d+)', score_text)
            if score_match:
                score = int(score_match.group(1))
                # Normalize to 0-1 range
                faithfulness = score / 10.0
                logger.info(f"Faithfulness evaluation: {score}/10")
                return min(1.0, max(0.0, faithfulness))
            
            # Fallback if parsing fails
            return 0.5
            
        except Exception as e:
            logger.warning(f"Faithfulness evaluation failed: {str(e)}")
            # Return neutral score on error
            return 0.5
    
    def _calculate_source_coverage(
        self,
        sources: List[SourceReference],
        answer: str,
    ) -> float:
        """
        Calculate how well the sources cover the topics in the answer.
        
        High coverage: Sources address most topics mentioned in answer
        Low coverage: Many topics in answer not covered by sources
        """
        if not sources:
            return 0.0
        
        # Simple heuristic: coverage based on number of relevant sources
        # and their relevance scores
        if len(sources) >= 3:
            coverage = 0.9
        elif len(sources) == 2:
            coverage = 0.7
        elif len(sources) == 1:
            coverage = 0.5
        else:
            coverage = 0.0
        
        # Boost by average source confidence
        avg_relevance = sum(
            s.metadata.get("relevance_to_answer", 0)
            for s in sources
        ) / len(sources) if sources else 0
        
        final_coverage = (0.5 * coverage) + (0.5 * avg_relevance)
        return min(1.0, max(0.0, final_coverage))


def get_answer_quality_assessor() -> AnswerQualityAssessor:
    """Get or create the quality assessor instance"""
    return AnswerQualityAssessor()
