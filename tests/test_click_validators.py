from unittest.mock import patch
from src.click_validators import get_public_ip, get_ip_from_domain, validate_host
import socket
import pytest
import click
from unittest.mock import patch
from src.click_validators import validate_host  # Replace 'your_module' with the actual module name


@pytest.fixture
def mock_ctx():
    return None  # Context is not used in validate_host


@pytest.fixture
def mock_param():
    return None  # Param is not used in validate_host


@patch("src.click_validators.get_ip_from_domain")
@patch("src.click_validators.get_public_ip")
@patch("socket.gethostbyname")
def test_validate_host_valid_hostname(mock_gethostbyname, mock_get_public_ip, mock_get_ip_from_domain, mock_ctx,
                                      mock_param):
    mock_gethostbyname.return_value = "192.168.1.1"
    mock_get_ip_from_domain.return_value = "192.168.1.1"
    mock_get_public_ip.return_value = "192.168.1.1"

    assert validate_host(mock_ctx, mock_param, "example.com") == ["example.com"]


@patch("src.click_validators.get_ip_from_domain")
@patch("socket.gethostbyname")
def test_validate_host_invalid_hostname(mock_gethostbyname, mock_get_ip_from_domain, mock_ctx, mock_param):
    mock_gethostbyname.side_effect = socket.gaierror
    mock_get_ip_from_domain.return_value = None

    with pytest.raises(click.BadParameter, match="Host does not exist."):
        validate_host(mock_ctx, mock_param, "invalid.example")


@patch("src.click_validators.get_ip_from_domain")
@patch("src.click_validators.get_public_ip")
@patch("socket.gethostbyname")
def test_validate_host_ip_mismatch(mock_gethostbyname, mock_get_public_ip, mock_get_ip_from_domain, mock_ctx,
                                   mock_param):
    mock_gethostbyname.return_value = "192.168.1.1"
    mock_get_ip_from_domain.return_value = "192.168.1.1"
    mock_get_public_ip.return_value = "192.168.1.2"

    with pytest.raises(click.BadParameter,
                       match="The IP address associated with the host does not match the public IP address."):
        validate_host(mock_ctx, mock_param, "example.com")


@patch("socket.gethostbyname")
def test_validate_host_localhost(mock_gethostbyname, mock_ctx, mock_param):
    assert validate_host(mock_ctx, mock_param, "localhost") == ["localhost"]


def test_get_public_ip():
    with patch('requests.get') as mock_get:
        mock_get.return_value.text = '8.8.8.8'  # Mocked public IP
        assert get_public_ip() == '8.8.8.8'


def test_get_ip_from_domain_success():
    with patch('socket.gethostbyname') as mock_gethostbyname:
        mock_gethostbyname.return_value = '192.0.2.1'
        assert get_ip_from_domain('example.com') == '192.0.2.1'


def test_get_ip_from_domain_failure():
    with patch('socket.gethostbyname', side_effect=socket.gaierror):
        assert get_ip_from_domain('invalid_domain') is None


def test_validate_host_success():
    with patch('socket.gethostbyname') as mock_gethostbyname, \
            patch('requests.get') as mock_get:
        mock_gethostbyname.return_value = '192.0.2.1'
        mock_get.return_value


@patch("src.click_validators.get_ip_from_domain")
@patch("socket.gethostbyname")
def test_validate_host_dns_resolution_error(mock_gethostbyname, mock_get_ip_from_domain, mock_ctx, mock_param):
    mock_gethostbyname.return_value = "192.168.1.1"  # Let the first check pass
    mock_get_ip_from_domain.return_value = None  # Simulate DNS resolution failure

    with pytest.raises(click.BadParameter,
                       match="Host does not resolve to an IP address or there is a other error related error with the DNS."):
        validate_host(mock_ctx, mock_param, "example.com")
