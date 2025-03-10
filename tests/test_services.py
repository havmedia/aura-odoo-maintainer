import pytest
from src.Services import BaseService, WhoamiService, PostgresService, TraefikService
from src.ComposeManager import ComposeManager
from src.configs.DatabaseConfig import DatabaseConfig
from src.exceptions import (
    InvalidKeyError,
    InvalidValueTypeError,
    InvalidRestartPolicyError,
    ServiceNotFoundError,
    ServiceAlreadyExistsError
)


def test_base_service():
    service = BaseService("test")
    service.set_image("nginx:latest")
    service.set_ports(["80:80"])
    service.set_environment({"DEBUG": "true"})
    service.set_depends_on(["db", "redis"])
    service.set_labels(["label1", "label2"])
    
    config = service.to_dict()
    assert "test" in config
    assert config["test"]["image"] == "nginx:latest"
    assert config["test"]["ports"] == ["80:80"]
    assert config["test"]["environment"] == {"DEBUG": "true"}
    assert config["test"]["depends_on"] == ["db", "redis"]
    assert config["test"]["labels"] == ["label1", "label2"]

    service.add_labels(["label3", "label4"])
    config = service.to_dict()
    assert config["test"]["labels"] == ["label1", "label2", "label3", "label4"]

    service.add_traefik("host1", "1010:1010")
    config = service.to_dict()
    assert config["test"]["labels"] == ["label1", "label2", "label3", "label4", "traefik.enable=true", "traefik.http.routers.test.rule=Host(`host1`)", "traefik.http.routers.test.entrypoints=web", "traefik.http.services.test.loadbalancer.server.port=1010:1010"]


def test_base_service_healthcheck():
    service = BaseService("test")
    
    # Test string command
    service.set_healthcheck(
        test="curl -f http://localhost/health",
        interval="15s",
        timeout="10s",
        retries=5,
        start_period="30s"
    )
    
    config = service.to_dict()["test"]["healthcheck"]
    assert config["test"] == ["CMD-SHELL", "curl -f http://localhost/health"]
    assert config["interval"] == "15s"
    assert config["timeout"] == "10s"
    assert config["retries"] == 5
    assert config["start_period"] == "30s"
    
    # Test list command
    service.set_healthcheck(
        test=["CMD", "curl", "-f", "http://localhost/health"]
    )
    config = service.to_dict()["test"]["healthcheck"]
    assert config["test"] == ["CMD", "curl", "-f", "http://localhost/health"]
    
    # Test disable
    service.set_healthcheck(test="", disable=True)
    config = service.to_dict()["test"]["healthcheck"]
    assert config == {"disable": True}


def test_base_service_restart_policy():
    service = BaseService("test")
    
    # Test valid policies
    for policy in BaseService.VALID_RESTART_POLICIES:
        service.set_restart_policy(policy)
        assert service.to_dict()["test"]["restart"] == policy
    
    # Test invalid policy
    with pytest.raises(InvalidRestartPolicyError) as exc_info:
        service.set_restart_policy("invalid")
    assert exc_info.value.invalid_policy == "invalid"
    assert exc_info.value.valid_policies == BaseService.VALID_RESTART_POLICIES


def test_base_service_from_dict():
    config = {
        "image": "nginx:latest",
        "ports": ["80:80"],
        "environment": {"DEBUG": "true"},
        "volumes": ["/data:/data"],
        "depends_on": ["db"]
    }
    
    service = BaseService.from_dict("test", config)
    result = service.to_dict()
    
    assert result["test"] == config


def test_base_service_from_dict_validation():
    # Test invalid key
    with pytest.raises(InvalidKeyError) as exc_info:
        BaseService.from_dict("test", {"invalid_key": "value"})
    assert "invalid_key" in exc_info.value.invalid_keys
    
    # Test invalid image type
    with pytest.raises(InvalidValueTypeError) as exc_info:
        BaseService.from_dict("test", {"image": 123})
    assert exc_info.value.key == "image"
    assert exc_info.value.expected_type == "string"
    assert exc_info.value.received_type == "int"
    
    # Test invalid command type
    with pytest.raises(InvalidValueTypeError) as exc_info:
        BaseService.from_dict("test", {"command": 123})
    assert exc_info.value.key == "command"
    assert exc_info.value.expected_type == "string or list"
    
    # Test invalid ports type
    with pytest.raises(InvalidValueTypeError) as exc_info:
        BaseService.from_dict("test", {"ports": "80:80"})
    assert exc_info.value.key == "ports"
    assert exc_info.value.expected_type == "list"
    
    # Test invalid environment type
    with pytest.raises(InvalidValueTypeError) as exc_info:
        BaseService.from_dict("test", {"environment": ["DEBUG=true"]})
    assert exc_info.value.key == "environment"
    assert exc_info.value.expected_type == "dictionary"
    
    # Test invalid volumes type
    with pytest.raises(InvalidValueTypeError) as exc_info:
        BaseService.from_dict("test", {"volumes": "/data:/data"})
    assert exc_info.value.key == "volumes"
    assert exc_info.value.expected_type == "list"
    
    # Test invalid depends_on type
    with pytest.raises(InvalidValueTypeError) as exc_info:
        BaseService.from_dict("test", {"depends_on": "db"})
    assert exc_info.value.key == "depends_on"
    assert exc_info.value.expected_type == "list"


def test_whoami_service():
    service = WhoamiService(name="test_whoami", port=8080)
    config = service.to_dict()
    
    assert "test_whoami" in config
    assert config["test_whoami"]["image"] == "traefik/whoami"
    assert "--port=8080" in config["test_whoami"]["command"]
    assert "--name=test_whoami" in config["test_whoami"]["command"]


def test_compose_manager_service_operations(tmp_path):
    # Create a test compose file
    compose_file = tmp_path / "docker-compose.yml"
    compose_file.touch()
    
    manager = ComposeManager(str(compose_file))
    
    # Test adding a service
    whoami = WhoamiService("test_whoami", 8080)
    manager.add_service(whoami)
    
    # Test adding duplicate service
    with pytest.raises(ServiceAlreadyExistsError) as exc_info:
        manager.add_service(whoami)
    assert exc_info.value.service_name == "test_whoami"
    
    services = manager.list_services()
    assert "test_whoami" in services
    
    # Test getting a service
    service = manager.get_service("test_whoami")
    assert isinstance(service, BaseService)
    assert service.name == "test_whoami"
    service_dict = service.to_dict()
    assert service_dict["test_whoami"]["image"] == "traefik/whoami"
    
    # Test getting nonexistent service
    with pytest.raises(ServiceNotFoundError) as exc_info:
        manager.get_service("nonexistent")
    assert exc_info.value.service_name == "nonexistent"
    
    # Test updating a service
    whoami.set_environment({"DEBUG": "true"})
    manager.update_service(whoami)
    
    updated_service = manager.get_service("test_whoami")
    updated_dict = updated_service.to_dict()
    assert updated_dict["test_whoami"]["environment"] == {"DEBUG": "true"}
    
    # Test updating nonexistent service
    nonexistent = WhoamiService("nonexistent")
    with pytest.raises(ServiceNotFoundError) as exc_info:
        manager.update_service(nonexistent)
    assert exc_info.value.service_name == "nonexistent"
    
    # Test removing a service
    manager.remove_service("test_whoami")
    assert "test_whoami" not in manager.list_services()
    
    # Test removing nonexistent service
    with pytest.raises(ServiceNotFoundError) as exc_info:
        manager.remove_service("test_whoami")
    assert exc_info.value.service_name == "test_whoami"


def test_compose_manager_nonexistent_service(tmp_path):
    compose_file = tmp_path / "docker-compose.yml"
    compose_file.touch()
    
    manager = ComposeManager(str(compose_file))
    
    with pytest.raises(ServiceNotFoundError):
        manager.get_service("nonexistent")
    
    with pytest.raises(ServiceNotFoundError):
        whoami = WhoamiService("test_whoami")
        manager.update_service(whoami)


def test_postgres_service():
    service = PostgresService(
        name="test_db",
        db_config=DatabaseConfig(name="test_db", password="secret", user="testuser"),
        port=5433,
        version="14"
    )
    
    config = service.to_dict()
    assert "test_db" in config
    db_config = config["test_db"]
    
    # Check image and version
    assert db_config["image"] == "postgres:14"
    
    # Check environment variables
    assert db_config["environment"] == {
        "POSTGRES_PASSWORD": "secret",
        "POSTGRES_USER": "testuser",
        "POSTGRES_DB": "test_db"
    }
    
    # Check port mapping
    assert db_config["ports"] == ["5433:5432"]
    
    # Check volume
    assert db_config["volumes"] == ["./test_db/data:/var/lib/postgresql/data"]
    
    # Check healthcheck
    assert "healthcheck" in db_config
    assert db_config["healthcheck"]["test"] == ["CMD-SHELL", "pg_isready -U testuser"]
    assert db_config["healthcheck"]["interval"] == "10s"
    assert db_config["healthcheck"]["timeout"] == "5s"
    assert db_config["healthcheck"]["retries"] == 5
    
    # Check restart policy
    assert db_config["restart"] == "unless-stopped"

def test_traefik_service():
    service = TraefikService(
        name="test_traefik",
        dashboard_port=8080,
        api_insecure=True,
        metrics=True
    )

    config = service.to_dict()
    assert "test_traefik" in config
    assert config["test_traefik"]["image"] == "traefik:v3"
    assert config["test_traefik"]["ports"] == ["80:80", "443:443", "8080:8080"]
    assert config["test_traefik"]["command"] == [
        "--providers.docker=true",
        "--providers.docker.exposedbydefault=false",
        "--entrypoints.web.address=:80",
        "--entrypoints.websecure.address=:443",
        "--metrics.prometheus=true",
        "--api.insecure=true",
        "--api.dashboard=true"
    ]