#!/bin/bash
set -e

ENV_FILE="$(dirname "$0")/../.env"

if [ ! -f "$ENV_FILE" ]; then
    echo "No se encontró .env en $ENV_FILE"
    exit 1
fi

current=$(grep "^ALLOWED_USER_IDS=" "$ENV_FILE" | cut -d= -f2)
ids="$current"

echo "Usuarios actuales: ${ids:-"(ninguno)"}"
echo "Ingresá IDs de usuario (-1 para terminar):"

while true; do
    read -rp "> " id
    [[ "$id" == "-1" ]] && break
    if ! [[ "$id" =~ ^[0-9]+$ ]]; then
        echo "  ID inválido, solo números."
        continue
    fi
    if [[ ",$ids," == *",$id,"* ]]; then
        echo "  $id ya existe."
        continue
    fi
    ids="${ids:+$ids,}$id"
    echo "  Agregado: $id"
done

tmp=$(mktemp)
grep -v "^ALLOWED_USER_IDS=" "$ENV_FILE" > "$tmp"
echo "ALLOWED_USER_IDS=$ids" >> "$tmp"
mv "$tmp" "$ENV_FILE"

echo ""
echo "Guardado. Usuarios: $ids"
echo "Aplicar: docker compose restart print-bot"
