from datetime import datetime
from requests.auth import HTTPBasicAuth
import paho.mqtt.client as mqtt
import os
import re
import sys
import time
import json
import random
import requests
import signal
import subprocess
import configparser

from amcrest import Http
	
def on_connect(client,userdata,flags,rc):
    if rc==0:
        print("Connected to MQTT...")
        client.connected_flag=True

def on_disconnect(client,userdata,rc):
    print("Disconnecting reason "+str(rc))
    client.connected_flag=False
    client.disconnect_flag=True
	
def sigterm_handler(signal, frame):
	print('Exiting...')
#	ret.close()
	client.disconnect()
	client.loop_stop()
	sys.exit(0)

def lines(ret):
	line = ''
	for char in ret.iter_content(decode_unicode=True):
		line = line + char
		if line.endswith('\r\n'):
			yield line.strip()
			line = ''

signal.signal(signal.SIGTERM, sigterm_handler)

# Mike Yaeger's Original Defines
camera = os.environ['CAMERA']
config = configparser.ConfigParser()
config.read('/config/'+camera+'.conf')
user = config['camera']['user']
pswd = config['camera']['password']
host = config['camera']['address']
port = config['camera']['port']
ad110 = config.getboolean('camera','ad110')
basetopic = config['mqtt']['topic']
biurl = "http://"+config['blueiris']['address']+":"+config['blueiris']['port']
bicred = "user="+config['blueiris']['user']+"&pw="+config['blueiris']['password']
broker_address = config['mqtt']['address']
client.username_pw_set(username=config['mqtt']['user'],password=config['mqtt']['password'])
client = mqtt.Client(config['camera']['name']+str(int(random.random()*100)))

client.connected_flag=False
client.on_connect=on_connect
client.connect(broker_address)
client.loop_start()
while not client.connected_flag:
    time.sleep(1)


if ad110:
	cam = Http(host, port, user, pswd, retries_connection=1, timeout_protocol=3.05)
	ret = cam.command('configManager.cgi?action=setConfig&Lighting[0] [0].Mode=Off', timeout_cmd=(3.05, None), stream=False)
	if ret.status_code == requests.codes.ok:
		print("Night Vision Disabled...")

def main():
	global config, camera, user, pswd, host, port, ad110, biurl, bicred

	cam = Http(host, port, user, pswd, retries_connection=1, timeout_protocol=3.05)
#	ret = cam.command('eventManager.cgi?action=attach&codes=[VideoMotion, CrossLineDetection, CrossRegionDetection, _DoTalkAction_]', timeout_cmd=(3.05, None), stream=True) # Will pull just these events
	ret = cam.command('eventManager.cgi?action=attach&codes=[All]', timeout_cmd=(3.05, None), stream=True)
	ret.encoding = 'utf-8'

	for line in lines(ret):
		code   = ''
		action = ''
		index = ''
		QOS = 2
		m = re.search('Code=(.*?);', line)
		if m:
			line = line.replace('\n', '')
			print("-----")
			print(line)
			print("-----")
			code = m.group(1)

		m2 = re.search('action=(.*?);', line)
		if m2:
			action = m2.group(1)
		m3 = re.search('index=(.*?);', line)
		if m3:
			index = m3.group(1)
		m4 = re.search(';data={(.*)}', line, flags = re.S)
		if m4:
			data = m4.group(1).replace('\n', '')
			data = f'{{ {data} }}'
			obj = json.loads(data)

		if code == '_DoTalkAction_':
			print("-----")
			print(line)
			print("-----")
			print(obj['Action'])
			if obj['Action'] == 'Invite':
				print("Button Pressed")
				client.publish(basetopic+'/'+camera+'/button','on',QOS,False)
			elif obj['Action'] == 'Hangup':
				print("Button Cancelled")
				client.publish(basetopic+'/'+camera+'/button','off',QOS,False)

		elif code == 'AlarmLocal':
##			global recording
			if action == 'Start':
				print(datetime.now().replace(microsecond=0),' - Doorbell Motion Start')
			elif action == 'Stop':
				print(datetime.now().replace(microsecond=0),' - Doorbell Motion Stop')

		elif code == 'VideoMotion' and not ad110:
			if action == 'Start':
				print(datetime.now().replace(microsecond=0),' - Motion Start')
			elif action == 'Stop':
				print(datetime.now().replace(microsecond=0),' - Motion Stop')

		elif code == 'CrossLineDetection':
			if action == 'Start':
				print(datetime.now().replace(microsecond=0),' - Intrusion Start ('+obj['Name']+')')
#				response = requests.get(biurl+"/admin?camera="+camera+"&trigger&flagalert=1&"+bicred)#memo=IVS&"+bicred)
				client.publish(basetopic+'/'+camera+'/ivs/'+obj['Name'],'on',QOS,False)
			elif action == 'Stop':
				print(datetime.now().replace(microsecond=0),' - Intrusion Stop ('+obj['Name']+')')
				client.publish(basetopic+'/'+camera+'/ivs/'+obj['Name'],'off',QOS,False)

		elif code == 'CrossRegionDetection':
			if action == 'Start':
				print(datetime.now().replace(microsecond=0),' - Region Start ('+obj['Name']+')')
#				response = requests.get(biurl+"/admin?camera="+camera+"&trigger&flagalert=1&"+bicred)#memo=IVS&"+bicred)
				client.publish(basetopic+'/'+camera+'/ivs/'+obj['Name'],'on',QOS,False)
			elif action == 'Stop':
				print(datetime.now().replace(microsecond=0),' - Region Stop ('+obj['Name']+')')
				client.publish(basetopic+'/'+camera+'/ivs/'+obj['Name'],'off',QOS,False)

if __name__ == '__main__':
	main()

