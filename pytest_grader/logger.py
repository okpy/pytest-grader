"""
Logging that tracks a student's progress through an assignment.
"""

from abc import ABC, abstractmethod
import sqlite3
import hashlib
import os
from datetime import datetime


class ProgressLogger(ABC):
    """Logs progress through an assignment."""

    @abstractmethod
    def snapshot(self):
        """Store assignment code used for this test."""

    @abstractmethod
    def test_case(self, name, passed: bool, response: str | None = None):
        """Store the AI response and result of a test case."""

    @abstractmethod
    def unlock_attempt(self, name, output_number, guess, success: bool, response: str | None = None):
        """Store the AI response and result of an attempt to unlock a test case."""


class SQLLogger(ProgressLogger):
    def __init__(self, db: str, conf: dict[str, str]):
        self.db_path = db
        self.conf = conf
        self.current_snapshot = None
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        self._setup_db()

    def _setup_db(self):
        """Set up the database tables."""
        # Files table to store file snapshots
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                content TEXT NOT NULL,
                sha1_hash TEXT NOT NULL UNIQUE
            )
        ''')

        # Snapshots table to track when snapshots were taken
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Snapshot files table to track which files were included in each snapshot
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS snapshot_files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                snapshot_id INTEGER,
                filename TEXT NOT NULL,
                sha1_hash TEXT NOT NULL,
                FOREIGN KEY (snapshot_id) REFERENCES snapshots (id)
            )
        ''')

        # Test cases table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS test_cases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                snapshot_id INTEGER,
                name TEXT NOT NULL,
                passed BOOLEAN NOT NULL,
                response TEXT,
                FOREIGN KEY (snapshot_id) REFERENCES snapshots (id)
            )
        ''')

        # Unlock attempts table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS unlock_attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                snapshot_id INTEGER,
                name TEXT NOT NULL,
                guess TEXT NOT NULL,
                success BOOLEAN NOT NULL,
                response TEXT,
                FOREIGN KEY (snapshot_id) REFERENCES snapshots (id)
            )
        ''')

        self.conn.commit()

    def _execute_and_commit(self, query, params=None):
        """Execute a query and commit the transaction."""
        if params:
            self.cursor.execute(query, params)
        else:
            self.cursor.execute(query)
        self.conn.commit()

    def snapshot(self):
        """Store assignment code used for this test."""
        # Create a new snapshot record
        self._execute_and_commit('INSERT INTO snapshots DEFAULT VALUES')
        snapshot_id = self.cursor.lastrowid
        self.current_snapshot = snapshot_id

        # Process each included file
        for filename in self.conf.get('included_files', []):
            if os.path.exists(filename):
                with open(filename, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Calculate SHA-1 hash
                sha1_hash = hashlib.sha1(content.encode('utf-8')).hexdigest()

                # Check if this hash already exists in the database
                self.cursor.execute('SELECT id FROM files WHERE sha1_hash = ?', (sha1_hash,))
                existing = self.cursor.fetchone()

                if not existing:
                    # Store the file content if hash doesn't exist
                    self._execute_and_commit('''
                        INSERT INTO files (filename, content, sha1_hash)
                        VALUES (?, ?, ?)
                    ''', (filename, content, sha1_hash))

                # Always record which files were part of this snapshot
                self._execute_and_commit('''
                    INSERT INTO snapshot_files (snapshot_id, filename, sha1_hash)
                    VALUES (?, ?, ?)
                ''', (snapshot_id, filename, sha1_hash))

    def test_case(self, name, passed: bool, response: str | None = None):
        """Store the AI response and result of a test case."""
        self._execute_and_commit('''
            INSERT INTO test_cases (snapshot_id, name, passed, response)
            VALUES (?, ?, ?, ?)
        ''', (self.current_snapshot, name, passed, response))

    def unlock_attempt(self, name, output_number, guess, success: bool, response: str | None = None):
        """Store the AI response and result of an attempt to unlock a test case."""
        self._execute_and_commit('''
            INSERT INTO unlock_attempts (snapshot_id, name, guess, success, response)
            VALUES (?, ?, ?, ?, ?)
        ''', (self.current_snapshot, f"{name}[{output_number}]", guess, success, response))