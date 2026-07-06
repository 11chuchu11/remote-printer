#!/bin/bash
set -e

ENV_FILE="$(dirname "$0")/../.env"

if [ ! -f "$ENV_FILE" ]; then
    echo "No se encontró .env en $ENV_FILE"
    exit 1
fi

current_ids=$(grep "^ALLOWED_USER_IDS=" "$ENV_FILE" | cut -d= -f2)
current_names=$(grep "^USER_NAMES=" "$ENV_FILE" | cut -d= -f2)

echo "Usuarios actuales: ${current_ids:-"(ninguno)"}"
read -rp "ID a eliminar: " id

if ! [[ "$id" =~ ^[0-9]+$ ]]; then
    echo "ID inválido."
    exit 1
fi

if [[ ",$current_ids," != *",$id,"* ]]; then
    echo "Usuario $id no encontrado."
    exit 1
fi

new_ids=$(echo "$current_ids" | tr ',' '\n' | grep -v "^${id}$" | paste -sd ',')
new_names=$(echo "$current_names" | tr ',' '\n' | grep -v "^${id}:" | paste -sd ',')

tmp=$(mktemp)
grep -v "^ALLOWED_USER_IDS=" "$ENV_FILE" | grep -v "^USER_NAMES=" > "$tmp"
echo "ALLOWED_USER_IDS=$new_ids" >> "$tmp"
[ -n "$new_names" ] && echo "USER_NAMES=$new_names" >> "$tmp"
mv "$tmp" "$ENV_FILE"

echo "Removido: $id"
echo "Aplicar: docker compose restart print-bot"
