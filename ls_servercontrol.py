#!/usr/bin/python

###### CONFIGURE FIRST ######

# The Pins. Use Broadcom numbers.
RED_PIN   = 16
GREEN_PIN = 20
BLUE_PIN  = 21


###### CONFIGURE ENDS ######

import os
import sys
import termios
import tty
import pigpio
import time
import MySQLdb

pi = pigpio.pi()
bright = 255

def setLights(pin, brightness):
	realBrightness = int(int(brightness) * (float(bright) / 255.0))
	pi.set_PWM_dutycycle(pin, realBrightness)
	
while True:
	# Open database connection
	db = MySQLdb.connect("localhost","root","raspberry","Ledstrip" ) #LOCALHOST SHALL BE REPLACED BY NORMAL IPV4-ADDRESS

	# prepare a cursor object using cursor() method
	cursor = db.cursor()

	# Execute the SQL command
	cursor.execute("SELECT * FROM Color order by Id desc limit 1")
	# Fetch all the rows in a list of lists.
	for row in cursor.fetchall():
		g = row[1]
		r = row[2]
		b = row[3]
		
		setLights(RED_PIN, r)
		setLights(GREEN_PIN, g)
		setLights(BLUE_PIN, b)

	# disconnect from server
	db.close()
	
pi.stop()