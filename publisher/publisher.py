#!/usr/bin/env python3
import json
import os
import random
import signal
import time
import paho.mqtt.client as mqtt

MQTT_HOST = os.getenv('MQTT_HOST', 'localhost')
MQTT_PORT = int(os.getenv('MQTT_PORT', '1883'))
PUBLISH_INTERVAL = float(os.getenv('PUBLISH_INTERVAL', '4.0'))
ZONES = ['A', 'B', 'C', 'D', 'E']

BASE_VALUES = {
    'temperatura': 30.0,
    'fumaca': 10.0,
    'gas': 7.0,
    'umidade': 50.0,
    'ventilacao': 10.0,
}

EVENT_DURATION = 40
EVENT_COOLDOWN = 100

running = True
active_event = None
last_event_at = time.time() - EVENT_COOLDOWN


def signal_handler(signum, frame):
    global running
    running = False
    print('\n[publisher] encerrando...')


def compute_value(base, amplitude, trend=0.0):
    return round(max(0.0, base + random.uniform(-amplitude, amplitude) + trend), 1)


def build_measurement(zone, event_strength):
    temperature = compute_value(BASE_VALUES['temperatura'], 3.0, event_strength * 0.9)
    smoke = compute_value(BASE_VALUES['fumaca'], 4.0, event_strength * 1.4)
    gas = compute_value(BASE_VALUES['gas'], 2.5, event_strength * 1.2)
    humidity = compute_value(BASE_VALUES['umidade'], 5.5, -event_strength * 0.5)
    ventilation = compute_value(BASE_VALUES['ventilacao'], 2.5, -event_strength * 0.4)

    return {
        'temperatura': temperature,
        'fumaca': smoke,
        'gas': gas,
        'umidade': humidity,
        'ventilacao': ventilation,
    }


def calculate_risk(measurement):
    return round(
        measurement['temperatura']
        + measurement['fumaca']
        + measurement['gas']
        - measurement['umidade']
        - measurement['ventilacao'],
        2,
    )


def get_risk_level(risk_value):
    if risk_value >= 60:
        return 'critico'
    if risk_value >= 45:
        return 'alto'
    if risk_value >= 30:
        return 'moderado'
    return 'baixo'


def main():
    global active_event, last_event_at

    client = mqtt.Client(client_id='iot-mine-publisher')
    client.connect(MQTT_HOST, MQTT_PORT, 60)
    client.loop_start()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    print(f'[publisher] conectando em mqtt://{MQTT_HOST}:{MQTT_PORT}')

    while running:
        now = time.time()

        if active_event is None and now - last_event_at > EVENT_COOLDOWN:
            active_event = {
                'zone': random.choice(ZONES),
                'start': now,
                'duration': EVENT_DURATION,
                'strength': random.uniform(12.0, 20.0),
            }
            print(f'[publisher] iniciado evento de risco progressivo na zona {active_event["zone"]}')

        if active_event and now - active_event['start'] > active_event['duration']:
            print(f'[publisher] evento de risco finalizado na zona {active_event["zone"]}')
            active_event = None
            last_event_at = now

        for zone in ZONES:
            event_strength = 0.0
            if active_event and zone == active_event['zone']:
                event_progress = min(1.0, (now - active_event['start']) / active_event['duration'])
                event_strength = active_event['strength'] * event_progress

            measurement = build_measurement(zone, event_strength)
            risk_value = calculate_risk(measurement)
            risk_level = get_risk_level(risk_value)

            payload = {
                'zona': zone,
                'temperatura': measurement['temperatura'],
                'fumaca': measurement['fumaca'],
                'gas': measurement['gas'],
                'umidade': measurement['umidade'],
                'ventilacao': measurement['ventilacao'],
                'risco_estimado': risk_value,
                'nivel_risco': risk_level,
                'timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
            }

            topic = f'mina/zona{zone}/sensores'
            client.publish(topic, json.dumps(payload), qos=0)
            print(f'[publisher] {topic} -> {json.dumps(payload)}')

        time.sleep(PUBLISH_INTERVAL)

    client.loop_stop()
    client.disconnect()


if __name__ == '__main__':
    main()
