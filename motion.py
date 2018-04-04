import RPi.GPIO as GPIO
import time
import MySQLdb
import datetime
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD)
GPIO.setup(11, GPIO.IN)         #Read output from PIR motion sensor

while True:
	i=GPIO.input(11)
	if i==0:                 #When output from motion sensor is LOW
		print "Ready",i
		#GPIO.output(3, 0)  #Turn OFF LED
		time.sleep(0.1)
	elif i==1:               #When output from motion sensor is HIGH
		print "Motion detected!",i
		status = " Motion detected!"
		#GPIO.output(3, 1)  #Turn ON LED
		con = MySQLdb.connect(host="localhost", user="root", passwd="raspberry", db="WeatherStation")
		cur = con.cursor()
		cur.execute("INSERT INTO motion(motion,datetime) VALUES (%s, %s)",(status, datetime.datetime.now()))
		con.commit()
		time.sleep(0.1)