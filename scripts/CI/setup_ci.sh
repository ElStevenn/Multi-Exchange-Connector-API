#!/bin/bash






# Create ips handling file
if ! ls src/app | grep -q "ips_management.json"; then
    echo "{}" > src/security/ips_management.json
fi

# Create public and private keys



