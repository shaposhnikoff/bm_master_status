import pytest
import json
from unittest.mock import patch, MagicMock
from generate_status_page import (
    check_tcp,
    check_http,
    check_icmp,
    check_server,
    main
)

# Sample test data
MOCK_SERVERS = [
    {
        "id": "1",
        "country": "US",
        "address": "test1.brandmeister.network"
    },
    {
        "id": "2",
        "country": "DE",
        "address": "test2.brandmeister.network"
    }
]

@pytest.fixture
def mock_api_response():
    return MagicMock(
        json=lambda: MOCK_SERVERS,
        raise_for_status=lambda: None
    )

@pytest.fixture
def mock_socket():
    with patch('socket.create_connection') as mock:
        yield mock

@pytest.fixture
def mock_requests():
    with patch('requests.get') as mock:
        yield mock

@pytest.fixture
def mock_ping():
    with patch('ping3.ping') as mock:
        yield mock

def test_check_tcp_success(mock_socket):
    """Test successful TCP connection check"""
    mock_socket.return_value.__enter__.return_value = MagicMock()
    assert check_tcp("test.brandmeister.network", 50180) is True

def test_check_tcp_failure(mock_socket):
    """Test failed TCP connection check"""
    mock_socket.side_effect = Exception("Connection failed")
    assert check_tcp("test.brandmeister.network", 50180) is False

def test_check_http_success(mock_requests):
    """Test successful HTTP connection check"""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_requests.return_value = mock_response
    assert check_http("test.brandmeister.network") is True

def test_check_http_failure(mock_requests):
    """Test failed HTTP connection check"""
    mock_requests.side_effect = Exception("HTTP request failed")
    assert check_http("test.brandmeister.network") is False

def test_check_icmp_success(mock_ping):
    """Test successful ICMP check"""
    mock_ping.return_value = 0.1
    assert check_icmp("test.brandmeister.network") is True

def test_check_icmp_failure(mock_ping):
    """Test failed ICMP check"""
    mock_ping.return_value = None
    assert check_icmp("test.brandmeister.network") is False

def test_check_server_all_success(mock_socket, mock_requests, mock_ping):
    """Test server check with all services successful"""
    # Mock successful responses
    mock_socket.return_value.__enter__.return_value = MagicMock()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_requests.return_value = mock_response
    mock_ping.return_value = 0.1

    result = check_server(MOCK_SERVERS[0])
    assert result["tcp_ok"] is True
    assert result["http_ok"] is True
    assert result["icmp_ok"] is True
    assert result["id"] == "1"
    assert result["country"] == "US"

def test_check_server_all_failure(mock_socket, mock_requests, mock_ping):
    """Test server check with all services failed"""
    # Mock failed responses
    mock_socket.side_effect = Exception("TCP failed")
    mock_requests.side_effect = Exception("HTTP failed")
    mock_ping.return_value = None

    result = check_server(MOCK_SERVERS[0])
    assert result["tcp_ok"] is False
    assert result["http_ok"] is False
    assert result["icmp_ok"] is False

@patch('builtins.open', new_callable=MagicMock)
@patch('requests.get')
def test_main_success(mock_requests, mock_open, mock_socket, mock_ping):
    """Test successful main execution"""
    # Mock API response
    mock_response = MagicMock()
    mock_response.json.return_value = MOCK_SERVERS
    mock_requests.return_value = mock_response

    # Mock successful network checks
    mock_socket.return_value.__enter__.return_value = MagicMock()
    mock_ping.return_value = 0.1

    # Run main function
    main()

    # Verify file was written
    mock_open.assert_called_once_with("index.html", "w", encoding='utf-8')
    file_content = mock_open.return_value.__enter__.return_value.write.call_args[0][0]
    
    # Verify HTML content
    assert "BrandMeister Master Status" in file_content
    assert "test1.brandmeister.network" in file_content
    assert "test2.brandmeister.network" in file_content
    assert "🟢" in file_content  # Success indicators

@patch('requests.get')
def test_main_api_failure(mock_requests):
    """Test main execution with API failure"""
    mock_requests.side_effect = Exception("API request failed")
    main()  # Should handle the error gracefully

if __name__ == '__main__':
    pytest.main(['-v']) 