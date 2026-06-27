#!/bin/sh
set -eu

ORION_URL=http://orion:1026
QL_URL=http://quantumleap:8668
SUB_URL=$ORION_URL/v2/subscriptions
SERVICE=iotmineracao
SERVICEPATH=/

printf '[orion-init] aguardando Orion...\n'
while ! curl -sSf "$ORION_URL/version" >/dev/null 2>&1; do
  sleep 2
  printf '.'
done
printf '\n[orion-init] Orion disponível. criando subscription...\n'

curl -s -X POST "$SUB_URL" \
  -H 'Content-Type: application/json' \
  -H "Fiware-Service: $SERVICE" \
  -H "Fiware-ServicePath: $SERVICEPATH" \
  -d '{
    "description": "Subscription to persist MineZone risk history in QuantumLeap",
    "subject": {
      "entities": [{ "idPattern": "Zona.*", "type": "MineZone" }],
      "condition": { "attrs": ["risco_atual"] }
    },
    "notification": {
      "http": {
        "url": "http://quantumleap:8668/v2/notify"
      },
      "attrs": ["risco_atual"],
      "metadata": ["timestamp"]
    },
    "throttling": 5
  }'

printf '[orion-init] subscription enviada para Orion.\n'