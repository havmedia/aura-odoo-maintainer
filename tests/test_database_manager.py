import pytest
from unittest.mock import Mock, patch
from src.DatabaseManager import DatabaseManager


@pytest.fixture
def db_manager():
    return DatabaseManager(
        host="test_host",
        port=5432,
        user="test_user",
        password="test_pass",
        database="test_db"
    )


@pytest.fixture
def mock_connection():
    with patch('psycopg2.connect') as mock_connect:
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        yield mock_conn


def test_execute_sql_select(db_manager, mock_connection):
    # Setup mock cursor with sample data
    mock_cursor = mock_connection.cursor.return_value
    mock_cursor.description = [Mock()]  # Simulate SELECT query
    mock_cursor.fetchall.return_value = [(1, "test"), (2, "test2")]

    # Execute a SELECT query
    result = db_manager.execute_sql("SELECT * FROM test_table WHERE id = %s", (1,))

    # Verify the query was executed correctly
    mock_cursor.execute.assert_called_once_with("SELECT * FROM test_table WHERE id = %s", (1,))
    assert result == [(1, "test"), (2, "test2")]


def test_execute_sql_insert(db_manager, mock_connection):
    # Setup mock cursor for INSERT
    mock_cursor = mock_connection.cursor.return_value
    mock_cursor.description = None  # Simulate non-SELECT query

    # Execute an INSERT query
    result = db_manager.execute_sql(
        "INSERT INTO test_table (name) VALUES (%s)",
        ("test_name",)
    )

    # Verify the query was executed and returns empty list for non-SELECT
    mock_cursor.execute.assert_called_once_with(
        "INSERT INTO test_table (name) VALUES (%s)",
        ("test_name",)
    )
    assert result == []


def test_execute_sql_no_params(db_manager, mock_connection):
    # Setup mock cursor
    mock_cursor = mock_connection.cursor.return_value
    mock_cursor.description = [Mock()]
    mock_cursor.fetchall.return_value = [(1,)]

    # Execute query without parameters
    result = db_manager.execute_sql("SELECT COUNT(*) FROM test_table")

    # Verify execution
    mock_cursor.execute.assert_called_once_with("SELECT COUNT(*) FROM test_table", None)
    assert result == [(1,)]


def test_connection_parameters(db_manager, mock_connection):
    # Execute any query to trigger connection
    db_manager.execute_sql("SELECT 1")

    # Verify connection was made with correct parameters
    import psycopg2
    psycopg2.connect.assert_called_once_with(
        host="test_host",
        port=5432,
        user="test_user",
        password="test_pass",
        database="test_db"
    )


def test_connection_cleanup(db_manager, mock_connection):
    # Setup mocks
    mock_cursor = mock_connection.cursor.return_value

    # Execute query
    db_manager.execute_sql("SELECT 1")

    # Verify cleanup
    mock_cursor.close.assert_called_once()
    mock_connection.close.assert_called_once()


def test_execute_sql_error_handling(db_manager, mock_connection):
    # Setup mock to raise exception
    mock_cursor = mock_connection.cursor.return_value
    mock_cursor.execute.side_effect = Exception("Database error")

    # Verify exception handling
    with pytest.raises(Exception):
        db_manager.execute_sql("SELECT * FROM non_existent_table")

    # Verify cleanup still occurs
    mock_cursor.close.assert_called_once()
    mock_connection.close.assert_called_once()


@patch('subprocess.run')
def test_create_backup(mock_run, db_manager):
    # Test create_backup with default extension
    output_file = "/path/to/backup"
    with patch('src.DatabaseManager.datetime') as mock_datetime:
        mock_datetime.now.return_value.strftime.return_value = "20240101_120000"
        result = db_manager.create_backup(output_file)

    expected_file = f"{output_file}_20240101_120000.sql"
    assert result == expected_file

    mock_run.assert_called_once()
    args, kwargs = mock_run.call_args
    cmd = args[0]
    assert cmd == [
        'pg_dump',
        '--host=test_host',
        '--port=5432',
        '--username=test_user',
        '--dbname=test_db',
        '--format=p',
        f'--file={expected_file}'
    ]
    assert kwargs['env']['PGPASSWORD'] == 'test_pass'
    assert kwargs['check'] is True


@patch('subprocess.run')
def test_restore_backup(mock_run, db_manager):
    backup_file = "/path/to/backup.sql"
    db_manager.restore_backup(backup_file)

    mock_run.assert_called_once()
    args, kwargs = mock_run.call_args
    cmd = args[0]
    assert cmd == [
        'psql',
        '--host=test_host',
        '--port=5432',
        '--username=test_user',
        '--dbname=test_db',
        '-f', backup_file
    ]
    assert kwargs['env']['PGPASSWORD'] == 'test_pass'
    assert kwargs['check'] is True


def test_duplicate_database(db_manager, mock_connection):
    mock_cursor = mock_connection.cursor.return_value

    db_manager.duplicate_database('source_db', 'target_db')

    # Verify all expected SQL commands were executed
    expected_calls = [
        ("""
            SELECT pg_terminate_backend(pid) 
            FROM pg_stat_activity 
            WHERE datname = %s AND pid != pg_backend_pid()
        """, ('target_db',)),
        ("DROP DATABASE IF EXISTS target_db", None),
        ("CREATE DATABASE target_db WITH TEMPLATE source_db", None)
    ]

    assert mock_cursor.execute.call_count == 3
    for (expected_sql, expected_params), call in zip(expected_calls, mock_cursor.execute.call_args_list):
        actual_sql = call[0][0]  # First arg of the first tuple
        actual_params = call[0][1] if len(call[0]) > 1 else None  # Second arg of the first tuple if it exists
        assert actual_sql.strip() == expected_sql.strip()
        assert actual_params == expected_params


def test_create_user(db_manager, mock_connection):
    mock_cursor = mock_connection.cursor.return_value

    # Test creating regular user
    db_manager.create_user('new_user', 'password123')
    mock_cursor.execute.assert_called_with("CREATE USER new_user WITH PASSWORD '%s' CREATEDB", ('password123',))

    # Test creating superuser
    mock_cursor.reset_mock()
    db_manager.create_user('new_superuser', 'password456', superuser=True)
    assert mock_cursor.execute.call_count == 2
    mock_cursor.execute.assert_any_call("CREATE USER new_superuser WITH PASSWORD '%s' CREATEDB", ('password456',))
    mock_cursor.execute.assert_any_call("ALTER USER new_superuser WITH SUPERUSER")


def test_list_databases(db_manager, mock_connection):
    mock_cursor = mock_connection.cursor.return_value
    mock_cursor.description = [Mock()]
    mock_cursor.fetchall.return_value = [('db1',), ('db2',), ('db3',)]

    result = db_manager.list_databases()

    mock_cursor.execute.assert_called_once_with(
        "SELECT datname FROM pg_database WHERE datistemplate = false",
        None
    )
    assert result == ['db1', 'db2', 'db3']
