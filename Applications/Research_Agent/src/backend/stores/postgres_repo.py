"""
PostgreSQL repository for storing paper metadata.
Uses SQLAlchemy ORM for database operations and automatic migrations.
Handles duplicate detection, metadata persistence, and query optimization.
"""
from __future__ import annotations
from typing import List, Optional, Dict, Any
from datetime import datetime
from contextlib import contextmanager
import os

from sqlalchemy import (
    Column, String, Text, Integer, DateTime, Boolean, create_engine, func
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, scoped_session
from sqlalchemy.exc import SQLAlchemyError

from backend.services.logging import get_logger

logger = get_logger(__name__)

Base = declarative_base()


class Paper(Base):
    """SQLAlchemy model for paper metadata"""
    __tablename__ = "papers"
    
    # Primary key
    arxiv_id = Column(String(100), primary_key=True)
    
    # Paper metadata
    title = Column(String(500), nullable=False, index=True)
    authors = Column(Text, nullable=True)  # Comma-separated
    published_date = Column(String(50), nullable=True)
    
    # Storage and processing info
    pdf_path = Column(String(500), nullable=True)
    fingerprint = Column(String(500), nullable=False, index=True, unique=True)
    chunks_count = Column(Integer, default=0)
    
    # Processing status
    processed = Column(Boolean, default=False, index=True)
    indexed = Column(Boolean, default=False, index=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "arxiv_id": self.arxiv_id,
            "title": self.title,
            "authors": self.authors,
            "published_date": self.published_date,
            "pdf_path": self.pdf_path,
            "fingerprint": self.fingerprint,
            "chunks_count": self.chunks_count,
            "processed": self.processed,
            "indexed": self.indexed,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


class PostgresRepository:
    """
    PostgreSQL repository for paper metadata.
    Uses SQLAlchemy ORM with connection pooling and automatic migrations.
    """
    
    def __init__(self, database_url: Optional[str] = None):
        """
        Initialize PostgreSQL repository.
        
        Args:
            database_url: PostgreSQL connection URL. If not provided,
                         will try to get from DATABASE_URL environment variable
        """
        self.database_url = database_url or os.getenv(
            "DATABASE_URL",
            "postgresql://user:password@localhost:5432/research_agent"
        )
        
        # Create engine with connection pooling
        self.engine = create_engine(
            self.database_url,
            echo=os.getenv("SQL_DEBUG", "false").lower() == "true",
            pool_pre_ping=True,  # Verify connections before using
            pool_recycle=3600,  # Recycle connections after 1 hour
        )
        
        # Create session factory
        self.SessionLocal = scoped_session(sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        ))
        
        # Create tables if they don't exist
        self._init_db()
        
        logger.info(f"PostgreSQL repository initialized: {self.database_url}")
    
    def _init_db(self) -> None:
        """Initialize database tables"""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database tables created/verified")
        except SQLAlchemyError as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    @contextmanager
    def get_session(self) -> Session:
        """
        Context manager for database sessions.
        Ensures proper cleanup and error handling.
        
        Usage:
            with repo.get_session() as session:
                # Do work with session
        """
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database transaction error: {e}")
            raise
        finally:
            session.close()
    
    def insert_paper(
        self,
        arxiv_id: str,
        title: str,
        authors: Optional[str] = None,
        published_date: Optional[str] = None,
        pdf_path: Optional[str] = None,
        fingerprint: str = "",
        chunks_count: int = 0,
        processed: bool = False,
        indexed: bool = False,
    ) -> bool:
        """
        Insert a new paper into the database.
        
        Args:
            arxiv_id: arXiv paper identifier (unique)
            title: Paper title
            authors: Comma-separated author names
            published_date: Publication date
            pdf_path: Path to stored PDF
            fingerprint: Normalized title for deduplication
            chunks_count: Number of chunks created from this paper
            processed: Whether paper has been processed
            indexed: Whether paper has been indexed in vector store
            
        Returns:
            True if successful, False if paper already exists
        """
        try:
            with self.get_session() as session:
                # Check if paper already exists
                existing = session.query(Paper).filter_by(arxiv_id=arxiv_id).first()
                if existing:
                    logger.debug(f"Paper {arxiv_id} already exists")
                    return False
                
                # Create new paper
                paper = Paper(
                    arxiv_id=arxiv_id,
                    title=title,
                    authors=authors,
                    published_date=published_date,
                    pdf_path=pdf_path,
                    fingerprint=fingerprint,
                    chunks_count=chunks_count,
                    processed=processed,
                    indexed=indexed,
                )
                session.add(paper)
                logger.debug(f"Inserted paper: {arxiv_id}")
                return True
        except SQLAlchemyError as e:
            logger.error(f"Failed to insert paper {arxiv_id}: {e}")
            return False
    
    def get_paper_by_arxiv_id(self, arxiv_id: str) -> Optional[Dict[str, Any]]:
        """Get paper metadata by arXiv ID"""
        try:
            with self.get_session() as session:
                paper = session.query(Paper).filter_by(arxiv_id=arxiv_id).first()
                return paper.to_dict() if paper else None
        except SQLAlchemyError as e:
            logger.error(f"Failed to get paper {arxiv_id}: {e}")
            return None
    
    def paper_exists(self, arxiv_id: str) -> bool:
        """Check if paper already exists by arXiv ID"""
        try:
            with self.get_session() as session:
                exists = session.query(Paper).filter_by(arxiv_id=arxiv_id).first()
                return exists is not None
        except SQLAlchemyError as e:
            logger.error(f"Failed to check paper existence {arxiv_id}: {e}")
            return False
    
    def fingerprint_exists(self, fingerprint: str) -> bool:
        """Check if fingerprint already exists (for duplicate detection)"""
        try:
            with self.get_session() as session:
                exists = session.query(Paper).filter_by(fingerprint=fingerprint).first()
                return exists is not None
        except SQLAlchemyError as e:
            logger.error(f"Failed to check fingerprint: {e}")
            return False
    
    def get_all_paper_fingerprints(self) -> List[str]:
        """Get all title fingerprints for deduplication"""
        try:
            with self.get_session() as session:
                fingerprints = session.query(Paper.fingerprint).all()
                return [f[0] for f in fingerprints]
        except SQLAlchemyError as e:
            logger.error(f"Failed to get fingerprints: {e}")
            return []
    
    def get_all_arxiv_ids(self) -> List[str]:
        """Get all arXiv IDs of stored papers"""
        try:
            with self.get_session() as session:
                arxiv_ids = session.query(Paper.arxiv_id).all()
                return [id[0] for id in arxiv_ids]
        except SQLAlchemyError as e:
            logger.error(f"Failed to get arXiv IDs: {e}")
            return []
    
    def get_all_papers(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get all stored papers"""
        try:
            with self.get_session() as session:
                query = session.query(Paper).order_by(Paper.created_at.desc())
                if limit:
                    query = query.limit(limit)
                papers = query.all()
                return [p.to_dict() for p in papers]
        except SQLAlchemyError as e:
            logger.error(f"Failed to get all papers: {e}")
            return []
    
    def get_unprocessed_papers(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get papers that haven't been processed yet"""
        try:
            with self.get_session() as session:
                papers = (
                    session.query(Paper)
                    .filter_by(processed=False)
                    .order_by(Paper.created_at.asc())
                    .limit(limit)
                    .all()
                )
                return [p.to_dict() for p in papers]
        except SQLAlchemyError as e:
            logger.error(f"Failed to get unprocessed papers: {e}")
            return []
    
    def get_unindexed_papers(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get papers that haven't been indexed in vector store"""
        try:
            with self.get_session() as session:
                papers = (
                    session.query(Paper)
                    .filter_by(indexed=False)
                    .order_by(Paper.created_at.asc())
                    .limit(limit)
                    .all()
                )
                return [p.to_dict() for p in papers]
        except SQLAlchemyError as e:
            logger.error(f"Failed to get unindexed papers: {e}")
            return []
    
    def mark_processed(self, arxiv_id: str) -> bool:
        """Mark a paper as processed"""
        try:
            with self.get_session() as session:
                paper = session.query(Paper).filter_by(arxiv_id=arxiv_id).first()
                if paper:
                    paper.processed = True
                    paper.updated_at = datetime.utcnow()
                    logger.debug(f"Marked {arxiv_id} as processed")
                    return True
                return False
        except SQLAlchemyError as e:
            logger.error(f"Failed to mark {arxiv_id} as processed: {e}")
            return False
    
    def mark_indexed(self, arxiv_id: str) -> bool:
        """Mark a paper as indexed in vector store"""
        try:
            with self.get_session() as session:
                paper = session.query(Paper).filter_by(arxiv_id=arxiv_id).first()
                if paper:
                    paper.indexed = True
                    paper.updated_at = datetime.utcnow()
                    logger.debug(f"Marked {arxiv_id} as indexed")
                    return True
                return False
        except SQLAlchemyError as e:
            logger.error(f"Failed to mark {arxiv_id} as indexed: {e}")
            return False
    
    def update_chunks_count(self, arxiv_id: str, chunks_count: int) -> bool:
        """Update the number of chunks for a paper"""
        try:
            with self.get_session() as session:
                paper = session.query(Paper).filter_by(arxiv_id=arxiv_id).first()
                if paper:
                    paper.chunks_count = chunks_count
                    paper.updated_at = datetime.utcnow()
                    return True
                return False
        except SQLAlchemyError as e:
            logger.error(f"Failed to update chunks count: {e}")
            return False
    
    def get_paper_count(self) -> int:
        """Get total number of papers"""
        try:
            with self.get_session() as session:
                count = session.query(func.count(Paper.arxiv_id)).scalar()
                return count or 0
        except SQLAlchemyError as e:
            logger.error(f"Failed to get paper count: {e}")
            return 0
    
    def get_processed_count(self) -> int:
        """Get number of processed papers"""
        try:
            with self.get_session() as session:
                count = session.query(func.count(Paper.arxiv_id)).filter_by(
                    processed=True
                ).scalar()
                return count or 0
        except SQLAlchemyError as e:
            logger.error(f"Failed to get processed count: {e}")
            return 0
    
    def get_indexed_count(self) -> int:
        """Get number of indexed papers"""
        try:
            with self.get_session() as session:
                count = session.query(func.count(Paper.arxiv_id)).filter_by(
                    indexed=True
                ).scalar()
                return count or 0
        except SQLAlchemyError as e:
            logger.error(f"Failed to get indexed count: {e}")
            return 0
    
    def search_papers(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Search papers by title or authors.
        
        Args:
            query: Search query string
            limit: Maximum number of results
            
        Returns:
            List of matching papers
        """
        try:
            with self.get_session() as session:
                query_text = f"%{query}%"
                papers = (
                    session.query(Paper)
                    .filter(
                        (Paper.title.ilike(query_text)) |
                        (Paper.authors.ilike(query_text))
                    )
                    .order_by(Paper.created_at.desc())
                    .limit(limit)
                    .all()
                )
                return [p.to_dict() for p in papers]
        except SQLAlchemyError as e:
            logger.error(f"Failed to search papers: {e}")
            return []
    
    def delete_paper(self, arxiv_id: str) -> bool:
        """Delete a paper from the database"""
        try:
            with self.get_session() as session:
                paper = session.query(Paper).filter_by(arxiv_id=arxiv_id).first()
                if paper:
                    session.delete(paper)
                    logger.debug(f"Deleted paper: {arxiv_id}")
                    return True
                return False
        except SQLAlchemyError as e:
            logger.error(f"Failed to delete paper {arxiv_id}: {e}")
            return False
    
    def close(self) -> None:
        """Close database connection"""
        try:
            self.SessionLocal.remove()
            self.engine.dispose()
            logger.info("Database connection closed")
        except Exception as e:
            logger.error(f"Failed to close database: {e}")


# Global repository instance
_repository: Optional[PostgresRepository] = None


def get_repository(database_url: Optional[str] = None) -> PostgresRepository:
    """Get or create the global PostgreSQL repository instance"""
    global _repository
    if _repository is None:
        _repository = PostgresRepository(database_url)
    return _repository
