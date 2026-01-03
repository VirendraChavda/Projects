"""
Django Channels WebSocket consumer for real-time progress streaming.
Handles ingestion progress updates and analysis streaming.
"""
import json
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async

from backend.langgraph.graphs import get_ingestion_graph
from backend.models.states import IngestionState


class IngestionProgressConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for streaming ingestion progress.
    
    Client events:
    - "start_ingestion": {"days": 7, "max_results": 100}
    - "cancel": {}
    
    Server events:
    - "progress": {"status": str, "progress": float, ...}
    - "complete": {"docs_ingested": int, ...}
    - "error": {"error": str}
    """
    
    async def connect(self):
        """Handle WebSocket connection"""
        await self.accept()
        self.ingestion_task = None
        print("[IngestionProgressConsumer] Client connected")
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        # Cancel ongoing ingestion
        if self.ingestion_task and not self.ingestion_task.done():
            self.ingestion_task.cancel()
        print(f"[IngestionProgressConsumer] Client disconnected with code {close_code}")
    
    async def receive(self, text_data):
        """Handle incoming WebSocket messages"""
        try:
            message = json.loads(text_data)
            event_type = message.get('type')
            
            if event_type == 'start_ingestion':
                await self.handle_start_ingestion(message)
            elif event_type == 'cancel':
                await self.handle_cancel()
            else:
                await self.send_error(f"Unknown event type: {event_type}")
                
        except json.JSONDecodeError:
            await self.send_error("Invalid JSON")
        except Exception as e:
            await self.send_error(f"Error processing message: {str(e)}")
    
    async def handle_start_ingestion(self, message):
        """Start ingestion workflow and stream progress"""
        try:
            days = message.get('days', 7)
            max_results = message.get('max_results', 100)
            
            # Validate
            if not (1 <= days <= 365):
                await self.send_error("days must be between 1 and 365")
                return
            
            if not (1 <= max_results <= 1000):
                await self.send_error("max_results must be between 1 and 1000")
                return
            
            print(f"[IngestionProgressConsumer] Starting ingestion: days={days}, max_results={max_results}")
            
            # Start ingestion task
            self.ingestion_task = asyncio.create_task(
                self._run_ingestion(days, max_results)
            )
            
        except Exception as e:
            await self.send_error(f"Failed to start ingestion: {str(e)}")
    
    async def _run_ingestion(self, days: int, max_results: int):
        """Run ingestion in background and stream progress"""
        try:
            # Create initial state
            state = IngestionState(
                days_back=days,
                max_results=max_results
            )
            
            # Get graph
            graph = get_ingestion_graph()
            
            # Execute graph (sync, run in executor)
            loop = asyncio.get_event_loop()
            
            # Execute with streaming
            for step in graph.stream(state):
                # Send progress update
                progress_data = {
                    "type": "progress",
                    "status": step.status.value,
                    "progress_percent": step.progress_percent,
                    "docs_found": step.docs_found,
                    "docs_existing": step.docs_existing,
                    "docs_new": step.docs_new,
                    "docs_ingested": step.docs_ingested,
                    "docs_failed": step.docs_failed,
                }
                
                await self.send(text_data=json.dumps(progress_data))
                
                # Yield control to allow other tasks
                await asyncio.sleep(0.1)
            
            # Send completion
            await self.send(json.dumps({
                "type": "complete",
                "docs_ingested": step.docs_ingested,
                "docs_failed": step.docs_failed,
                "message": "Ingestion completed"
            }))
            
        except asyncio.CancelledError:
            await self.send_error("Ingestion cancelled")
        except Exception as e:
            await self.send_error(f"Ingestion failed: {str(e)}")
    
    async def handle_cancel(self):
        """Cancel ongoing ingestion"""
        if self.ingestion_task and not self.ingestion_task.done():
            self.ingestion_task.cancel()
            print("[IngestionProgressConsumer] Ingestion cancelled")
            await self.send(json.dumps({
                "type": "cancelled",
                "message": "Ingestion cancelled by user"
            }))
    
    async def send_error(self, error_message: str):
        """Send error message to client"""
        await self.send(json.dumps({
            "type": "error",
            "error": error_message
        }))


class ResearchAnalysisConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time research analysis updates.
    
    Client events:
    - "execute_analysis": {"query": str, "analysis_type": str}
    - "cancel": {}
    
    Server events:
    - "retrieval_complete": {"count": int}
    - "reranking_complete": {"count": int}
    - "analysis_complete": {"type": str, "result": dict}
    - "complete": {"final_response": dict}
    - "error": {"error": str}
    """
    
    async def connect(self):
        """Handle WebSocket connection"""
        await self.accept()
        self.analysis_task = None
        print("[ResearchAnalysisConsumer] Client connected")
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        if self.analysis_task and not self.analysis_task.done():
            self.analysis_task.cancel()
        print(f"[ResearchAnalysisConsumer] Client disconnected with code {close_code}")
    
    async def receive(self, text_data):
        """Handle incoming WebSocket messages"""
        try:
            message = json.loads(text_data)
            event_type = message.get('type')
            
            if event_type == 'execute_analysis':
                await self.handle_execute_analysis(message)
            elif event_type == 'cancel':
                await self.handle_cancel()
            else:
                await self.send_error(f"Unknown event type: {event_type}")
                
        except json.JSONDecodeError:
            await self.send_error("Invalid JSON")
        except Exception as e:
            await self.send_error(f"Error processing message: {str(e)}")
    
    async def handle_execute_analysis(self, message):
        """Execute analysis workflow and stream progress"""
        try:
            query = message.get('query', '')
            analysis_type = message.get('analysis_type', 'comprehensive')
            
            if not query or len(query.strip()) < 3:
                await self.send_error("Query must be at least 3 characters")
                return
            
            print(f"[ResearchAnalysisConsumer] Starting analysis: query='{query}'")
            
            # Start analysis task
            self.analysis_task = asyncio.create_task(
                self._run_analysis(query, analysis_type)
            )
            
        except Exception as e:
            await self.send_error(f"Failed to start analysis: {str(e)}")
    
    async def _run_analysis(self, query: str, analysis_type: str):
        """Run analysis in background and stream progress"""
        try:
            from backend.langgraph.graphs import get_research_graph
            from backend.models.states import ResearchState
            
            # Create initial state
            state = ResearchState(
                user_query=query,
                analysis_type=analysis_type
            )
            
            # Get graph
            graph = get_research_graph()
            
            # Execute graph with streaming
            for step in graph.stream(state):
                # Send progress updates for different stages
                if step.retrieval_results:
                    await self.send(json.dumps({
                        "type": "retrieval_complete",
                        "count": len(step.retrieval_results),
                        "message": f"Retrieved {len(step.retrieval_results)} results"
                    }))
                
                if step.ranked_results:
                    await self.send(json.dumps({
                        "type": "reranking_complete",
                        "count": len(step.ranked_results),
                        "message": f"Reranked to top {len(step.ranked_results)}"
                    }))
                
                # Yield control
                await asyncio.sleep(0.1)
            
            # Send final response
            await self.send(json.dumps({
                "type": "complete",
                "final_response": step.final_response
            }))
            
        except asyncio.CancelledError:
            await self.send_error("Analysis cancelled")
        except Exception as e:
            await self.send_error(f"Analysis failed: {str(e)}")
    
    async def handle_cancel(self):
        """Cancel ongoing analysis"""
        if self.analysis_task and not self.analysis_task.done():
            self.analysis_task.cancel()
            print("[ResearchAnalysisConsumer] Analysis cancelled")
            await self.send(json.dumps({
                "type": "cancelled",
                "message": "Analysis cancelled by user"
            }))
    
    async def send_error(self, error_message: str):
        """Send error message to client"""
        await self.send(json.dumps({
            "type": "error",
            "error": error_message
        }))
