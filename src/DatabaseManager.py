import psycopg2
from typing import Optional, List, Tuple, Any
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import os
import subprocess
from datetime import datetime


class DatabaseManager:
    """Manager class for PostgreSQL database operations"""

    def __init__(self, host: str = "localhost",
                 port: int = 5432,
                 user: str = "postgres",
                 password: str = None,
                 database: str = "postgres"):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database

    def _get_connection(self, database: Optional[str] = None) -> psycopg2.extensions.connection:
        """Create a database connection"""
        db = database or self.database
        conn = psycopg2.connect(
            host=self.host,
            port=self.port,
            user=self.user,
            password=self.password,
            database=db
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        return conn

    def execute_sql(self, sql: str, params: Tuple[Any, ...] = None) -> List[Tuple]:
        """
        Execute a SQL query and return results
        
        :param sql: SQL query to execute
        :param params: Query parameters for parameterized queries
        :return: List of query results
        """
        conn = self._get_connection()
        cur = conn.cursor()

        try:
            cur.execute(sql, params)
            if cur.description:  # If the query returns data
                results = cur.fetchall()
            else:
                results = []
        finally:
            cur.close()
            conn.close()

        return results

    def create_backup(self, output_file: str) -> str:
        """
        Create a backup of the database
        
        :param output_file: Path where the backup should be saved
        :return: Path to the backup file
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        if not output_file.endswith('.sql'):
            output_file = f"{output_file}_{timestamp}.sql"

        cmd = [
            'pg_dump',
            f'--host={self.host}',
            f'--port={self.port}',
            f'--username={self.user}',
            f'--dbname={self.database}',
            '--format=p',
            f'--file={output_file}'
        ]

        env = os.environ.copy()
        env['PGPASSWORD'] = self.password

        subprocess.run(cmd, env=env, check=True)
        return output_file

    def restore_backup(self, backup_file: str) -> None:
        """
        Restore a database from a backup file
        
        :param backup_file: Path to the backup file
        """
        cmd = [
            'psql',
            f'--host={self.host}',
            f'--port={self.port}',
            f'--username={self.user}',
            f'--dbname={self.database}',
            '-f', backup_file
        ]

        env = os.environ.copy()
        env['PGPASSWORD'] = self.password

        subprocess.run(cmd, env=env, check=True)

    def duplicate_database(self, source_db: str, target_db: str) -> None:
        """
        Create a copy of a database
        
        :param source_db: Name of the source database
        :param target_db: Name of the target database
        """
        conn = self._get_connection('postgres')
        cur = conn.cursor()

        # Terminate existing connections to the target database
        cur.execute(f"""
            SELECT pg_terminate_backend(pid) 
            FROM pg_stat_activity 
            WHERE datname = %s AND pid != pg_backend_pid()
        """, (target_db,))

        # Drop target database if exists
        cur.execute(f"DROP DATABASE IF EXISTS {target_db}")

        # Create new database as a copy
        cur.execute(f"CREATE DATABASE {target_db} WITH TEMPLATE {source_db}")

        cur.close()
        conn.close()

    def create_user(self, username: str, password: str, superuser: bool = False) -> None:
        """
        Create a new database user
        
        :param username: Username for the new user
        :param password: Password for the new user
        :param superuser: Whether to grant superuser privileges
        """
        conn = self._get_connection()
        cur = conn.cursor()

        cur.execute(f"CREATE USER {username} WITH PASSWORD %s", (password,))
        if superuser:
            cur.execute(f"ALTER USER {username} WITH SUPERUSER")

        cur.close()
        conn.close()

    def list_databases(self) -> List[str]:
        """
        List all databases in the PostgreSQL instance
        
        :return: List of database names
        """
        return [row[0] for row in self.execute_sql("SELECT datname FROM pg_database WHERE datistemplate = false")]
