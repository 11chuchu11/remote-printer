#!/bin/bash
set -e

ENV_FILE="$(dirname "$0")/../.env"

if [ ! -f "$ENV_FILE" ]; then
    echo "No se encontró .env en $ENV_FILE"
    exit 1
fi

current_ids=$(grep "^ALLOWED_USER_IDS=" "$ENV_FILE" | cut -d= -f2)
current_names=$(grep "^USER_NAMES=" "$ENV_FILE" | cut -d= -f2)

if [ -z "$current_ids" ]; then
    echo "No hay usuarios configurados."
    exit 0
fi

get_name() {
    echo "$current_names" | tr ',' '\n' | grep "^${1}:" | cut -d: -f2
}

echo "Usuarios actuales:"
i=1
while IFS= read -r uid; do
    name=$(get_name "$uid")
    if [ -n "$name" ]; then
        echo "  $i. $uid ($name)"
    else
        echo "  $i. $uid"
    fi
    ((i++))
done < <(echo "$current_ids" | tr ',' '\n')

echo ""
read -rp "ID a editar: " id

if ! [[ "$id" =~ ^[0-9]+$ ]]; then
    echo "ID inválido."
    exit 1
fi

if [[ ",$current_ids," != *",$id,"* ]]; then
    echo "Usuario $id no encontrado."
    exit 1
fi

current_name=$(get_name "$id")
read -rp "Nuevo nombre${current_name:+ (actual: $current_name)} (Enter para quitar): " new_name

new_names=$(echo "$current_names" | tr ',' '\n' | grep -v "^${id}:" | paste -sd ',')
[ -n "$new_name" ] && new_names="${new_names:+$new_names,}${id}:${new_name}"

tmp=$(mktemp)
grep -v "^USER_NAMES=" "$ENV_FILE" > "$tmp"
[ -n "$new_names" ] && echo "USER_NAMES=$new_names" >> "$tmp"
mv "$tmp" "$ENV_FILE"

if [ -n "$new_name" ]; then
    echo "Nombre actualizado: $id → $new_name"
else
    echo "Nombre removido para: $id"
fi
echo "Aplicar: docker compose restart print-bot"
