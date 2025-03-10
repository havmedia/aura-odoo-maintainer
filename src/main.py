import click

from src.ConfigManager import ConfigManager
from src.configs.DatabaseConfig import DatabaseConfig
from src.click_validators import validate_host
from src.configs.OdooConfig import OdooConfig
from src.const import SECURE_SERVICES, VALID_VERSIONS, DB_MASTER_DEFAULT_NAME
from .ComposeManager import ComposeManager
from .Services import PostgresService, WhoamiService, TraefikService
from .exceptions import SetupAlreadyExistsError, SetupNotFoundError
import secrets


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

    config_manager = ConfigManager.create(version=version, hosts=host,
                                          db_config=DatabaseConfig(password=create_password(),
                                                                   name=DB_MASTER_DEFAULT_NAME,
                                                                   user=DB_MASTER_DEFAULT_NAME))

    mode = 'production'
    # Check if host is localhost
    if host[0] == 'localhost' or host[0] == 'odoo.test':
        mode = 'local'

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
        api_insecure=mode == 'local',
        metrics=True,
    ))

    # Create and add live service
    whoami = WhoamiService(name='live')
    whoami.add_traefik(host[0], '8069')
    compose_manager.add_service(whoami)

    click.echo(f"Created docker-compose.yml with whoami service")


@cli.group()
@click.pass_context
def env(ctx):
    """Manage environments"""
    ctx.ensure_object(dict)

    compose_manager = ComposeManager('docker-compose.yml')
    if not compose_manager.config['services']:
        raise SetupNotFoundError()

    ctx.obj['COMPOSE_MANAGER'] = compose_manager
    ctx.obj['CONFIG_MANAGER'] = ConfigManager()


@env.command(name='create')
@click.argument('name', nargs=-1, required=True)
@click.pass_context
def env_create(ctx, name: list[str]):
    """Create a new or more envs"""
    config_manager: ConfigManager = ctx.obj['CONFIG_MANAGER']
    compose_manager: ComposeManager = ctx.obj['COMPOSE_MANAGER']

    for env_name in name:
        config_manager.add_odoo(OdooConfig(
            name=env_name,
            db_password=create_password()
        ))

        compose_manager.add_service(
            WhoamiService(name=env_name).add_traefik(f'{env_name}.{config_manager.get_hosts()[0]}', '8069'))
        print(env_name)


@env.command(name='delete')
@click.argument('name', nargs=-1, required=True)
@click.pass_context
def env_delete(ctx, name: list[str]):
    """Deletes one or more envs"""

    config_manager: ConfigManager = ctx.obj['CONFIG_MANAGER']

    non_existent = [env for env in name if env not in [odoo.name for odoo in config_manager.get_odoos()]]
    if non_existent:
        raise ValueError(f'Cannot delete envs: {", ".join(non_existent)} do not exist')

    secured_services = [service for service in name if service in SECURE_SERVICES]
    if secured_services:
        raise ValueError(f"Cannot delete {', '.join(secured_services)} service(s).")

    compose_manager: ComposeManager = ctx.obj['COMPOSE_MANAGER']

    for service_name in name:
        compose_manager.remove_service(service_name)
        config_manager.remove_odoo(service_name)

    print(name)


@env.command(name='list')
@click.pass_context
def env_list(ctx):
    """Lists all envs"""

    config_manager: ConfigManager = ctx.obj['CONFIG_MANAGER']

    service_names = [service.name for service in config_manager.get_odoos()]

    print(f"The following envs are available: {', '.join(service_names)}")


def create_password(length: int = 32) -> str:
    """Generate a random password of the given length."""
    return secrets.token_urlsafe(length)


if __name__ == '__main__':  # pragma: no cover
    cli()
