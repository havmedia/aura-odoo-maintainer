import yaml
from pathlib import Path
from typing import List

from src.configs.DatabaseConfig import DatabaseConfig
from src.configs.OdooConfig import OdooConfig
from src.exceptions import OdooAlreadyExistsError
from src.const import SECURE_SERVICES


class ConfigManager:
    def __init__(self, config_path: str = 'setup.yml'):
        self.config_path = Path(config_path)
        self._validate_config_exists()
        self.config = self._load_config()
        self.db_config = DatabaseConfig.from_dict(self.config['db'])

    @classmethod
    def create(cls, version: str, hosts: List[str], db_config: DatabaseConfig,
               config_path: str = 'setup.yml') -> 'ConfigManager':
        path = Path(config_path)
        if path.exists():
            raise ValueError(f"Config file {config_path} already exists.")

        cls._create_default_config_file(hosts, version, db_config, path)
        return cls(config_path=config_path)

    @staticmethod
    def _create_default_config_file(hosts: List[str], version: str, db_config: DatabaseConfig,
                                    config_path: Path) -> None:
        with open(config_path, 'w') as file:
            yaml.dump({'version': version, 'hosts': hosts,
                       'db': db_config.to_dict(), 'services': []}, file)

    def _validate_config_exists(self) -> None:
        if not self.config_path.exists():
            raise ValueError(f"{self.config_path} does not exist.")

    def _load_config(self) -> dict:
        with open(self.config_path, 'r') as file:
            config = yaml.safe_load(file) or {}
        return config

    def _save_config(self) -> None:
        with open(self.config_path, 'w') as file:
            yaml.dump(self.config, file, default_flow_style=False)

    def get_version(self) -> str:
        return self.config['version']

    def get_hosts(self) -> List[str]:
        return self.config.get('hosts', [])

    def get_db(self) -> DatabaseConfig:
        return self.db_config

    def set_hosts(self, hosts: List[str]) -> None:
        if not hosts:
            raise ValueError("There must be at least one host.")
        self.config['hosts'] = hosts
        self._save_config()

    def add_host(self, host: str) -> None:
        if host not in self.config['hosts']:
            self.config['hosts'].append(host)
            self._save_config()

    def remove_host(self, host: str) -> None:
        if host in self.config['hosts']:
            if len(self.config['hosts']) > 1:
                self.config['hosts'].remove(host)
                self._save_config()
            else:
                raise ValueError("Cannot remove the only remaining host.")

    def list_hosts(self) -> List[str]:
        return self.get_hosts()

    def get_odoos(self) -> List[OdooConfig]:
        return [OdooConfig.from_dict(service) for service in self.config['services']]

    def add_odoo(self, service: OdooConfig) -> None:
        # Check if service name already exists
        if service.name in [s['name'] for s in self.config['services']]:
            raise OdooAlreadyExistsError(service.name)

        if service.name in SECURE_SERVICES:
            raise ValueError(f"Cannot add {service.name} service.")

        self.config['services'].append(service.to_dict())
        self._save_config()

    def remove_odoo(self, name: str) -> None:
        if name not in [s['name'] for s in self.config['services']]:
            raise ValueError(f"Odoo service {name} does not exist.")

        if name in SECURE_SERVICES:
            raise ValueError(f"Cannot remove {name} service.")

        self.config['services'] = [s for s in self.config['services'] if s['name'] != name]
        self._save_config()
