import pytest
from unittest.mock import patch, MagicMock
from tls_cipher_scanner import check_cipher_security, scan_endpoint

def test_check_cipher_security_secure():
    issues = check_cipher_security("ECDHE-ECDSA-AES128-GCM-SHA256")
    assert len(issues) == 0

def test_check_cipher_security_weak():
    issues = check_cipher_security("RC4-SHA")
    assert any("RC4" in issue for issue in issues)

    issues2 = check_cipher_security("DES-CBC3-SHA")
    assert any("3DES" in issue for issue in issues2)

    issues3 = check_cipher_security("AES128-CBC-SHA")
    assert any("CBC" in issue for issue in issues3)

@patch("socket.create_connection")
@patch("ssl.create_default_context")
def test_scan_endpoint_success(mock_create_context, mock_create_connection):
    mock_sock = MagicMock()
    mock_create_connection.return_value.__enter__.return_value = mock_sock

    mock_context = MagicMock()
    mock_create_context.return_value = mock_context
    mock_ssock = MagicMock()
    mock_context.wrap_socket.return_value.__enter__.return_value = mock_ssock
    mock_ssock.cipher.return_value = ("ECDHE-RSA-AES128-GCM-SHA256", "TLSv1.2", 128)

    results = scan_endpoint("example.com", 443)
    assert results["host"] == "example.com"
    assert results["port"] == 443
    assert len(results["ciphers"]) == 1
    assert results["ciphers"][0]["name"] == "ECDHE-RSA-AES128-GCM-SHA256"
