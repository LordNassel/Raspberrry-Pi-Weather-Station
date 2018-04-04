#!/usr/bin/python
import MySQLdb
import subprocess
import re
import sys
import time
import datetime
import Adafruit_DHT

# Open database connection
conn = MySQLdb.connect("localhost","root","raspberry","WeatherStation")

# Continuously append data
while(True):

	date = time.strftime("%d/%m/%Y")
	clock = time.strftime("%H:%M")
	
	humidity, temperature = Adafruit_DHT.read_retry(11, 4)
	print 'Temp: {0:0.1f} C  Humidity: {1:0.1f} %'.format(temperature, humidity)
	
	# MYSQL DATA Processing
	c = conn.cursor()

	c.execute("INSERT INTO data_th (datetime, temperature, hum) VALUES (%s, %s, %s)",(datetime.datetime.now(), temperature, humidity))
	conn.commit()
	print "Data Base Loaded"

	time.sleep(60)