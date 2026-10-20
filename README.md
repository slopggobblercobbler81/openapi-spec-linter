# tls-cipher-scanner

Python CLI that audits SSL/TLS cipher suites and TLS protocol versions for domains or endpoints, flagging deprecated ciphers (RC4, 3DES, CBC mode ciphers) and old protocols (TLSv1.0, TLSv1.1).

## Installation

```bash
pip install .
```

## Usage

```bash
tls-cipher-scanner example.com
tls-cipher-scanner https://example.com:443 --json
```

## Testing

```bash
pytest
```
