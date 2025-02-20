import click

from src.ConfigManager import ConfigManager
from src.configs.DatabaseConfig import DatabaseConfig
from src.click_validators import validate_host
from src.configs.OdooConfig import OdooConfig
from .ComposeManager import ComposeManager
from .Services import PostgresService, WhoamiService, TraefikService
from .exceptions import SetupAlreadyExistsError
import secrets

VALID_VERSIONS = ['18.0']
DB_MASTER_DEFAULT_NAME = 'postgres'


@click.group()
def cli():
    """CLI tool for managing aura odoo setups"""
    pass


@cli.command()
@click.option('--host', help='Hostname which should be used for odoo', multiple=True, required=True,
              callback=validate_host)
@click.option('--version', default='18.0', help='Odoo version to install', type=click.Choice(VALID_VERSIONS))
def init(host: list[str], version: str):
    """Initialize a new docker-compose.yml with database and whoami services"""
    compose_manager = ComposeManager('docker-compose.yml')

    # Check if any services already exist
    if compose_manager.config['services']:
        raise SetupAlreadyExistsError()

    config_manager = ConfigManager.create(version=version, hosts=host, db_config=DatabaseConfig(password=create_password(), name=DB_MASTER_DEFAULT_NAME, user=DB_MASTER_DEFAULT_NAME))

    # Create and add postgres service
    compose_manager.add_service(PostgresService(
        name='db',
        db_config=config_manager.get_db(),
    ))

    config_manager.add_odoo(OdooConfig(
        name='live',
        db_password=create_password()
    ))

    compose_manager.add_service(TraefikService(
        name='traefik',
        api_insecure=True,
    ))

    # Create and add whoami service
    whoami = WhoamiService(name='whoami')
    compose_manager.add_service(whoami)

    click.echo(f"Created docker-compose.yml with whoami service")


def create_password(length: int = 32) -> str:
    """Generate a random password of the given length."""
    return secrets.token_urlsafe(length)


if __name__ == '__main__':  # pragma: no cover
    cli()
