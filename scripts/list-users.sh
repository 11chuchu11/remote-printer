#!/bin/bash

ENV_FILE="$(dirname "$0")/../.env"

if [ ! -f "$ENV_FILE" ]; then
    echo "No se encontró .env en $ENV_FILE"
    exit 1
fi

current=$(grep "^ALLOWED_USER_IDS=" "$ENV_FILE" | cut -d= -f2)

if [ -z "$current" ]; then
    echo "No hay usuarios configurados."
    exit 0
fi

echo "Usuarios permitidos:"
echo "$current" | tr ',' '\n' | nl -ba
