"""
Django management command to run the ingestion workflow.

Usage:
    python manage.py run_ingestion --days 7 --max_results 100
    python manage.py run_ingestion --days 30  # defaults to 100 results
"""
from django.core.management.base import BaseCommand
from django.conf import settings

import sys
sys.path.insert(0, str(settings.BASE_DIR.parent))

from backend.langgraph.graphs import get_ingestion_graph
from backend.models.states import IngestionState, IngestionStatus


class Command(BaseCommand):
    """Management command for running ingestion workflow."""
    
    help = 'Run the paper ingestion workflow'
    
    def add_arguments(self, parser):
        """Add command arguments."""
        parser.add_argument(
            '--days',
            type=int,
            default=7,
            help='Number of days back to search (default: 7)'
        )
        parser.add_argument(
            '--max_results',
            type=int,
            default=100,
            help='Maximum results to fetch (default: 100)'
        )
    
    def handle(self, *args, **options):
        """Execute the command."""
        days = options['days']
        max_results = options['max_results']
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Starting ingestion: days={days}, max_results={max_results}'
            )
        )
        
        try:
            # Create initial state
            state = IngestionState(
                days_back=days,
                max_results=max_results
            )
            
            # Get graph
            graph = get_ingestion_graph()
            
            # Execute graph with streaming
            for step_state in graph.stream(state):
                # Display progress
                self.stdout.write(
                    f"[{step_state.status.value}] "
                    f"Progress: {step_state.progress_percent}% | "
                    f"Found: {step_state.docs_found} | "
                    f"Ingested: {step_state.docs_ingested} | "
                    f"Failed: {step_state.docs_failed}"
                )
            
            # Final summary
            self.stdout.write(
                self.style.SUCCESS(
                    f'\nIngestion completed!\n'
                    f'Total documents found: {step_state.docs_found}\n'
                    f'Documents ingested: {step_state.docs_ingested}\n'
                    f'Documents failed: {step_state.docs_failed}\n'
                    f'Documents skipped (existing): {step_state.docs_existing}'
                )
            )
            
        except KeyboardInterrupt:
            self.stdout.write(
                self.style.WARNING('\nIngestion cancelled by user')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Ingestion failed: {str(e)}')
            )
            raise
