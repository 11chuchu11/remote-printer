#!/bin/bash
set -e

ENV_FILE="$(dirname "$0")/../.env"

if [ ! -f "$ENV_FILE" ]; then
    echo "No se encontró .env en $ENV_FILE"
    exit 1
fi

current_ids=$(grep "^ALLOWED_USER_IDS=" "$ENV_FILE" | cut -d= -f2)
current_names=$(grep "^USER_NAMES=" "$ENV_FILE" | cut -d= -f2)
ids="$current_ids"
names="$current_names"

echo "Usuarios actuales: ${ids:-"(ninguno)"}"
echo "Ingresá IDs de usuario (-1 para terminar):"

while true; do
    read -rp "ID > " id
    [[ "$id" == "-1" ]] && break

    if ! [[ "$id" =~ ^[0-9]+$ ]]; then
        echo "  ID inválido, solo números."
        continue
    fi
    if [[ ",$ids," == *",$id,"* ]]; then
        echo "  $id ya existe."
        continue
    fi

    read -rp "Nombre (Enter para omitir) > " name

    ids="${ids:+$ids,}$id"
    echo "  Agregado: $id${name:+ ($name)}"

    if [ -n "$name" ]; then
        names="${names:+$names,}${id}:${name}"
    fi
done

tmp=$(mktemp)
grep -v "^ALLOWED_USER_IDS=" "$ENV_FILE" | grep -v "^USER_NAMES=" > "$tmp"
echo "ALLOWED_USER_IDS=$ids" >> "$tmp"
[ -n "$names" ] && echo "USER_NAMES=$names" >> "$tmp"
mv "$tmp" "$ENV_FILE"

echo ""
echo "Guardado."
echo "Aplicar: docker compose restart print-bot"
