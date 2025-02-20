from unittest.mock import Mock, patch
from click.testing import CliRunner
import pytest
from src.main import cli
from src.ComposeManager import ComposeManager
from src.Services import PostgresService, WhoamiService
from src.exceptions import SetupAlreadyExistsError

def test_init_command_default_values():
    runner = CliRunner()
    
    with patch('src.main.ComposeManager') as mock_manager:
        # Setup mocks
        manager_instance = Mock()
        manager_instance._config = {'services': {}}  # Empty services
        mock_manager.return_value = manager_instance
        
        # Run command with default values
        result = runner.invoke(cli, ['init'])
        
        # Verify command succeeded
        assert result.exit_code == 0
        
        # Verify ComposeManager was initialized correctly
        mock_manager.assert_called_once_with('docker-compose.yml')
        
        # Verify services were created with correct parameters
        calls = manager_instance.add_service.call_args_list
        assert len(calls) == 2
        
        # Verify postgres service
        postgres_service = calls[0][0][0]
        assert isinstance(postgres_service, PostgresService)
        assert postgres_service.name == 'postgres'
        assert postgres_service._config['environment']['POSTGRES_PASSWORD'] == 'postgres'
        assert postgres_service._config['ports'] == ['5432:5432']
        
        # Verify whoami service
        whoami_service = calls[1][0][0]
        assert isinstance(whoami_service, WhoamiService)
        assert whoami_service.name == 'whoami'

def test_init_command_with_existing_services():
    runner = CliRunner()
    
    with patch('src.main.ComposeManager') as mock_manager:
        # Setup mocks with existing services
        manager_instance = Mock()
        manager_instance._config = {'services': {'existing': {}}}
        mock_manager.return_value = manager_instance
        
        # Run command
        result = runner.invoke(cli, ['init'])
        
        # Verify command failed with correct error
        assert result.exit_code != 0
        assert isinstance(result.exception, SetupAlreadyExistsError)
        
        # Verify no services were added
        manager_instance.add_service.assert_not_called()

def test_init_command_custom_values():
    runner = CliRunner()
    
    with patch('src.main.ComposeManager') as mock_manager:
        # Setup mocks
        manager_instance = Mock()
        manager_instance._config = {'services': {}}  # Empty services
        mock_manager.return_value = manager_instance
        
        # Run command with custom values
        result = runner.invoke(cli, [
            'init',
            '--db-name', 'mydb',
            '--db-password', 'secret',
            '--db-port', '5433'
        ])
        
        # Verify command succeeded
        assert result.exit_code == 0
        
        # Verify ComposeManager was initialized correctly
        mock_manager.assert_called_once_with('docker-compose.yml')
        
        # Verify services were created with correct parameters
        calls = manager_instance.add_service.call_args_list
        assert len(calls) == 2
        
        # Verify postgres service with custom values
        postgres_service = calls[0][0][0]
        assert isinstance(postgres_service, PostgresService)
        assert postgres_service.name == 'mydb'
        assert postgres_service._config['environment']['POSTGRES_PASSWORD'] == 'secret'
        assert postgres_service._config['ports'] == ['5433:5432']
        
        # Verify whoami service
        whoami_service = calls[1][0][0]
        assert isinstance(whoami_service, WhoamiService)
        assert whoami_service.name == 'whoami'

def test_init_command_output():
    runner = CliRunner()
    
    with patch('src.main.ComposeManager') as mock_manager:
        # Setup mocks
        manager_instance = Mock()
        manager_instance._config = {'services': {}}  # Empty services
        mock_manager.return_value = manager_instance
        
        # Run command
        result = runner.invoke(cli, ['init', '--db-name', 'testdb'])
        
        # Verify output message
        assert "Created docker-compose.yml with testdb database and whoami service" in result.output 