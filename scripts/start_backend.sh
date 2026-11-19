#!/bin/bash

set -e

cd "$(dirname "$0")/.."

python3 scripts/init_database.py

export CRYPTOGRAPHY_OPENSSL_NO_LEGACY=1

python3 -m backend.app

