import subprocess
from pathlib import Path
from typing import List, Optional, Dict, Any
import yaml

from .Services import BaseService
from .exceptions import (
    ComposeFilePermissionError,
    DockerNotFoundError,
    DockerCommandExecutionError,
    ServiceNotFoundError,
    ServiceAlreadyExistsError
)
from .const import SECURE_SERVICES


def _detect_compose_command() -> List[str]:
    """
    Detect whether to use 'docker compose' or 'docker-compose'

    :raises DockerNotFoundError: If neither docker compose nor docker-compose is found
    """
    try:
        # Try docker compose first (newer version)
        subprocess.run(['docker', 'compose', 'version'],
                     capture_output=True, check=True)
        return ['docker', 'compose']
    except subprocess.CalledProcessError:
        try:
            # Fall back to docker-compose
            subprocess.run(['docker-compose', '--version'],
                         capture_output=True, check=True)
            return ['docker-compose']
        except (subprocess.CalledProcessError, FileNotFoundError):
            raise DockerNotFoundError()


class ComposeManager:
    def __init__(self, compose_file_path: str):
        self.compose_file_path = Path(compose_file_path)
        # Create file if it doesn't exist
        if not self.compose_file_path.exists():
            self._create_empty_compose_file()
        # Detect which compose command to use
        self.compose_command = _detect_compose_command()
        # Load existing compose file
        self._config = self._load_compose_file()

    def _create_empty_compose_file(self):
        """Create an empty compose file with basic structure"""
        try:
            with open(self.compose_file_path, 'w') as f:
                yaml.dump({'services': {}}, f)
        except PermissionError:
            raise ComposeFilePermissionError(str(self.compose_file_path), "write")

    def _run_compose_command(self, command: List[str], service: Optional[str] = None, capture_output: bool = False):
        """
        Runs a docker-compose command on the compose file.

        :raises DockerCommandExecutionError: If the command fails to execute
        """
        cmd = self.compose_command + ["-f", str(self.compose_file_path)]
        cmd.extend(command)
        if service:
            cmd.append(service)

        try:
            if capture_output:
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                return result.stdout
            else:
                subprocess.run(cmd, check=True)
                return None
        except subprocess.CalledProcessError as e:
            raise DockerCommandExecutionError(" ".join(cmd), str(e))

    def up(self, service: Optional[str] = None, detach: bool = True):
        """
        Starts the services in the compose file.
        :param service: The service to start. If not provided, all services will be started.
        :param detach: Whether to run the command in detached mode.
        """
        command = ["up"]
        if detach:
            command.append("-d")
        self._run_compose_command(command, service)

    def down(self):
        """
        Stops and removes the services in the compose file.
        """
        self._run_compose_command(["down"])

    def restart(self, service: Optional[str] = None):
        """
        Restarts the services in the compose file.
        :param service: The service to restart. If not provided, all services will be restarted.
        """
        self._run_compose_command(["restart"], service)

    def build(self, service: Optional[str] = None):
        """
        Builds the images in the compose file.
        :param service: The service to build. If not provided, all services will be built.
        """
        self._run_compose_command(["build"], service)

    def ps(self, service: Optional[str] = None):
        """
        Lists the running containers in the compose file.
        :param service: The service to list containers for. If not provided, all services will be listed.
        """
        self._run_compose_command(["ps"], service)

    def run(self, service: str):
        """
        Runs the services in the compose file.
        :param service: The service to run.
        """
        self._run_compose_command(["run"], service)

    def exec(self, service: str, command: str):
        """
        Runs a command in a container in the compose file.
        :param service: The service to run the command on.
        :param command: The command to run.
        """
        self._run_compose_command(["exec", service, command])

    def logs(self, service: Optional[str] = None) -> str:
        """
        Get logs from containers
        :param service: Optional service name to get logs for
        :return: Container logs as string
        """
        return self._run_compose_command(["logs"], service, capture_output=True)

    def _load_compose_file(self) -> Dict[str, Any]:
        """
        Load the compose file configuration

        :raises ComposeFilePermissionError: If the file cannot be read
        """
        try:
            with open(self.compose_file_path) as f:
                config = yaml.safe_load(f)
                return config if config is not None else {'services': {}}
        except PermissionError:
            raise ComposeFilePermissionError(str(self.compose_file_path), "read")

    def _save_compose_file(self):
        """
        Save the current configuration to the compose file

        :raises ComposeFilePermissionError: If the file cannot be written
        """
        try:
            with open(self.compose_file_path, 'w') as f:
                yaml.dump(self._config, f, default_flow_style=False, sort_keys=False)
        except PermissionError:
            raise ComposeFilePermissionError(str(self.compose_file_path), "write")

    def _ensure_services_dict(self):
        """Ensure the services dictionary exists in the config"""
        if 'services' not in self._config:
            self._config['services'] = {}

    def add_service(self, service: BaseService):
        """
        Add a new service to the compose file

        :raises ServiceAlreadyExistsError: If the service already exists
        :raises ComposeFilePermissionError: If the file cannot be written
        """
        self._ensure_services_dict()

        service_dict = service.to_dict()
        service_name = next(iter(service_dict))

        if service_name in self._config['services']:
            raise ServiceAlreadyExistsError(service_name)

        self._config['services'].update(service_dict)
        self._save_compose_file()

    def remove_service(self, service_name: str):
        """
        Remove a service from the compose file

        :raises ServiceNotFoundError: If the service does not exist
        :raises ComposeFilePermissionError: If the file cannot be written
        """
        self._ensure_services_dict()

        if service_name not in self._config['services']:
            raise ServiceNotFoundError(service_name)

        if service_name in SECURE_SERVICES:
            raise ValueError(f"Cannot remove {service_name} service.")

        del self._config['services'][service_name]
        self._save_compose_file()

    def update_service(self, service: BaseService):
        """
        Update an existing service in the compose file

        :raises ServiceNotFoundError: If the service does not exist
        :raises ComposeFilePermissionError: If the file cannot be written
        """
        self._ensure_services_dict()

        service_dict = service.to_dict()
        service_name = next(iter(service_dict))

        if service_name not in self._config['services']:
            raise ServiceNotFoundError(service_name)

        self._config['services'].update(service_dict)
        self._save_compose_file()

    def get_service(self, service_name: str) -> BaseService:
        """
        Get service configuration by name

        :param service_name: Name of the service to get
        :return: BaseService instance
        :raises ServiceNotFoundError: If the service does not exist
        """
        self._ensure_services_dict()

        if service_name not in self._config['services']:
            raise ServiceNotFoundError(service_name)

        return BaseService.from_dict(service_name, self._config['services'][service_name])

    def list_services(self) -> List[str]:
        """List all service names in the compose file"""
        self._ensure_services_dict()
        return list(self._config['services'].keys())

    @property
    def config(self):
        return self._config
