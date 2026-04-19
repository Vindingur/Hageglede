"""
SQLite data loader for Hageglede data pipeline.
Handles database operations with upsert logic.
"""
import sqlite3
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import json
from datetime import datetime

logger = logging.getLogger(__name__)


class SQLLiteLoader:
    """SQLite database loader with upsert capabilities."""
    
    def __init__(self, db_path: str):
        """
        Initialize SQLite loader.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_schema()
    
    def _ensure_schema(self) -> None:
        """Ensure database schema exists."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sources (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    url TEXT,
                    last_fetched TIMESTAMP,
                    data_quality_score REAL,
                    metadata_json TEXT
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS articles (
                    id TEXT PRIMARY KEY,
                    source_id TEXT NOT NULL,
                    url TEXT NOT NULL,
                    title TEXT NOT NULL,
                    content TEXT,
                    summary TEXT,
                    published_date TIMESTAMP,
                    fetched_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    category TEXT,
                    keywords_json TEXT,
                    sentiment_score REAL,
                    engagement_score REAL,
                    metadata_json TEXT,
                    FOREIGN KEY (source_id) REFERENCES sources (id)
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS entities (
                    id TEXT PRIMARY KEY,
                    entity_type TEXT NOT NULL,
                    name TEXT NOT NULL,
                    context TEXT,
                    source_article_id TEXT,
                    confidence_score REAL,
                    extracted_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata_json TEXT,
                    FOREIGN KEY (source_article_id) REFERENCES articles (id)
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS pipeline_runs (
                    id TEXT PRIMARY KEY,
                    run_type TEXT NOT NULL,
                    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    end_time TIMESTAMP,
                    status TEXT NOT NULL,
                    sources_processed INTEGER DEFAULT 0,
                    articles_processed INTEGER DEFAULT 0,
                    errors_encountered INTEGER DEFAULT 0,
                    metadata_json TEXT
                )
            """)
            
            # Create indexes for better query performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_articles_source ON articles(source_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_articles_date ON articles(published_date)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_entities_article ON entities(source_article_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_pipeline_status ON pipeline_runs(status)")
            
            conn.commit()
    
    def upsert_source(self, source_data: Dict[str, Any]) -> bool:
        """
        Insert or update a source record.
        
        Args:
            source_data: Dictionary containing source data
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO sources 
                    (id, name, url, last_fetched, data_quality_score, metadata_json)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    source_data.get("id"),
                    source_data.get("name"),
                    source_data.get("url"),
                    source_data.get("last_fetched"),
                    source_data.get("data_quality_score"),
                    json.dumps(source_data.get("metadata", {}))
                ))
                conn.commit()
                logger.info(f"Upserted source: {source_data.get('name')}")
                return True
        except Exception as e:
            logger.error(f"Failed to upsert source: {e}")
            return False
    
    def upsert_article(self, article_data: Dict[str, Any]) -> bool:
        """
        Insert or update an article record.
        
        Args:
            article_data: Dictionary containing article data
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO articles 
                    (id, source_id, url, title, content, summary, published_date, 
                     category, keywords_json, sentiment_score, engagement_score, metadata_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    article_data.get("id"),
                    article_data.get("source_id"),
                    article_data.get("url"),
                    article_data.get("title"),
                    article_data.get("content"),
                    article_data.get("summary"),
                    article_data.get("published_date"),
                    article_data.get("category"),
                    json.dumps(article_data.get("keywords", [])),
                    article_data.get("sentiment_score"),
                    article_data.get("engagement_score"),
                    json.dumps(article_data.get("metadata", {}))
                ))
                conn.commit()
                logger.info(f"Upserted article: {article_data.get('title')}")
                return True
        except Exception as e:
            logger.error(f"Failed to upsert article: {e}")
            return False
    
    def upsert_entity(self, entity_data: Dict[str, Any]) -> bool:
        """
        Insert or update an entity record.
        
        Args:
            entity_data: Dictionary containing entity data
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO entities 
                    (id, entity_type, name, context, source_article_id, 
                     confidence_score, metadata_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    entity_data.get("id"),
                    entity_data.get("entity_type"),
                    entity_data.get("name"),
                    entity_data.get("context"),
                    entity_data.get("source_article_id"),
                    entity_data.get("confidence_score"),
                    json.dumps(entity_data.get("metadata", {}))
                ))
                conn.commit()
                logger.info(f"Upserted entity: {entity_data.get('name')}")
                return True
        except Exception as e:
            logger.error(f"Failed to upsert entity: {e}")
            return False
    
    def start_pipeline_run(self, run_id: str, run_type: str) -> bool:
        """
        Record the start of a pipeline run.
        
        Args:
            run_id: Unique identifier for the run
            run_type: Type of run (e.g., 'full', 'incremental')
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO pipeline_runs 
                    (id, run_type, status, start_time)
                    VALUES (?, ?, ?, ?)
                """, (run_id, run_type, "running", datetime.now().isoformat()))
                conn.commit()
                logger.info(f"Started pipeline run: {run_id}")
                return True
        except Exception as e:
            logger.error(f"Failed to start pipeline run: {e}")
            return False
    
    def update_pipeline_run(self, run_id: str, **updates) -> bool:
        """
        Update pipeline run status and statistics.
        
        Args:
            run_id: ID of the run to update
            **updates: Fields to update and their values
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Build dynamic update query
                set_clauses = []
                values = []
                
                for key, value in updates.items():
                    if key == "metadata_json" and isinstance(value, dict):
                        set_clauses.append(f"{key} = ?")
                        values.append(json.dumps(value))
                    elif key == "end_time":
                        set_clauses.append(f"{key} = ?")
                        values.append(datetime.now().isoformat())
                    else:
                        set_clauses.append(f"{key} = ?")
                        values.append(value)
                
                values.append(run_id)
                query = f"""
                    UPDATE pipeline_runs 
                    SET {', '.join(set_clauses)}
                    WHERE id = ?
                """
                conn.execute(query, values)
                conn.commit()
                logger.info(f"Updated pipeline run: {run_id}")
                return True
        except Exception as e:
            logger.error(f"Failed to update pipeline run: {e}")
            return False
    
    def load_batch(self, batch_type: str, data: List[Dict[str, Any]]) -> Tuple[int, int]:
        """
        Load a batch of data records.
        
        Args:
            batch_type: Type of data ('sources', 'articles', 'entities')
            data: List of data dictionaries
            
        Returns:
            Tuple of (success_count, failure_count)
        """
        success_count = 0
        failure_count = 0
        
        for item in data:
            if batch_type == "sources":
                success = self.upsert_source(item)
            elif batch_type == "articles":
                success = self.upsert_article(item)
            elif batch_type == "entities":
                success = self.upsert_entity(item)
            else:
                logger.error(f"Unknown batch type: {batch_type}")
                success = False
            
            if success:
                success_count += 1
            else:
                failure_count += 1
        
        logger.info(f"Loaded batch of {batch_type}: {success_count} succeeded, {failure_count} failed")
        return success_count, failure_count
    
    def get_connection(self) -> sqlite3.Connection:
        """Get a database connection."""
        return sqlite3.connect(self.db_path)


def create_loader(db_path: Optional[str] = None) -> SQLLiteLoader:
    """
    Factory function to create a loader instance.
    
    Args:
        db_path: Optional database path, defaults to config value
        
    Returns:
        SQLLiteLoader instance
    """
    if db_path is None:
        from scripts.config import Config
        config = Config()
        db_path = config.database_path
    
    return SQLLiteLoader(db_path)