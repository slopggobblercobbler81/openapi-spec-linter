import os
import sys
import ssl
import socket
import argparse
import json
from urllib.parse import urlparse

DEPRECATED_PROTOCOLS = {
    ssl.TLSVersion.TLSv1: "TLSv1.0 (Deprecated)",
    ssl.TLSVersion.TLSv1_1: "TLSv1.1 (Deprecated)",
}

SECURE_PROTOCOLS = {
    ssl.TLSVersion.TLSv1_2: "TLSv1.2 (Secure)",
    ssl.TLSVersion.TLSv1_3: "TLSv1.3 (Secure)",
}

INSECURE_CIPHER_TERMS = ["RC4", "DES", "RC2", "MD5", "NULL", "EXPORT", "anon"]

def check_cipher_security(cipher_name):
    upper_name = cipher_name.upper()
    issues = []
    if "CBC3" in upper_name or "3DES" in upper_name:
        issues.append("Weak/Deprecated cipher term: 3DES")
    for term in INSECURE_CIPHER_TERMS:
        if term in upper_name:
            issues.append(f"Weak/Deprecated cipher term: {term}")
    if "CBC" in upper_name and "AEAD" not in upper_name:
        issues.append("CBC mode cipher (potential padding oracle): CBC")
    return issues

def scan_endpoint(host, port=443, timeout=5.0):
    results = {
        "host": host,
        "port": port,
        "supported_protocols": {},
        "deprecated_protocols_found": [],
        "ciphers": [],
        "vulnerabilities": []
    }

    protocols_to_test = [
        (ssl.TLSVersion.TLSv1, "TLSv1.0"),
        (ssl.TLSVersion.TLSv1_1, "TLSv1.1"),
        (ssl.TLSVersion.TLSv1_2, "TLSv1.2"),
        (ssl.TLSVersion.TLSv1_3, "TLSv1.3"),
    ]

    for proto_version, proto_name in protocols_to_test:
        context = ssl.create_default_context()
        context.minimum_version = proto_version
        context.maximum_version = proto_version
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE

        try:
            with socket.create_connection((host, port), timeout=timeout) as sock:
                with context.wrap_socket(sock, server_hostname=host) as ssock:
                    results["supported_protocols"][proto_name] = True
                    if proto_version in DEPRECATED_PROTOCOLS:
                        results["deprecated_protocols_found"].append(proto_name)
                        results["vulnerabilities"].append(f"Supports deprecated protocol: {proto_name}")
        except Exception:
            results["supported_protocols"][proto_name] = False

    try:
        context = ssl.create_default_context()
        context.minimum_version = ssl.TLSVersion.TLSv1_2
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE

        with socket.create_connection((host, port), timeout=timeout) as sock:
            with context.wrap_socket(sock, server_hostname=host) as ssock:
                cipher = ssock.cipher()
                if cipher:
                    cipher_name = cipher[0]
                    results["ciphers"].append({
                        "name": cipher_name,
                        "version": cipher[1],
                        "bits": cipher[2]
                    })
                    issues = check_cipher_security(cipher_name)
                    for issue in issues:
                        results["vulnerabilities"].append(f"Cipher {cipher_name}: {issue}")
    except Exception as e:
        results["vulnerabilities"].append(f"Failed to retrieve active cipher: {str(e)}")

    return results

def main():
    parser = argparse.ArgumentParser(description="Audit SSL/TLS cipher suites and protocol versions.")
    parser.add_argument("target", help="Domain name or URL to scan")
    parser.add_argument("-p", "--port", type=int, default=443, help="Port to scan (default: 443)")
    parser.add_argument("--json", action="store_true", help="Output results in JSON format")
    args = parser.parse_args()

    target = args.target
    if "://" in target:
        parsed = urlparse(target)
        host = parsed.hostname
        port = parsed.port or args.port
    else:
        host = target
        port = args.port

    if not host:
        print(f"Error: Invalid target {target}", file=sys.stderr)
        sys.exit(1)

    print(f"Scanning {host}:{port} for TLS protocols and ciphers...")
    results = scan_endpoint(host, port)

    if args.json:
        print(json.dumps(results, indent=2))
    else:
        print("\n--- Scan Results ---")
        print(f"Target: {results['host']}:{results['port']}")
        print("\nSupported Protocols:")
        for proto, supported in results["supported_protocols"].items():
            status = "SUPPORTED" if supported else "Not supported"
            print(f"  - {proto}: {status}")

        print("\nActive Cipher:")
        if results["ciphers"]:
            for c in results["ciphers"]:
                print(f"  - Name: {c['name']} ({c['version']}, {c['bits']} bits)")
        else:
            print("  - None retrieved")

        print("\nVulnerabilities / Flags:")
        if results["vulnerabilities"]:
            for v in results["vulnerabilities"]:
                print(f"  [!] {v}")
        else:
            print("  [+] No deprecated protocols or weak ciphers flagged.")

if __name__ == "__main__":
    main()
