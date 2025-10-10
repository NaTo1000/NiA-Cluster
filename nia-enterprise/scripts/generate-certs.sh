#!/bin/bash
# Generate self-signed certificates for development

set -e

CERTS_DIR="certs"
mkdir -p "$CERTS_DIR"

echo "Generating CA certificate..."
openssl req -x509 -newkey rsa:4096 -keyout "$CERTS_DIR/ca.key" -out "$CERTS_DIR/ca.crt" \
    -days 365 -nodes -subj "/CN=NiA-Enterprise-CA"

echo "Generating server certificate..."
openssl req -newkey rsa:4096 -keyout "$CERTS_DIR/server.key" -out "$CERTS_DIR/server.csr" \
    -nodes -subj "/CN=relay.nia-enterprise.local"

openssl x509 -req -in "$CERTS_DIR/server.csr" -CA "$CERTS_DIR/ca.crt" -CAkey "$CERTS_DIR/ca.key" \
    -CAcreateserial -out "$CERTS_DIR/server.crt" -days 365

echo "Generating client certificate..."
openssl req -newkey rsa:4096 -keyout "$CERTS_DIR/client.key" -out "$CERTS_DIR/client.csr" \
    -nodes -subj "/CN=client.nia-enterprise.local"

openssl x509 -req -in "$CERTS_DIR/client.csr" -CA "$CERTS_DIR/ca.crt" -CAkey "$CERTS_DIR/ca.key" \
    -CAcreateserial -out "$CERTS_DIR/client.crt" -days 365

# Clean up CSR files
rm -f "$CERTS_DIR"/*.csr

echo "Certificates generated in $CERTS_DIR/"
ls -la "$CERTS_DIR"

echo ""
echo "Certificate generation complete!"
echo "Use these certificates for TLS/mTLS configuration."
