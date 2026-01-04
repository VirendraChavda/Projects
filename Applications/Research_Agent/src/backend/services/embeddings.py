from __future__ import annotations
import numpy as np
import requests
from typing import Optional
from backend.config import settings

class Embedder:
    """OLLAMA-based embeddings using local models"""
    
    def __init__(self, model_name: Optional[str] = None, api_url: Optional[str] = None):
        """
        Initialize embedder with OLLAMA model.
        
        Args:
            model_name: Model name (default: nomic-embed-text)
            api_url: OLLAMA API endpoint (default: from settings)
        """
        self.model = model_name or settings.embed_model
        self.api_url = api_url or settings.embed_api_url
        
        print(f"[Embedder] Initialized OLLAMA embeddings with model: {self.model} at {self.api_url}")
        self._verify_connection()
    
    def _verify_connection(self) -> bool:
        """Verify OLLAMA is running and accessible"""
        try:
            response = requests.post(
                self.api_url,
                json={
                    "model": self.model,
                    "prompt": "test",
                },
                timeout=5
            )
            if response.status_code == 200:
                print(f"[Embedder] OLLAMA connection verified")
                return True
        except Exception as e:
            print(f"[Embedder] Warning: Could not verify OLLAMA connection: {str(e)}")
        return False

    def encode(self, texts: list[str]) -> np.ndarray:
        """
        Generate embeddings for a list of texts using OLLAMA.
        
        Args:
            texts: List of text strings to embed
            
        Returns:
            numpy array of embeddings with shape (len(texts), embedding_dim)
        """
        embeddings = []
        
        for text in texts:
            try:
                response = requests.post(
                    self.api_url,
                    json={
                        "model": self.model,
                        "prompt": text,
                    },
                    timeout=60
                )
                
                if response.status_code != 200:
                    raise RuntimeError(f"OLLAMA API error: {response.status_code}")
                
                result = response.json()
                embedding = result.get("embedding", [])
                embeddings.append(embedding)
            except Exception as e:
                print(f"[Embedder] Error encoding text: {str(e)}")
                # Return zero vector on error
                embeddings.append([0.0] * 384)  # Default embedding dimension
        
        # Convert to numpy array and normalize
        embeddings_array = np.array(embeddings, dtype="float32")
        
        # Normalize embeddings (L2 normalization)
        norms = np.linalg.norm(embeddings_array, axis=1, keepdims=True)
        norms[norms == 0] = 1  # Avoid division by zero
        embeddings_array = embeddings_array / norms
        
        return embeddings_array
