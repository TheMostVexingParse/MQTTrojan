import zlib
from base64 import urlsafe_b64encode as b64e, urlsafe_b64decode as b64d
import random
import time

from paho.mqtt import client as mqtt_client


broker = 'broker.emqx.io'
port = 1883
topic = "5A7134743777217A25432A462D4A614E"

client_id = f'server-{random.randint(0, 10000000)}'
username = 'emqx'
password = 'public'

encryption_key = 'JaNcRfUjXn2r5u8x/A?D(G+KbPeSgVkY'
prev_key = encryption_key
ascii_table = ''.join([chr(i) for i in range(33,128)])

def sample(table, len_):
    copied = list(table)
    random.shuffle(copied)
    return ''.join(copied[:len_])

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

def connect_mqtt():
    def on_connect(client, userdata, flags, rc):
        if rc == 0: print("Connected to MQTT Broker!")
        else: print("Failed to connect, return code %d\n", rc)

    client = mqtt_client.Client(client_id)
    client.username_pw_set(username, password)
    client.on_connect = on_connect
    client.connect(broker, port)
    return client

wait_until = False

def publish(client):
    global wait_until, encryption_key, prev_key
    while True:
        while wait_until:
            pass
        print('', end='')
        inp = input('\n>>>')
        new_key = encryption_key
        if inp.startswith('lock to'):
            inp = inp.split('lock to')[-1].strip()
            new_key = sample(ascii_table, 32)
            inp = 'cli:'+inp+'€'+new_key
        elif inp.startswith('release'):
            encryption_key = prev_key
        msg = 'server: '+inp
        msg = shift_by(msg, encryption_key)
        encryption_key = new_key
        result = client.publish(topic, msg)
        wait_until = True
        status = result[0]
        if status != 0: print(f"Failed to send message to topic {topic}")

    
def run():
    def on_message(client, userdata, msg):
        global wait_until, encryption_key, prev_key
        payload = msg.payload.decode()
        payload = reverse_shift(payload, encryption_key)
        if payload.startswith('server:'): return None
        payload = payload.split('client:')[-1].strip()
        if payload != '':
            print(payload)
        wait_until = False
    
    client = connect_mqtt()
    time.sleep(2)
    client.subscribe(topic)
    client.on_message = on_message
    client.loop_start()
    publish(client)
    client.loop_forever()
    

if __name__ == '__main__':
    run()
