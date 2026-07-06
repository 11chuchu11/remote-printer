#!/bin/bash

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

echo "Usuarios permitidos:"
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
