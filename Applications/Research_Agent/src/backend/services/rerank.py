"""
Advanced reranking strategies for search results.
Implements cross-encoder, semantic diversity, and ensemble reranking.
"""
from __future__ import annotations
import numpy as np
from typing import List, Optional
from datetime import datetime

from backend.models.states import RetrievalResult, RankedResult


class AdvancedRanker:
    """
    Multi-strategy reranking engine.
    Combines multiple ranking approaches for better results.
    """
    
    def __init__(self):
        self.cross_encoder = None
        self._init_cross_encoder()
    
    def _init_cross_encoder(self):
        """Initialize cross-encoder model for reranking"""
        try:
            from sentence_transformers import CrossEncoder
            print("[AdvancedRanker] Loading cross-encoder model: mixedbread-ai/mxbai-rerank-xsmall-v1")
            self.cross_encoder = CrossEncoder(
                "mixedbread-ai/mxbai-rerank-xsmall-v1",
                max_length=512,
            )
            print("[AdvancedRanker] Cross-encoder loaded successfully")
        except ImportError:
            print("[AdvancedRanker] Warning: sentence-transformers not installed. Cross-encoder reranking disabled.")
        except Exception as e:
            print(f"[AdvancedRanker] Warning: Failed to load cross-encoder: {e}")
    
    # ========================================================================
    # CROSS-ENCODER RERANKING
    # ========================================================================
    
    def cross_encoder_rerank(
        self,
        query: str,
        results: List[RetrievalResult],
        top_k: int = 20,
    ) -> List[RankedResult]:
        """
        Rerank results using cross-encoder model.
        Best accuracy, but slower than vector-based scoring.
        
        Args:
            query: Search query
            results: Retrieved results from vector search
            top_k: Keep top-k results
            
        Returns:
            List of RankedResult objects sorted by combined score
        """
        if not self.cross_encoder:
            print("[cross_encoder_rerank] Cross-encoder not available, skipping")
            return self._fallback_rerank(results, top_k)
        
        if not results:
            return []
        
        try:
            print(f"[cross_encoder_rerank] Reranking {len(results)} results with cross-encoder")
            
            # Prepare query-passage pairs
            passages = [r.text for r in results]
            pairs = [[query, passage] for passage in passages]
            
            # Get cross-encoder scores
            scores = self.cross_encoder.predict(pairs, batch_size=32, show_progress_bar=False)
            
            # Normalize scores to 0-1 range
            scores = (scores - scores.min()) / (scores.max() - scores.min() + 1e-8)
            
            # Create ranked results
            ranked = []
            for idx, (result, ce_score) in enumerate(zip(results, scores)):
                # Combine original retrieval score with cross-encoder score
                combined_score = 0.5 * result.score + 0.5 * float(ce_score)
                
                ranked_result = RankedResult(
                    chunk_id=result.chunk_id,
                    paper_id=result.paper_id,
                    section_id=result.section_id,
                    text=result.text,
                    primary_score=result.score,
                    rerank_score=float(ce_score),
                    combined_score=combined_score,
                    rank=idx + 1,
                    source=result.source,
                )
                ranked.append(ranked_result)
            
            # Sort by combined score descending
            ranked.sort(key=lambda x: x.combined_score, reverse=True)
            
            # Update ranks
            for idx, r in enumerate(ranked[:top_k]):
                r.rank = idx + 1
            
            print(f"[cross_encoder_rerank] Reranked to top-{len(ranked[:top_k])}")
            
            return ranked[:top_k]
            
        except Exception as e:
            print(f"[cross_encoder_rerank] Error: {e}, falling back to simple reranking")
            return self._fallback_rerank(results, top_k)
    
    # ========================================================================
    # SEMANTIC DIVERSITY RERANKING (MMR)
    # ========================================================================
    
    def semantic_diversity_rerank(
        self,
        results: List[RetrievalResult],
        top_k: int = 20,
        diversity_weight: float = 0.3,
    ) -> List[RankedResult]:
        """
        Rerank using Maximal Marginal Relevance (MMR).
        Balances relevance and diversity to avoid similar results.
        
        Formula: MMR_i = λ * sim(doc_i, query) - (1-λ) * max(sim(doc_i, doc_j))
        where doc_j are already selected documents
        
        Args:
            results: Retrieved results
            top_k: Number of diverse results to select
            diversity_weight: Weight for diversity (0.0-1.0)
            
        Returns:
            List of RankedResult objects
        """
        if not results:
            return []
        
        try:
            print(f"[semantic_diversity_rerank] Applying MMR with diversity_weight={diversity_weight}")
            
            # Get embeddings for diversity calculation
            from backend.services.embeddings import Embedder
            embedder = Embedder()
            
            texts = [r.text for r in results]
            embeddings = embedder.encode(texts)  # Shape: (n, dim)
            embeddings = np.array([e for e in embeddings], dtype=np.float32)
            
            # Normalize embeddings
            embeddings = embeddings / (np.linalg.norm(embeddings, axis=1, keepdims=True) + 1e-8)
            
            # MMR selection
            selected_indices = []
            remaining_indices = set(range(len(results)))
            
            # Select top result
            first_idx = np.argmax([r.score for r in results])
            selected_indices.append(first_idx)
            remaining_indices.remove(first_idx)
            
            # Greedily select remaining results
            for _ in range(min(top_k - 1, len(remaining_indices))):
                best_idx = None
                best_score = -float('inf')
                
                for idx in remaining_indices:
                    # Relevance: original retrieval score
                    relevance = results[idx].score
                    
                    # Redundancy: max similarity to already selected results
                    selected_embeddings = embeddings[selected_indices]
                    current_embedding = embeddings[idx:idx+1]
                    similarities = np.dot(current_embedding, selected_embeddings.T)[0]
                    redundancy = np.max(similarities) if len(selected_embeddings) > 0 else 0.0
                    
                    # MMR score
                    mmr_score = diversity_weight * relevance - (1 - diversity_weight) * redundancy
                    
                    if mmr_score > best_score:
                        best_score = mmr_score
                        best_idx = idx
                
                if best_idx is not None:
                    selected_indices.append(best_idx)
                    remaining_indices.remove(best_idx)
            
            # Create ranked results from selected indices
            ranked = []
            for rank, idx in enumerate(selected_indices):
                result = results[idx]
                ranked_result = RankedResult(
                    chunk_id=result.chunk_id,
                    paper_id=result.paper_id,
                    section_id=result.section_id,
                    text=result.text,
                    primary_score=result.score,
                    rerank_score=result.score,  # Same as primary for diversity reranking
                    combined_score=result.score,
                    rank=rank + 1,
                    source=result.source,
                )
                ranked.append(ranked_result)
            
            print(f"[semantic_diversity_rerank] Selected {len(ranked)} diverse results")
            return ranked
            
        except Exception as e:
            print(f"[semantic_diversity_rerank] Error: {e}, falling back to simple reranking")
            return self._fallback_rerank(results, top_k)
    
    # ========================================================================
    # ENSEMBLE RERANKING
    # ========================================================================
    
    def ensemble_rerank(
        self,
        query: str,
        results: List[RetrievalResult],
        top_k: int = 20,
        strategies: List[str] = ["cross_encoder", "semantic_diversity"],
        weights: List[float] = [0.6, 0.4],
    ) -> List[RankedResult]:
        """
        Combine multiple reranking strategies with weighted ensemble.
        
        Args:
            query: Search query
            results: Retrieved results
            top_k: Number of results to return
            strategies: List of strategies to use
            weights: Weights for each strategy (must sum to 1.0)
            
        Returns:
            List of RankedResult objects with ensemble scores
        """
        if not results:
            return []
        
        if len(strategies) != len(weights):
            raise ValueError("strategies and weights must have same length")
        
        if abs(sum(weights) - 1.0) > 0.01:
            raise ValueError("weights must sum to 1.0")
        
        try:
            print(f"[ensemble_rerank] Ensemble reranking with strategies: {strategies}")
            
            # Run each strategy
            ranked_results_per_strategy = []
            
            for strategy, weight in zip(strategies, weights):
                if strategy == "cross_encoder":
                    ranked = self.cross_encoder_rerank(query, results, top_k=len(results))
                elif strategy == "semantic_diversity":
                    ranked = self.semantic_diversity_rerank(results, top_k=len(results), diversity_weight=0.3)
                else:
                    print(f"[ensemble_rerank] Unknown strategy: {strategy}, skipping")
                    continue
                
                ranked_results_per_strategy.append((ranked, weight))
            
            if not ranked_results_per_strategy:
                return self._fallback_rerank(results, top_k)
            
            # Aggregate scores
            score_map = {}  # chunk_id -> aggregated_score
            
            for ranked_list, weight in ranked_results_per_strategy:
                for result in ranked_list:
                    # Normalize rank-based score (inverse of rank)
                    rank_score = 1.0 - (result.rank - 1) / max(len(ranked_list), 1)
                    
                    if result.chunk_id not in score_map:
                        score_map[result.chunk_id] = 0.0
                    
                    score_map[result.chunk_id] += weight * rank_score
            
            # Create final ranked results
            ranked = []
            
            for result in results:
                if result.chunk_id in score_map:
                    ensemble_score = score_map[result.chunk_id]
                else:
                    ensemble_score = 0.0
                
                ranked_result = RankedResult(
                    chunk_id=result.chunk_id,
                    paper_id=result.paper_id,
                    section_id=result.section_id,
                    text=result.text,
                    primary_score=result.score,
                    rerank_score=ensemble_score,
                    combined_score=0.5 * result.score + 0.5 * ensemble_score,
                    rank=0,  # Will be set below
                    source=result.source,
                )
                ranked.append(ranked_result)
            
            # Sort by combined score
            ranked.sort(key=lambda x: x.combined_score, reverse=True)
            
            # Update ranks and keep top-k
            for idx, r in enumerate(ranked[:top_k]):
                r.rank = idx + 1
            
            print(f"[ensemble_rerank] Ensemble result: top-{len(ranked[:top_k])}")
            
            return ranked[:top_k]
            
        except Exception as e:
            print(f"[ensemble_rerank] Error: {e}, falling back to simple reranking")
            return self._fallback_rerank(results, top_k)
    
    # ========================================================================
    # FALLBACK RERANKING
    # ========================================================================
    
    def _fallback_rerank(
        self,
        results: List[RetrievalResult],
        top_k: int = 20,
    ) -> List[RankedResult]:
        """
        Simple fallback reranking when advanced methods fail.
        Just sorts by original retrieval score.
        """
        ranked = []
        
        for idx, result in enumerate(sorted(results, key=lambda x: x.score, reverse=True)[:top_k]):
            ranked_result = RankedResult(
                chunk_id=result.chunk_id,
                paper_id=result.paper_id,
                section_id=result.section_id,
                text=result.text,
                primary_score=result.score,
                rerank_score=result.score,
                combined_score=result.score,
                rank=idx + 1,
                source=result.source,
            )
            ranked.append(ranked_result)
        
        return ranked


# ============================================================================
# SINGLETON RANKER INSTANCE
# ============================================================================

_ranker: Optional[AdvancedRanker] = None


def get_ranker() -> AdvancedRanker:
    """Get or create the global ranker (singleton)"""
    global _ranker
    if _ranker is None:
        _ranker = AdvancedRanker()
    return _ranker


def set_ranker(ranker: AdvancedRanker) -> None:
    """Set the global ranker (for testing)"""
    global _ranker
    _ranker = ranker
