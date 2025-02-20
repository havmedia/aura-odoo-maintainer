import subprocess
import yaml

import pytest

from src.ComposeManager import ComposeManager
from src.exceptions import DockerNotFoundError, DockerCommandExecutionError, ComposeFilePermissionError, \
    ServiceNotFoundError


# Fixture for the ComposeManager instance
@pytest.fixture
def compose_manager(tmp_path, mocker):
    # Create a dummy docker-compose.yml file in a temporary directory
    compose_file = tmp_path / "docker-compose.yml"
    compose_file.write_text("version: '3'")

    # Mock the version checks to simulate docker compose being available
    mock_run = mocker.patch("subprocess.run")
    mock_run.side_effect = [
        subprocess.CompletedProcess(args=[], returncode=0, stdout=""),  # docker compose succeeds
    ]

    return ComposeManager(str(compose_file))


@pytest.fixture
def legacy_compose_manager(tmp_path, mocker):
    # Create a dummy docker-compose.yml file in a temporary directory
    compose_file = tmp_path / "docker-compose.yml"
    compose_file.write_text("version: '3'")

    # Mock the version checks to simulate only docker-compose being available
    mock_run = mocker.patch("subprocess.run")
    mock_run.side_effect = [
        subprocess.CalledProcessError(1, "docker compose"),  # docker compose fails
        subprocess.CompletedProcess(args=[], returncode=0, stdout=""),  # docker-compose succeeds
    ]

    return ComposeManager(str(compose_file))


# Test initialization
def test_initialization(compose_manager, tmp_path):
    assert compose_manager.compose_file_path == tmp_path / "docker-compose.yml"


def test_initialization_creates_file(tmp_path):
    """Test that ComposeManager creates file with empty config if it doesn't exist"""
    compose_file = tmp_path / "docker-compose.yml"

    # Initialize manager (should create file)
    manager = ComposeManager(str(compose_file))

    # Verify file was created
    assert compose_file.exists()

    # Verify file contains basic structure
    with open(compose_file) as f:
        config = yaml.safe_load(f)
        assert config == {'services': {}}


# Test compose command detection
def test_detect_docker_compose(compose_manager):
    assert compose_manager.compose_command == ["docker", "compose"]


def test_detect_legacy_compose(legacy_compose_manager):
    assert legacy_compose_manager.compose_command == ["docker-compose"]


def test_no_compose_available(tmp_path, mocker):
    compose_file = tmp_path / "docker-compose.yml"
    compose_file.write_text("version: '3'")

    # Mock both commands failing
    mock_run = mocker.patch("subprocess.run")
    mock_run.side_effect = [
        subprocess.CalledProcessError(1, "docker compose"),
        subprocess.CalledProcessError(1, "docker-compose"),
    ]

    with pytest.raises(DockerNotFoundError, match="Neither 'docker compose' nor 'docker-compose' found"):
        ComposeManager(str(compose_file))


# Test _run_compose_command
def test_run_compose_command(compose_manager, mocker):
    mock_run = mocker.patch("subprocess.run")
    compose_manager._run_compose_command(["up"])
    mock_run.assert_called_once_with(
        ["docker", "compose", "-f", str(compose_manager.compose_file_path), "up"],
        check=True,
    )


def test_run_compose_command_legacy(legacy_compose_manager, mocker):
    mock_run = mocker.patch("subprocess.run")
    legacy_compose_manager._run_compose_command(["up"])
    mock_run.assert_called_once_with(
        ["docker-compose", "-f", str(legacy_compose_manager.compose_file_path), "up"],
        check=True,
    )


# Test up method
def test_up(compose_manager, mocker):
    mock_run = mocker.patch("subprocess.run")
    compose_manager.up()
    mock_run.assert_called_once_with(
        ["docker", "compose", "-f", str(compose_manager.compose_file_path), "up", "-d"],
        check=True,
    )


def test_up_legacy(legacy_compose_manager, mocker):
    mock_run = mocker.patch("subprocess.run")
    legacy_compose_manager.up()
    mock_run.assert_called_once_with(
        ["docker-compose", "-f", str(legacy_compose_manager.compose_file_path), "up", "-d"],
        check=True,
    )


def test_up_with_service(compose_manager, mocker):
    mock_run = mocker.patch("subprocess.run")
    compose_manager.up(service="web")
    mock_run.assert_called_once_with(
        ["docker", "compose", "-f", str(compose_manager.compose_file_path), "up", "-d", "web"],
        check=True,
    )


def test_up_with_service_legacy(legacy_compose_manager, mocker):
    mock_run = mocker.patch("subprocess.run")
    legacy_compose_manager.up(service="web")
    mock_run.assert_called_once_with(
        ["docker-compose", "-f", str(legacy_compose_manager.compose_file_path), "up", "-d", "web"],
        check=True,
    )


def test_up_without_detach(compose_manager, mocker):
    mock_run = mocker.patch("subprocess.run")
    compose_manager.up(detach=False)
    mock_run.assert_called_once_with(
        ["docker", "compose", "-f", str(compose_manager.compose_file_path), "up"],
        check=True,
    )


def test_up_without_detach_legacy(legacy_compose_manager, mocker):
    mock_run = mocker.patch("subprocess.run")
    legacy_compose_manager.up(detach=False)
    mock_run.assert_called_once_with(
        ["docker-compose", "-f", str(legacy_compose_manager.compose_file_path), "up"],
        check=True,
    )


# Test down method
def test_down(compose_manager, mocker):
    mock_run = mocker.patch("subprocess.run")
    compose_manager.down()
    mock_run.assert_called_once_with(
        ["docker", "compose", "-f", str(compose_manager.compose_file_path), "down"],
        check=True,
    )


def test_down_legacy(legacy_compose_manager, mocker):
    mock_run = mocker.patch("subprocess.run")
    legacy_compose_manager.down()
    mock_run.assert_called_once_with(
        ["docker-compose", "-f", str(legacy_compose_manager.compose_file_path), "down"],
        check=True,
    )


# Test restart method
def test_restart(compose_manager, mocker):
    mock_run = mocker.patch("subprocess.run")
    compose_manager.restart()
    mock_run.assert_called_once_with(
        ["docker", "compose", "-f", str(compose_manager.compose_file_path), "restart"],
        check=True,
    )


def test_restart_legacy(legacy_compose_manager, mocker):
    mock_run = mocker.patch("subprocess.run")
    legacy_compose_manager.restart()
    mock_run.assert_called_once_with(
        ["docker-compose", "-f", str(legacy_compose_manager.compose_file_path), "restart"],
        check=True,
    )


def test_restart_with_service(compose_manager, mocker):
    mock_run = mocker.patch("subprocess.run")
    compose_manager.restart(service="web")
    mock_run.assert_called_once_with(
        ["docker", "compose", "-f", str(compose_manager.compose_file_path), "restart", "web"],
        check=True,
    )


def test_restart_with_service_legacy(legacy_compose_manager, mocker):
    mock_run = mocker.patch("subprocess.run")
    legacy_compose_manager.restart(service="web")
    mock_run.assert_called_once_with(
        ["docker-compose", "-f", str(legacy_compose_manager.compose_file_path), "restart", "web"],
        check=True,
    )


# Test build method
def test_build(compose_manager, mocker):
    mock_run = mocker.patch("subprocess.run")
    compose_manager.build()
    mock_run.assert_called_once_with(
        ["docker", "compose", "-f", str(compose_manager.compose_file_path), "build"],
        check=True,
    )


def test_build_legacy(legacy_compose_manager, mocker):
    mock_run = mocker.patch("subprocess.run")
    legacy_compose_manager.build()
    mock_run.assert_called_once_with(
        ["docker-compose", "-f", str(legacy_compose_manager.compose_file_path), "build"],
        check=True,
    )


def test_build_with_service(compose_manager, mocker):
    mock_run = mocker.patch("subprocess.run")
    compose_manager.build(service="web")
    mock_run.assert_called_once_with(
        ["docker", "compose", "-f", str(compose_manager.compose_file_path), "build", "web"],
        check=True,
    )


def test_build_with_service_legacy(legacy_compose_manager, mocker):
    mock_run = mocker.patch("subprocess.run")
    legacy_compose_manager.build(service="web")
    mock_run.assert_called_once_with(
        ["docker-compose", "-f", str(legacy_compose_manager.compose_file_path), "build", "web"],
        check=True,
    )


# Test ps method
def test_ps(compose_manager, mocker):
    mock_run = mocker.patch("subprocess.run")
    compose_manager.ps()
    mock_run.assert_called_once_with(
        ["docker", "compose", "-f", str(compose_manager.compose_file_path), "ps"],
        check=True,
    )


def test_ps_legacy(legacy_compose_manager, mocker):
    mock_run = mocker.patch("subprocess.run")
    legacy_compose_manager.ps()
    mock_run.assert_called_once_with(
        ["docker-compose", "-f", str(legacy_compose_manager.compose_file_path), "ps"],
        check=True,
    )


def test_ps_with_service(compose_manager, mocker):
    mock_run = mocker.patch("subprocess.run")
    compose_manager.ps(service="web")
    mock_run.assert_called_once_with(
        ["docker", "compose", "-f", str(compose_manager.compose_file_path), "ps", "web"],
        check=True,
    )


def test_ps_with_service_legacy(legacy_compose_manager, mocker):
    mock_run = mocker.patch("subprocess.run")
    legacy_compose_manager.ps(service="web")
    mock_run.assert_called_once_with(
        ["docker-compose", "-f", str(legacy_compose_manager.compose_file_path), "ps", "web"],
        check=True,
    )


# Test run method
def test_run(compose_manager, mocker):
    mock_run = mocker.patch("subprocess.run")
    compose_manager.run("web")
    mock_run.assert_called_once_with(
        ["docker", "compose", "-f", str(compose_manager.compose_file_path), "run", "web"],
        check=True,
    )


def test_run_legacy(legacy_compose_manager, mocker):
    mock_run = mocker.patch("subprocess.run")
    legacy_compose_manager.run("web")
    mock_run.assert_called_once_with(
        ["docker-compose", "-f", str(legacy_compose_manager.compose_file_path), "run", "web"],
        check=True,
    )


# Test exec method
def test_exec(compose_manager, mocker):
    mock_run = mocker.patch("subprocess.run")
    compose_manager.exec("web", "ls")
    mock_run.assert_called_once_with(
        ["docker", "compose", "-f", str(compose_manager.compose_file_path), "exec", "web", "ls"],
        check=True,
    )


def test_exec_legacy(legacy_compose_manager, mocker):
    mock_run = mocker.patch("subprocess.run")
    legacy_compose_manager.exec("web", "ls")
    mock_run.assert_called_once_with(
        ["docker-compose", "-f", str(legacy_compose_manager.compose_file_path), "exec", "web", "ls"],
        check=True,
    )


# Test error handling in _run_compose_command
def test_run_compose_command_error(compose_manager, mocker):
    mock_run = mocker.patch("subprocess.run", side_effect=subprocess.CalledProcessError(1, "docker compose"))
    with pytest.raises(DockerCommandExecutionError):
        compose_manager._run_compose_command(["up"])
    mock_run.assert_called_once_with(
        ["docker", "compose", "-f", str(compose_manager.compose_file_path), "up"],
        check=True,
    )


def test_run_compose_command_error_legacy(legacy_compose_manager, mocker):
    mock_run = mocker.patch("subprocess.run", side_effect=subprocess.CalledProcessError(1, "docker-compose"))
    with pytest.raises(DockerCommandExecutionError):
        legacy_compose_manager._run_compose_command(["up"])
    mock_run.assert_called_once_with(
        ["docker-compose", "-f", str(legacy_compose_manager.compose_file_path), "up"],
        check=True,
    )


# Test edge case: empty command
def test_run_compose_command_empty_command(compose_manager, mocker):
    mock_run = mocker.patch("subprocess.run")
    compose_manager._run_compose_command([])
    mock_run.assert_called_once_with(
        ["docker", "compose", "-f", str(compose_manager.compose_file_path)],
        check=True,
    )


def test_run_compose_command_empty_command_legacy(legacy_compose_manager, mocker):
    mock_run = mocker.patch("subprocess.run")
    legacy_compose_manager._run_compose_command([])
    mock_run.assert_called_once_with(
        ["docker-compose", "-f", str(legacy_compose_manager.compose_file_path)],
        check=True,
    )


# Test logs method
def test_logs(compose_manager, mocker):
    mock_run = mocker.patch("subprocess.run")
    mock_run.return_value = subprocess.CompletedProcess(
        args=[],
        returncode=0,
        stdout="Container logs output"
    )

    logs = compose_manager.logs()
    mock_run.assert_called_once_with(
        ["docker", "compose", "-f", str(compose_manager.compose_file_path), "logs"],
        check=True,
        capture_output=True,
        text=True
    )
    assert logs == "Container logs output"


def test_logs_legacy(legacy_compose_manager, mocker):
    mock_run = mocker.patch("subprocess.run")
    mock_run.return_value = subprocess.CompletedProcess(
        args=[],
        returncode=0,
        stdout="Container logs output"
    )

    logs = legacy_compose_manager.logs()
    mock_run.assert_called_once_with(
        ["docker-compose", "-f", str(legacy_compose_manager.compose_file_path), "logs"],
        check=True,
        capture_output=True,
        text=True
    )
    assert logs == "Container logs output"


def test_logs_with_service(compose_manager, mocker):
    mock_run = mocker.patch("subprocess.run")
    mock_run.return_value = subprocess.CompletedProcess(
        args=[],
        returncode=0,
        stdout="Service logs output"
    )

    logs = compose_manager.logs(service="web")
    mock_run.assert_called_once_with(
        ["docker", "compose", "-f", str(compose_manager.compose_file_path), "logs", "web"],
        check=True,
        capture_output=True,
        text=True
    )
    assert logs == "Service logs output"


def test_logs_with_service_legacy(legacy_compose_manager, mocker):
    mock_run = mocker.patch("subprocess.run")
    mock_run.return_value = subprocess.CompletedProcess(
        args=[],
        returncode=0,
        stdout="Service logs output"
    )

    logs = legacy_compose_manager.logs(service="web")
    mock_run.assert_called_once_with(
        ["docker-compose", "-f", str(legacy_compose_manager.compose_file_path), "logs", "web"],
        check=True,
        capture_output=True,
        text=True
    )
    assert logs == "Service logs output"


# Test permission errors
def test_create_empty_compose_file_permission_error(tmp_path, mocker):
    compose_file = tmp_path / "docker-compose.yml"

    # Mock open to raise PermissionError
    mock_open = mocker.patch("builtins.open", side_effect=PermissionError)

    with pytest.raises(ComposeFilePermissionError) as exc_info:
        ComposeManager(str(compose_file))

    assert str(compose_file) in str(exc_info.value)
    assert "write" in str(exc_info.value)


def test_load_compose_file_permission_error(tmp_path, mocker):
    compose_file = tmp_path / "docker-compose.yml"
    compose_file.write_text("version: '3'")

    # Mock the version checks to simulate docker compose being available
    mock_run = mocker.patch("subprocess.run")
    mock_run.side_effect = [
        subprocess.CompletedProcess(args=[], returncode=0, stdout=""),  # docker compose succeeds
    ]

    # Mock open to raise PermissionError after file exists check
    original_open = open

    def mock_open_side_effect(*args, **kwargs):
        if 'w' not in kwargs.get('mode', ''):  # During read
            raise PermissionError
        return original_open(*args, **kwargs)

    mock_open = mocker.patch("builtins.open", side_effect=mock_open_side_effect)

    with pytest.raises(ComposeFilePermissionError) as exc_info:
        ComposeManager(str(compose_file))

    assert str(compose_file) in str(exc_info.value)
    assert "read" in str(exc_info.value)


def test_save_compose_file_permission_error(compose_manager, mocker):
    # Mock builtins.open to raise PermissionError only during write operations
    mock_open = mocker.mock_open()

    def mock_open_side_effect(*args, **kwargs):
        if len(args) > 1 and 'w' in args[1]:  # During write operations
            raise PermissionError("Permission denied")

    mock_open.side_effect = mock_open_side_effect
    mocker.patch("builtins.open", mock_open)

    # Create a dummy service to trigger file save
    dummy_service = mocker.Mock()
    dummy_service.to_dict.return_value = {'test-service': {}}

    with pytest.raises(ComposeFilePermissionError) as exc_info:
        compose_manager.add_service(dummy_service)

    assert str(compose_manager.compose_file_path) in str(exc_info.value)
    assert "write" in str(exc_info.value)


def test_add_service_initializes_services_dict(tmp_path, mocker):
    """Test that add_service initializes services dict if it doesn't exist"""
    compose_file = tmp_path / "docker-compose.yml"
    compose_file.write_text("version: '3'")  # Create file without services key

    # Mock the version checks
    mock_run = mocker.patch("subprocess.run")
    mock_run.side_effect = [
        subprocess.CompletedProcess(args=[], returncode=0, stdout=""),  # docker compose succeeds
    ]

    manager = ComposeManager(str(compose_file))
    manager._config = {}  # Explicitly remove services dict

    # Create a dummy service
    dummy_service = mocker.Mock()
    dummy_service.to_dict.return_value = {'test-service': {}}

    # Add service should initialize services dict
    manager.add_service(dummy_service)

    assert 'services' in manager._config
    assert manager._config['services'] == {'test-service': {}}


def test_update_service_initializes_services_dict(compose_manager, mocker):
    """Test that update_service initializes services dict if it doesn't exist"""
    # Remove services dict
    compose_manager._config = {}

    # Create a dummy service
    dummy_service = mocker.Mock()
    service_dict = {'test-service': {}}
    dummy_service.to_dict.return_value = service_dict

    # Should raise ServiceNotFoundError since service doesn't exist
    with pytest.raises(ServiceNotFoundError):
        compose_manager.update_service(dummy_service)

    # But should still initialize the services dict
    assert 'services' in compose_manager._config
    assert compose_manager._config['services'] == {}
