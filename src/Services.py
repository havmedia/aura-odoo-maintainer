from typing import Dict, Any, Optional, ClassVar, Set, Union, List

from .configs.DatabaseConfig import DatabaseConfig
from .exceptions import (
    InvalidKeyError,
    InvalidValueTypeError,
    InvalidRestartPolicyError
)


class BaseService:
    """Base class for Docker Compose services"""

    # Define valid configuration keys
    VALID_KEYS: ClassVar[Set[str]] = {
        'image', 'command', 'ports', 'environment', 'volumes', 'depends_on',
        'build', 'container_name', 'restart', 'networks', 'labels', 'expose',
        'env_file', 'entrypoint', 'user', 'working_dir', 'healthcheck'
    }

    VALID_RESTART_POLICIES: ClassVar[Set[str]] = {
        'no', 'always', 'on-failure', 'unless-stopped'
    }

    def __init__(self, name: str):
        self.name = name
        self._config: Dict[str, Any] = {}

    def set_healthcheck(self,
                        test: Union[str, List[str]],
                        interval: str = "30s",
                        timeout: str = "30s",
                        retries: int = 3,
                        start_period: Optional[str] = None,
                        disable: bool = False) -> 'BaseService':
        """
        Set healthcheck configuration for the service
        
        :param test: The test command. Can be a string or list of strings
        :param interval: Time between health checks (default: 30s)
        :param timeout: Maximum time to wait for a health check (default: 30s)
        :param retries: Number of retries before considering unhealthy (default: 3)
        :param start_period: Start period for the container (default: None)
        :param disable: Whether to disable the healthcheck (default: False)
        :return: self for method chaining
        """
        if disable:
            self._config['healthcheck'] = {"disable": True}
            return self

        if isinstance(test, str):
            test = ["CMD-SHELL", test]

        healthcheck = {
            "test": test,
            "interval": interval,
            "timeout": timeout,
            "retries": retries
        }

        if start_period:
            healthcheck["start_period"] = start_period

        self._config['healthcheck'] = healthcheck
        return self

    def set_restart_policy(self, policy: str) -> 'BaseService':
        """
        Set the restart policy for the service
        
        :param policy: One of 'no', 'always', 'on-failure', 'unless-stopped'
        :return: self for method chaining
        :raises InvalidRestartPolicyError: If the policy is not valid
        """
        if policy not in self.VALID_RESTART_POLICIES:
            raise InvalidRestartPolicyError(policy, self.VALID_RESTART_POLICIES)

        self._config['restart'] = policy
        return self

    @classmethod
    def from_dict(cls, name: str, config: Dict[str, Any]) -> 'BaseService':
        """
        Create a service from a dictionary configuration.
        
        :param name: Name of the service
        :param config: Service configuration dictionary
        :return: New service instance
        :raises InvalidKeyError: If configuration contains invalid keys
        :raises InvalidValueTypeError: If configuration values have invalid types
        """
        # Validate configuration keys
        invalid_keys = set(config.keys()) - cls.VALID_KEYS
        if invalid_keys:
            raise InvalidKeyError(invalid_keys)

        service = cls(name)

        # Validate and set each configuration option
        for key, value in config.items():
            if key == 'image' and not isinstance(value, str):
                raise InvalidValueTypeError(key, "string", type(value).__name__)
            elif key == 'command' and not isinstance(value, (str, list)):
                raise InvalidValueTypeError(key, "string or list", type(value).__name__)
            elif key == 'ports' and not isinstance(value, list):
                raise InvalidValueTypeError(key, "list", type(value).__name__)
            elif key == 'environment' and not isinstance(value, dict):
                raise InvalidValueTypeError(key, "dictionary", type(value).__name__)
            elif key == 'volumes' and not isinstance(value, list):
                raise InvalidValueTypeError(key, "list", type(value).__name__)
            elif key == 'depends_on' and not isinstance(value, list):
                raise InvalidValueTypeError(key, "list", type(value).__name__)

            service._config[key] = value

        return service

    def set_image(self, image: str) -> 'BaseService':
        """Set the Docker image for the service"""
        self._config['image'] = image
        return self

    def set_command(self, command: str | list[str]) -> 'BaseService':
        """Set the command to run in the container"""
        self._config['command'] = command
        return self

    def set_ports(self, ports: list[str]) -> 'BaseService':
        """Set port mappings for the service"""
        self._config['ports'] = ports
        return self

    def set_environment(self, env: Dict[str, str]) -> 'BaseService':
        """Set environment variables for the service"""
        self._config['environment'] = env
        return self

    def set_volumes(self, volumes: list[str]) -> 'BaseService':
        """Set volume mappings for the service"""
        self._config['volumes'] = volumes
        return self

    def set_depends_on(self, services: list[str]) -> 'BaseService':
        """Set service dependencies"""
        self._config['depends_on'] = services
        return self

    def to_dict(self) -> Dict[str, Any]:
        """Convert service configuration to dictionary"""
        return {self.name: self._config}


class WhoamiService(BaseService):
    """Traefik whoami service configuration"""

    def __init__(self, name: str, port: int = 2001):
        super().__init__(name)
        self.set_image("traefik/whoami")
        self.set_command([
            f"--port={port}",
            f"--name={name}"
        ])
        self.set_ports([f"{port}:{port}"])


class PostgresService(BaseService):
    """PostgreSQL service configuration"""

    def __init__(self, name: str,
                 db_config: DatabaseConfig,
                 port: int = 5432,
                 version: str = "15"):
        """
        Initialize a PostgreSQL service

        :param name: Service name
        :param postgres_password: Password for the PostgreSQL user
        :param postgres_user: PostgreSQL user (default: postgres)
        :param postgres_db: Default database name (default: postgres)
        :param port: Port to expose PostgreSQL on (default: 5432)
        :param version: PostgreSQL version (default: 15)
        """
        super().__init__(name)

        self.set_image(f"postgres:{version}")
        self.set_environment({
            "POSTGRES_PASSWORD": db_config.password,
            "POSTGRES_USER": db_config.user,
            "POSTGRES_DB": db_config.name
        })
        self.set_ports([f"{port}:5432"])

        # Add default volume for data persistence
        self.set_volumes([
            f"./{name}/data:/var/lib/postgresql/data"
        ])

        # Add healthcheck
        self.set_healthcheck(
            test=f"pg_isready -U {db_config.user}",
            interval="10s",
            timeout="5s",
            retries=5
        )

        # Set restart policy
        self.set_restart_policy("unless-stopped")


class TraefikService(BaseService):
    """Traefik service configuration"""

    def __init__(self, name: str, dashboard_port: int = 8080, api_insecure: bool = False, metrics: bool = False):
        """
        Initialize a Traefik service

        :param name: Service name
        :param dashboard_port: Port for the Traefik dashboard (default: 8080)
        :param api_insecure: Whether to enable insecure API (default: False)
        """
        super().__init__(name)

        self.set_image("traefik:v3")

        # Configure ports
        self.set_ports([
            "80:80",  # HTTP
            "443:443",  # HTTPS
            f"{dashboard_port}:8080"  # Dashboard/API
        ])

        # Add command with basic configuration
        command = [
            "--providers.docker=true",
            "--providers.docker.exposedbydefault=false",
            "--entrypoints.web.address=:80",
            "--entrypoints.websecure.address=:443"
        ]

        if metrics:
            command.extend([
                "--metrics.prometheus=true",
            ])

        if api_insecure:
            command.extend([
                "--api.insecure=true",
                "--api.dashboard=true"
            ])

        self.set_command(command)

        # Add volumes for Docker socket and configuration
        self.set_volumes([
            "/var/run/docker.sock:/var/run/docker.sock:ro",
            f"./{name}/config:/etc/traefik"
        ])

        # Set restart policy
        self.set_restart_policy("unless-stopped")

