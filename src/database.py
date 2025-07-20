"""
Database setup and management for CGAL GitHub Crawler.
"""

import sqlite3
import logging
import os
from typing import Optional, List, Dict, Any
from datetime import datetime

logger = logging.getLogger('cgal_crawler.database')

class DatabaseManager:
    """Manages SQLite database operations for the CGAL crawler."""

    def __init__(self, db_path: str):
        """Initialize database manager with database path."""
        self.db_path = db_path
        self.ensure_directory_exists()

    def ensure_directory_exists(self):
        """Ensure the database directory exists."""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

    def initialize_database(self):
        """Initialize the database with required tables."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Create repositories table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS repositories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    full_name TEXT UNIQUE NOT NULL,
                    description TEXT,
                    html_url TEXT NOT NULL,
                    clone_url TEXT,
                    language TEXT,
                    stars INTEGER DEFAULT 0,
                    forks INTEGER DEFAULT 0,
                    size INTEGER DEFAULT 0,
                    created_at TEXT,
                    updated_at TEXT,
                    pushed_at TEXT,
                    owner_login TEXT,
                    owner_type TEXT,
                    crawled_at TEXT,
                    cgal_files_count INTEGER DEFAULT 0,
                    cgal_patterns_found TEXT
                )
            """)

            # Create files table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    repository_id INTEGER,
                    file_path TEXT NOT NULL,
                    file_name TEXT NOT NULL,
                    file_size INTEGER,
                    file_url TEXT,
                    download_url TEXT,
                    sha TEXT,
                    content TEXT,
                    cgal_headers TEXT,
                    cgal_patterns TEXT,
                    pattern_count INTEGER DEFAULT 0,
                    analyzed_at TEXT,
                    FOREIGN KEY (repository_id) REFERENCES repositories (id)
                )
            """)

            # Create search_queries table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS search_queries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    query TEXT NOT NULL,
                    total_count INTEGER,
                    processed_count INTEGER DEFAULT 0,
                    executed_at TEXT,
                    status TEXT DEFAULT 'pending'
                )
            """)

            # Create crawler_stats table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS crawler_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT,
                    repositories_found INTEGER DEFAULT 0,
                    files_analyzed INTEGER DEFAULT 0,
                    cgal_files_found INTEGER DEFAULT 0,
                    start_time TEXT,
                    end_time TEXT,
                    duration_seconds INTEGER,
                    status TEXT DEFAULT 'running'
                )
            """)

            conn.commit()
            logger.info("Database initialized successfully")

    def insert_repository(self, repo_data: Dict[str, Any]) -> int:
        """Insert repository data and return the repository ID."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute("""
                INSERT OR REPLACE INTO repositories (
                    name, full_name, description, html_url, clone_url,
                    language, stars, forks, size, created_at, updated_at,
                    pushed_at, owner_login, owner_type, crawled_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                repo_data.get('name', ''),
                repo_data.get('full_name', ''),
                repo_data.get('description', ''),
                repo_data.get('html_url', ''),
                repo_data.get('clone_url', ''),
                repo_data.get('language', ''),
                repo_data.get('stargazers_count', 0),
                repo_data.get('forks_count', 0),
                repo_data.get('size', 0),
                repo_data.get('created_at', ''),
                repo_data.get('updated_at', ''),
                repo_data.get('pushed_at', ''),
                repo_data.get('owner', {}).get('login', ''),
                repo_data.get('owner', {}).get('type', ''),
                datetime.now().isoformat()
            ))

            return cursor.lastrowid

    def insert_file(self, file_data: Dict[str, Any], repository_id: int) -> int:
        """Insert file data and return the file ID."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute("""
                INSERT OR REPLACE INTO files (
                    repository_id, file_path, file_name, file_size,
                    file_url, download_url, sha, content, cgal_headers,
                    cgal_patterns, pattern_count, analyzed_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                repository_id,
                file_data.get('path', ''),
                file_data.get('name', ''),
                file_data.get('size', 0),
                file_data.get('html_url', ''),
                file_data.get('download_url', ''),
                file_data.get('sha', ''),
                file_data.get('content', ''),
                file_data.get('cgal_headers', ''),
                file_data.get('cgal_patterns', ''),
                file_data.get('pattern_count', 0),
                datetime.now().isoformat()
            ))

            return cursor.lastrowid

    def update_repository_cgal_stats(self, repo_id: int, files_count: int, patterns: str):
        """Update repository with CGAL statistics."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE repositories 
                SET cgal_files_count = ?, cgal_patterns_found = ?
                WHERE id = ?
            """, (files_count, patterns, repo_id))

    def get_repository_by_full_name(self, full_name: str) -> Optional[Dict[str, Any]]:
        """Get repository by full name."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM repositories WHERE full_name = ?", (full_name,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_all_repositories(self) -> List[Dict[str, Any]]:
        """Get all repositories."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM repositories ORDER BY stars DESC")
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def get_files_by_repository(self, repo_id: int) -> List[Dict[str, Any]]:
        """Get all files for a repository."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM files WHERE repository_id = ?", (repo_id,))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def get_statistics(self) -> Dict[str, Any]:
        """Get crawler statistics."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Get repository count
            cursor.execute("SELECT COUNT(*) FROM repositories")
            repo_count = cursor.fetchone()[0]

            # Get file count
            cursor.execute("SELECT COUNT(*) FROM files")
            file_count = cursor.fetchone()[0]

            # Get CGAL file count
            cursor.execute("SELECT COUNT(*) FROM files WHERE pattern_count > 0")
            cgal_file_count = cursor.fetchone()[0]

            # Get top languages
            cursor.execute("""
                SELECT language, COUNT(*) as count 
                FROM repositories 
                WHERE language IS NOT NULL 
                GROUP BY language 
                ORDER BY count DESC 
                LIMIT 10
            """)
            languages = cursor.fetchall()

            return {
                'total_repositories': repo_count,
                'total_files': file_count,
                'cgal_files': cgal_file_count,
                'top_languages': languages
            }
