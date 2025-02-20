import click
import socket
import requests


def get_public_ip() -> str:
    # TODO: Replace with a function that uses the public IPv4 address of the server
    return requests.get('https://api.ipify.org').text


def get_ip_from_domain(domain: str) -> str | None:
    """
    Returns the IPv4 address associated with the given domain name.
    If the domain resolves to multiple IPs, only one is returned.
    """
    try:
        ip = socket.gethostbyname(domain)
        return ip
    except socket.gaierror as e:
        print(f"Error resolving {domain}: {e}")
        return None


def validate_host(ctx, param, value) -> list:
    """Validates that the host parameter is a valid hostname."""

    if type(value) is not tuple:
        value = (value,)

    if value == ('localhost',):
        return list(value)
    # Check if the value is a valid hostname. This check verifies general hostname characteristics.
    for host in value:
        try:
            socket.gethostbyname(host)  # This tries to resolve the hostname to an IP address
        except socket.gaierror:
            raise click.BadParameter("Host does not exist.")

        ip_from_domain = get_ip_from_domain(host)
        if not ip_from_domain:
            raise click.BadParameter(
                "Host does not resolve to an IP address or there is a other error related error with the DNS.")

        if ip_from_domain != get_public_ip():
            raise click.BadParameter("The IP address associated with the host does not match the public IP address.")
    return list(value)
