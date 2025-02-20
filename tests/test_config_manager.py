from unittest.mock import mock_open, patch

import pytest
import yaml

from src.ConfigManager import ConfigManager
from src.configs.DatabaseConfig import DatabaseConfig
from src.configs.OdooConfig import OdooConfig


@pytest.fixture
def config_manager(tmp_path):
    """Fixture to create a temporary OdooConfigManager."""
    config_file = tmp_path / "setup.yml"
    manager = ConfigManager.create(version='15.0', hosts=['example1.com'], config_path=str(config_file),
                                   db_config=DatabaseConfig(name='postgres', password='secret', user='postgres'))
    return manager


def test_initialization(config_manager):
    """Test that the config manager initializes correctly."""
    assert config_manager.get_version() == '15.0'
    assert config_manager.get_hosts() == ['example1.com']


def test_add_host(config_manager):
    """Test adding a host to the configuration."""
    config_manager.add_host('example2.com')
    assert 'example2.com' in config_manager.get_hosts()
    assert len(config_manager.get_hosts()) == 2


def test_remove_host(config_manager):
    """Test removing a host from the configuration."""
    config_manager.add_host('example2.com')
    config_manager.remove_host('example2.com')
    assert 'example2.com' not in config_manager.get_hosts()


def test_remove_only_host(config_manager):
    """Test removing the only remaining host raises an error."""
    with pytest.raises(ValueError, match="Cannot remove the only remaining host."):
        config_manager.remove_host('example1.com')


def test_set_hosts(config_manager):
    """Test setting the list of hosts."""
    config_manager.set_hosts(['example3.com', 'example4.com'])
    assert config_manager.get_hosts() == ['example3.com', 'example4.com']


def test_list_hosts(config_manager):
    """Test listing hosts."""
    assert config_manager.list_hosts() == ['example1.com']
    config_manager.add_host('example2.com')
    assert config_manager.list_hosts() == ['example1.com', 'example2.com']


def test_set_hosts_empty_list_raises_value_error(config_manager):
    """Test that setting an empty list of hosts raises a ValueError."""
    with pytest.raises(ValueError, match="There must be at least one host."):
        config_manager.set_hosts([])


def test_validate_config_exists_raises_error(tmp_path):
    """Test that _validate_config_exists raises an error if config does not exist."""
    config_file = tmp_path / "nonexistent.yml"
    with pytest.raises(ValueError, match=f"{config_file} does not exist."):
        ConfigManager(config_path=str(config_file))


def test_create_raises_error_if_config_exists(tmp_path):
    """Test that create raises an error if config file already exists."""
    config_file = tmp_path / "setup.yml"
    config_file.touch()  # Create the file to simulate existing config
    with pytest.raises(ValueError, match=f"Config file {config_file} already exists."):
        ConfigManager.create(version='15.0', hosts=['example1.com'], config_path=str(config_file),
                             db_config=DatabaseConfig(name='postgres', password='secret', user='postgres'))


def test_get_odoos_empty(tmp_path):
    """Test get_odoos when no services exist"""
    # Create config file with no services
    config_file = tmp_path / "setup.yml"
    with open(config_file, 'w') as f:
        yaml.dump({'version': '1.0', 'hosts': ['localhost'], 'db': {'password': 'password', 'user': 'user', 'name': 'name'}, 'services': []}, f)

    manager = ConfigManager(str(config_file))
    odoos = manager.get_odoos()
    assert isinstance(odoos, list)
    assert len(odoos) == 0


def test_get_odoos(tmp_path, mocker):
    """Test get_odoos returns list of OdooConfig objects"""
    # Create mock OdooConfig
    service_dict = {'name': 'test-odoo', 'port': 8069}

    # Create config file with a service
    config_file = tmp_path / "setup.yml"
    with open(config_file, 'w') as f:
        yaml.dump({
            'version': '1.0',
            'hosts': ['localhost'],
            'db': {'password': 'password', 'user': 'user', 'name': 'name'},
            'services': [service_dict]
        }, f)

    # Mock OdooConfig.from_dict
    mock_odoo_config = mocker.Mock()
    mocker.patch('src.configs.OdooConfig.OdooConfig.from_dict',
                 return_value=mock_odoo_config)

    manager = ConfigManager(str(config_file))
    odoos = manager.get_odoos()

    assert len(odoos) == 1
    assert odoos[0] == mock_odoo_config
    OdooConfig.from_dict.assert_called_once_with(service_dict)


def test_add_odoo(tmp_path, mocker):
    """Test adding an Odoo service configuration"""
    # Create initial config file
    config_file = tmp_path / "setup.yml"
    with open(config_file, 'w') as f:
        yaml.dump({
            'version': '1.0',
            'hosts': ['localhost'],
            'db': {'password': 'password', 'user': 'user', 'name': 'name'},
            'services': []
        }, f)

    # Create mock OdooConfig
    mock_odoo = mocker.Mock()
    service_dict = {'name': 'test-odoo', 'port': 8069}
    mock_odoo.to_dict.return_value = service_dict

    manager = ConfigManager(str(config_file))
    manager.add_odoo(mock_odoo)

    # Verify config was updated and saved
    with open(config_file, 'r') as f:
        saved_config = yaml.safe_load(f)

    assert len(saved_config['services']) == 1
    assert saved_config['services'][0] == service_dict
    mock_odoo.to_dict.assert_called_once()


def test_add_odoo_multiple(tmp_path, mocker):
    """Test adding multiple Odoo service configurations"""
    # Create initial config file
    config_file = tmp_path / "setup.yml"
    with open(config_file, 'w') as f:
        yaml.dump({
            'version': '1.0',
            'hosts': ['localhost'],
            'db': {'password': 'password', 'user': 'user', 'name': 'name'},
            'services': []
        }, f)

    # Create mock OdooConfigs
    mock_odoo1 = mocker.Mock()
    mock_odoo1.to_dict.return_value = {'name': 'odoo1', 'port': 8069}

    mock_odoo2 = mocker.Mock()
    mock_odoo2.to_dict.return_value = {'name': 'odoo2', 'port': 8070}

    manager = ConfigManager(str(config_file))
    manager.add_odoo(mock_odoo1)
    manager.add_odoo(mock_odoo2)

    # Verify both services were added
    with open(config_file, 'r') as f:
        saved_config = yaml.safe_load(f)

    assert len(saved_config['services']) == 2
    assert saved_config['services'][0] == mock_odoo1.to_dict()
    assert saved_config['services'][1] == mock_odoo2.to_dict()

def test_add_odoo_multiple(tmp_path, mocker):
    """Test adding multiple Odoo service configurations"""
    # Create initial config file
    config_file = tmp_path / "setup.yml"
    with open(config_file, 'w') as f:
        yaml.dump({
            'version': '1.0',
            'hosts': ['localhost'],
            'db': {'password': 'password', 'user': 'user', 'name': 'name'},
            'services': []
        }, f)

    # Create mock OdooConfigs
    mock_odoo1 = mocker.Mock()
    mock_odoo1.to_dict.return_value = {'name': 'odoo1', 'port': 8069}

    mock_odoo2 = mocker.Mock()
    mock_odoo2.to_dict.return_value = {'name': 'odoo2', 'port': 8070}

    manager = ConfigManager(str(config_file))
    manager.add_odoo(mock_odoo1)
    manager.add_odoo(mock_odoo2)

    # Verify both services were added
    with open(config_file, 'r') as f:
        saved_config = yaml.safe_load(f)

    assert len(saved_config['services']) == 2
    assert saved_config['services'][0] == mock_odoo1.to_dict()
    assert saved_config['services'][1] == mock_odoo2.to_dict()


def test_get_db_config(tmp_path, mocker):
    """Test get_db_config returns DatabaseConfig object"""
    # Create initial config file
    config_file = tmp_path / "setup.yml"
    with open(config_file, 'w') as f:
        yaml.dump({
            'version': '1.0',
            'hosts': ['localhost'],
            'db': {'password': 'password', 'user': 'user', 'name': 'name'},
            'services': []
        }, f)

    manager = ConfigManager(str(config_file))
    db_config = manager.get_db()

    assert isinstance(db_config, DatabaseConfig)
    assert db_config.name == 'name'
    assert db_config.password == 'password'
    assert db_config.user == 'user'