"""
Analysis graph nodes for gap analysis, design suggestions, and pattern detection.
These nodes process ranked results and generate insights using LLM analysis.
"""
from __future__ import annotations
import json
from typing import Any
from datetime import datetime

from backend.models.states import (
    ResearchState,
    GapAnalysis,
    DesignSuggestion,
    PatternDetection,
    FutureDirections,
    RankedResult,
)
from backend.services.llm_client import (
    get_llm_client,
    SYSTEM_PROMPT_ANALYSIS,
    PROMPT_TEMPLATE_GAP_ANALYSIS,
    PROMPT_TEMPLATE_DESIGN_SUGGESTION,
    PROMPT_TEMPLATE_PATTERN_DETECTION,
    PROMPT_TEMPLATE_FUTURE_DIRECTIONS,
)


# ============================================================================
# NODE 1: GAP ANALYSIS
# ============================================================================

def gap_analysis_node(state: ResearchState) -> ResearchState:
    """
    Analyze research gaps based on retrieved papers using LLM.
    Identifies underexplored areas and missing benchmarks.
    
    Updates:
    - gap_analysis: GapAnalysis object with LLM-generated findings
    """
    try:
        if not state.ranked_results:
            print("[gap_analysis_node] No ranked results for gap analysis")
            state.gap_analysis = GapAnalysis(confidence_score=0.0)
            return state
        
        print(f"[gap_analysis_node] Analyzing research gaps across {len(state.ranked_results)} papers using LLM")
        
        # Extract text from ranked results
        papers_context = "\n\n".join([
            f"[{r.paper_id}] {r.text[:1000]}"
            for r in state.ranked_results[:10]  # Use top 10 for context
        ])
        
        # Use LLM for analysis
        try:
            llm_client = get_llm_client()
            prompt = PROMPT_TEMPLATE_GAP_ANALYSIS.format(papers_context=papers_context)
            
            response = llm_client.generate(
                prompt=prompt,
                system_prompt=SYSTEM_PROMPT_ANALYSIS,
                temperature=0.7,
                max_tokens=2000,
            )
            
            # Parse JSON response
            response_data = json.loads(response)
            
            state.gap_analysis = GapAnalysis(
                identified_gaps=response_data.get("identified_gaps", []),
                research_areas=response_data.get("research_areas", []),
                missing_benchmarks=response_data.get("missing_benchmarks", []),
                underexplored_topics=response_data.get("underexplored_topics", []),
                confidence_score=0.85  # LLM-based, high confidence
            )
            
            print(f"[gap_analysis_node] Found {len(state.gap_analysis.identified_gaps)} gaps with high confidence")
            
        except json.JSONDecodeError:
            # Fallback to heuristic if LLM response isn't valid JSON
            print("[gap_analysis_node] Warning: LLM response wasn't valid JSON, falling back to heuristic")
            gaps = _detect_gaps_heuristic(papers_context, state.user_query)
            state.gap_analysis = GapAnalysis(
                identified_gaps=gaps.get("gaps", []),
                research_areas=gaps.get("areas", []),
                missing_benchmarks=gaps.get("benchmarks", []),
                underexplored_topics=gaps.get("underexplored", []),
                confidence_score=0.6
            )
        except Exception as llm_error:
            # Fallback to heuristic if LLM fails
            print(f"[gap_analysis_node] Warning: LLM analysis failed ({llm_error}), falling back to heuristic")
            gaps = _detect_gaps_heuristic(papers_context, state.user_query)
            state.gap_analysis = GapAnalysis(
                identified_gaps=gaps.get("gaps", []),
                research_areas=gaps.get("areas", []),
                missing_benchmarks=gaps.get("benchmarks", []),
                underexplored_topics=gaps.get("underexplored", []),
                confidence_score=0.6
            )
        
        return state
        
    except Exception as e:
        state.error = f"Gap analysis failed: {str(e)}"
        print(f"[gap_analysis_node] Error: {state.error}")
        return state


def _detect_gaps_heuristic(text: str, query: str) -> dict:
    """Simple heuristic gap detection (placeholder)"""
    return {
        "gaps": [
            "Limited exploration of domain adaptation",
            "Missing comparison with recent SOTA methods",
            "Insufficient analysis of failure cases",
        ],
        "areas": [
            "Robustness and adversarial training",
            "Computational efficiency",
            "Few-shot learning scenarios",
        ],
        "benchmarks": [
            "Evaluation on adversarial examples",
            "Cross-domain generalization metrics",
            "Real-world deployment benchmarks",
        ],
        "underexplored": [
            "Interpretability in domain-specific contexts",
            "Integration with existing legacy systems",
            "Scalability to production environments",
        ],
    }


# ============================================================================
# NODE 2: DESIGN SUGGESTION
# ============================================================================

def design_suggestion_node(state: ResearchState) -> ResearchState:
    """
    Generate design suggestions based on retrieved papers using LLM.
    Proposes architectural improvements and implementation strategies.
    
    Updates:
    - design_suggestions: DesignSuggestion object with LLM-generated suggestions
    """
    try:
        if not state.ranked_results:
            print("[design_suggestion_node] No ranked results for design suggestions")
            state.design_suggestions = DesignSuggestion(confidence_score=0.0)
            return state
        
        print(f"[design_suggestion_node] Generating design suggestions from {len(state.ranked_results)} papers using LLM")
        
        # Extract text from ranked results
        papers_context = "\n\n".join([
            f"[{r.paper_id}] {r.text[:1000]}"
            for r in state.ranked_results[:10]
        ])
        
        # Use LLM for design suggestions
        try:
            llm_client = get_llm_client()
            prompt = PROMPT_TEMPLATE_DESIGN_SUGGESTION.format(papers_context=papers_context)
            
            response = llm_client.generate(
                prompt=prompt,
                system_prompt=SYSTEM_PROMPT_ANALYSIS,
                temperature=0.7,
                max_tokens=2000,
            )
            
            # Parse JSON response
            response_data = json.loads(response)
            
            state.design_suggestions = DesignSuggestion(
                suggested_approaches=response_data.get("suggested_approaches", []),
                architectural_improvements=response_data.get("architectural_improvements", []),
                implementation_strategies=response_data.get("implementation_strategies", []),
                trade_offs=response_data.get("trade_offs", []),
                confidence_score=0.85  # LLM-based, high confidence
            )
            
            print(f"[design_suggestion_node] Generated {len(state.design_suggestions.suggested_approaches)} approaches with high confidence")
            
        except json.JSONDecodeError:
            # Fallback to heuristic
            print("[design_suggestion_node] Warning: LLM response wasn't valid JSON, falling back to heuristic")
            suggestions = _generate_design_suggestions_heuristic(papers_context)
            state.design_suggestions = DesignSuggestion(
                suggested_approaches=suggestions.get("approaches", []),
                architectural_improvements=suggestions.get("improvements", []),
                implementation_strategies=suggestions.get("strategies", []),
                trade_offs=suggestions.get("tradeoffs", []),
                confidence_score=0.6
            )
        except Exception as llm_error:
            # Fallback to heuristic
            print(f"[design_suggestion_node] Warning: LLM failed ({llm_error}), falling back to heuristic")
            suggestions = _generate_design_suggestions_heuristic(papers_context)
            state.design_suggestions = DesignSuggestion(
                suggested_approaches=suggestions.get("approaches", []),
                architectural_improvements=suggestions.get("improvements", []),
                implementation_strategies=suggestions.get("strategies", []),
                trade_offs=suggestions.get("tradeoffs", []),
                confidence_score=0.6
            )
        
        return state
        
    except Exception as e:
        state.error = f"Design suggestion failed: {str(e)}"
        print(f"[design_suggestion_node] Error: {state.error}")
        return state


def _generate_design_suggestions_heuristic(text: str) -> dict:
    """Simple heuristic design suggestion generation (placeholder)"""
    return {
        "approaches": [
            "Implement modular architecture with pluggable components",
            "Use attention mechanisms for feature importance",
            "Apply knowledge distillation for efficiency",
        ],
        "improvements": [
            "Decouple model inference from business logic",
            "Implement caching layer for embedding retrieval",
            "Add monitoring and observability instrumentation",
        ],
        "strategies": [
            "Start with small-scale MVP and iterate",
            "Use containerization for deployment consistency",
            "Implement A/B testing infrastructure",
        ],
        "tradeoffs": [
            "Accuracy vs latency: Consider quantization or pruning",
            "Generalization vs specialization: Fine-tune vs transfer learning",
            "Complexity vs maintainability: Feature engineering overhead",
        ],
    }


# ============================================================================
# NODE 3: PATTERN DETECTION
# ============================================================================

def pattern_detection_node(state: ResearchState) -> ResearchState:
    """
    Detect patterns and trends in retrieved papers using LLM.
    Identifies emerging methodologies and common approaches.
    
    Updates:
    - pattern_detection: PatternDetection object with LLM-generated patterns
    """
    try:
        if not state.ranked_results:
            print("[pattern_detection_node] No ranked results for pattern detection")
            state.pattern_detection = PatternDetection(confidence_score=0.0)
            return state
        
        print(f"[pattern_detection_node] Detecting patterns across {len(state.ranked_results)} papers using LLM")
        
        papers_context = "\n\n".join([
            f"[{r.paper_id}] {r.text[:1000]}"
            for r in state.ranked_results[:10]
        ])
        
        # Use LLM for pattern detection
        try:
            llm_client = get_llm_client()
            prompt = PROMPT_TEMPLATE_PATTERN_DETECTION.format(papers_context=papers_context)
            
            response = llm_client.generate(
                prompt=prompt,
                system_prompt=SYSTEM_PROMPT_ANALYSIS,
                temperature=0.7,
                max_tokens=2000,
            )
            
            # Parse JSON response
            response_data = json.loads(response)
            
            state.pattern_detection = PatternDetection(
                patterns_found=response_data.get("patterns_found", []),
                trend_analysis=response_data.get("trend_analysis", []),
                emerging_methods=response_data.get("emerging_methods", []),
                confidence_score=0.80  # LLM-based, high confidence
            )
            
            print(f"[pattern_detection_node] Found {len(state.pattern_detection.patterns_found)} patterns with high confidence")
            
        except json.JSONDecodeError:
            # Fallback
            print("[pattern_detection_node] Warning: LLM response wasn't valid JSON, falling back to heuristic")
            patterns = _detect_patterns_heuristic(papers_context)
            state.pattern_detection = PatternDetection(
                patterns_found=patterns.get("patterns", []),
                trend_analysis=patterns.get("trends", []),
                emerging_methods=patterns.get("emerging", []),
                confidence_score=0.55
            )
        except Exception as llm_error:
            # Fallback
            print(f"[pattern_detection_node] Warning: LLM failed ({llm_error}), falling back to heuristic")
            patterns = _detect_patterns_heuristic(papers_context)
            state.pattern_detection = PatternDetection(
                patterns_found=patterns.get("patterns", []),
                trend_analysis=patterns.get("trends", []),
                emerging_methods=patterns.get("emerging", []),
                confidence_score=0.55
            )
        
        return state
        
    except Exception as e:
        state.error = f"Pattern detection failed: {str(e)}"
        print(f"[pattern_detection_node] Error: {state.error}")
        return state


def _detect_patterns_heuristic(text: str) -> dict:
    """Simple heuristic pattern detection (placeholder)"""
    return {
        "patterns": [
            "Common use of Transformer-based architectures",
            "Shift towards multi-modal learning approaches",
            "Increased focus on efficient model compression",
        ],
        "trends": [
            "Growing emphasis on interpretability and explainability",
            "Rising adoption of federated and privacy-preserving learning",
            "Increasing integration of symbolic reasoning with neural methods",
        ],
        "emerging": [
            "Mixture of Experts (MoE) scaling paradigm",
            "In-context learning and few-shot adaptation",
            "Diffusion models for generative tasks",
        ],
    }


# ============================================================================
# NODE 4: FUTURE DIRECTIONS
# ============================================================================

def future_directions_node(state: ResearchState) -> ResearchState:
    """
    Generate future research directions based on analysis using LLM.
    Suggests next steps, open questions, and applications.
    
    Updates:
    - future_directions: FutureDirections object with LLM-generated directions
    """
    try:
        if not state.ranked_results:
            print("[future_directions_node] No ranked results for future directions")
            state.future_directions = FutureDirections(confidence_score=0.0)
            return state
        
        print(f"[future_directions_node] Analyzing future directions from {len(state.ranked_results)} papers using LLM")
        
        papers_context = "\n\n".join([
            f"[{r.paper_id}] {r.text[:1000]}"
            for r in state.ranked_results[:10]
        ])
        
        # Use LLM for future directions
        try:
            llm_client = get_llm_client()
            prompt = PROMPT_TEMPLATE_FUTURE_DIRECTIONS.format(papers_context=papers_context)
            
            response = llm_client.generate(
                prompt=prompt,
                system_prompt=SYSTEM_PROMPT_ANALYSIS,
                temperature=0.7,
                max_tokens=2000,
            )
            
            # Parse JSON response
            response_data = json.loads(response)
            
            state.future_directions = FutureDirections(
                next_steps=response_data.get("next_steps", []),
                open_questions=response_data.get("open_questions", []),
                future_applications=response_data.get("future_applications", []),
                confidence_score=0.75  # LLM-based, good confidence
            )
            
            print(f"[future_directions_node] Generated {len(state.future_directions.next_steps)} future directions with high confidence")
            
        except json.JSONDecodeError:
            # Fallback
            print("[future_directions_node] Warning: LLM response wasn't valid JSON, falling back to heuristic")
            directions = _generate_future_directions_heuristic(papers_context)
            state.future_directions = FutureDirections(
                next_steps=directions.get("next_steps", []),
                open_questions=directions.get("questions", []),
                future_applications=directions.get("applications", []),
                confidence_score=0.5
            )
        except Exception as llm_error:
            # Fallback
            print(f"[future_directions_node] Warning: LLM failed ({llm_error}), falling back to heuristic")
            directions = _generate_future_directions_heuristic(papers_context)
            state.future_directions = FutureDirections(
                next_steps=directions.get("next_steps", []),
                open_questions=directions.get("questions", []),
                future_applications=directions.get("applications", []),
                confidence_score=0.5
            )
        
        return state
        
    except Exception as e:
        state.error = f"Future directions analysis failed: {str(e)}"
        print(f"[future_directions_node] Error: {state.error}")
        return state


def _generate_future_directions_heuristic(text: str) -> dict:
    """Simple heuristic future directions generation (placeholder)"""
    return {
        "next_steps": [
            "Investigate hybrid approaches combining multiple paradigms",
            "Develop more efficient pre-training objectives",
            "Create better evaluation metrics for real-world performance",
        ],
        "questions": [
            "How can we achieve better generalization to out-of-distribution data?",
            "What are fundamental limits of scaling laws?",
            "How to integrate world knowledge more effectively?",
        ],
        "applications": [
            "Medical diagnosis and treatment planning systems",
            "Autonomous system decision-making under uncertainty",
            "Knowledge graph construction and reasoning",
        ],
    }


# ============================================================================
# NODE 5: AGGREGATE ANALYSIS
# ============================================================================

def aggregate_analysis_node(state: ResearchState) -> ResearchState:
    """
    Aggregate all analysis results into final response.
    Combines gap analysis, design suggestions, patterns, and future directions.
    
    Updates:
    - final_response: Complete aggregated response
    - completed_at: Timestamp
    """
    try:
        print("[aggregate_analysis_node] Aggregating analysis results")
        
        # Collect all recommendations from different analyses
        recommendations = []
        
        if state.gap_analysis:
            recommendations.extend([
                f"Address gap: {gap}" 
                for gap in state.gap_analysis.identified_gaps[:3]
            ])
        
        if state.design_suggestions:
            recommendations.extend([
                f"Implement: {sugg}"
                for sugg in state.design_suggestions.suggested_approaches[:3]
            ])
        
        if state.pattern_detection:
            recommendations.extend([
                f"Follow trend: {trend}"
                for trend in state.pattern_detection.trend_analysis[:3]
            ])
        
        # Collect source papers
        sources = list(set([r.paper_id for r in state.ranked_results]))
        
        # Calculate average confidence
        confidences = []
        if state.gap_analysis:
            confidences.append(state.gap_analysis.confidence_score)
        if state.design_suggestions:
            confidences.append(state.design_suggestions.confidence_score)
        if state.pattern_detection:
            confidences.append(state.pattern_detection.confidence_score)
        if state.future_directions:
            confidences.append(state.future_directions.confidence_score)
        
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        
        # Build final response
        state.final_response = {
            "query": state.user_query,
            "timestamp": datetime.now().isoformat(),
            "analysis_type": state.analysis_type,
            "retrieved_papers": len(set([r.paper_id for r in state.ranked_results])),
            "ranked_results_count": len(state.ranked_results),
            "used_mcp": len(state.mcp_results) > 0,
            "analysis": {
                "gap_analysis": state.gap_analysis.dict() if state.gap_analysis else None,
                "design_suggestions": state.design_suggestions.dict() if state.design_suggestions else None,
                "pattern_detection": state.pattern_detection.dict() if state.pattern_detection else None,
                "future_directions": state.future_directions.dict() if state.future_directions else None,
            },
            "recommendations": recommendations,
            "sources": sources,
            "average_confidence": avg_confidence,
        }
        
        state.completed_at = datetime.now()
        
        print("[aggregate_analysis_node] Analysis complete")
        
        return state
        
    except Exception as e:
        state.error = f"Aggregation failed: {str(e)}"
        print(f"[aggregate_analysis_node] Error: {state.error}")
        return state
