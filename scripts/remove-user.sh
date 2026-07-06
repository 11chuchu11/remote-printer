#!/bin/bash
set -e

ENV_FILE="$(dirname "$0")/../.env"

if [ ! -f "$ENV_FILE" ]; then
    echo "No se encontró .env en $ENV_FILE"
    exit 1
fi

current=$(grep "^ALLOWED_USER_IDS=" "$ENV_FILE" | cut -d= -f2)

echo "Usuarios actuales: ${current:-"(ninguno)"}"
read -rp "ID a eliminar: " id

if ! [[ "$id" =~ ^[0-9]+$ ]]; then
    echo "ID inválido."
    exit 1
fi

if [[ ",$current," != *",$id,"* ]]; then
    echo "Usuario $id no encontrado."
    exit 1
fi

new=$(echo "$current" | tr ',' '\n' | grep -v "^${id}$" | paste -sd ',')

tmp=$(mktemp)
grep -v "^ALLOWED_USER_IDS=" "$ENV_FILE" > "$tmp"
echo "ALLOWED_USER_IDS=$new" >> "$tmp"
mv "$tmp" "$ENV_FILE"

echo "Removido: $id"
echo "Usuarios restantes: ${new:-"(ninguno)"}"
echo "Aplicar: docker compose restart print-bot"
