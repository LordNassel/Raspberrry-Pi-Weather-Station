import sys
import subprocess
import re
import os
import time
import MySQLdb as mdb
import datetime
import Adafruit_BMP.BMP085 as BMP085

sensor = BMP085.BMP085()


dbip="localhost"
databaseUsername="root"
databasePassword="raspberry"
databaseName="WeatherStation"

con=mdb.connect(dbip, databaseUsername, databasePassword, databaseName)

while True:
	legnyomas = sensor.read_pressure()
	homerseklet = sensor.read_temperature()
	with con:
		cur=con.cursor()
		cur.execute("INSERT INTO rpi (pressure,temperature) VALUES (%s,%s)",(legnyomas,homerseklet))
		
	print 'Temp = {0:0.2f} *C'.format(sensor.read_temperature()) # Temperature in Celcius
	print 'Pressure = {0:0.2f} Pa'.format(sensor.read_pressure()) # The local pressure
	print 'Altitude = {0:0.2f} m'.format(sensor.read_altitude()) # The current altitude
	print 'Sealevel Pressure = {0:0.2f} Pa'.format(sensor.read_sealevel_pressure()) # The sea-level pressure	
	print '\n'
	print '\n'
	time.sleep(10)