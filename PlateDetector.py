import time
import RPi.GPIO as GPIO
import SpectralSensor as ss
import ProximitySensor as ps
from threading import Thread
import queue
import Servo as servo
import numpy as np
import pickle

GPIO.setmode(GPIO.BCM)

class PlateDetector():

	def __init__(self,mode='Train'):

		self.s = ss.SpectralSensor()
		self.p = ps.ProximitySensor()
		self.interruptPin = 17
		self.mode = 'Train'
		self.resultQueue = queue.Queue()
		self.p.setHighThreshold(10000)
		GPIO.setup(self.interruptPin,GPIO.IN,pull_up_down=GPIO.PUD_UP)
		GPIO.add_event_detect(self.interruptPin,GPIO.FALLING,callback=self.sensorEvent)
		self.p.setInterrupt(1)
		#Loading dict from pickle file if it exists, else init new dict
    	
		self.refValues = self.load()

	def autoScanning(self):
		pass

	def train(self,c):
		val = pd.getResult()
		if c not in self.refValues.keys():
			self.refValues[c] = (val,1)
		else:
			(q,n) = self.refValues[c]
			newVal = q + (1/(n+1))*(val-q)
			self.refValues[c] = (newVal,n+1)




	def sensorEvent(self,pin):
		# Read Sensor and Store in Queue
		self.s.ledDrv(1)
		self.s.setBank(3)
		r = self.s.readAllCal()
		self.resultQueue.put_nowait(r)
		self.s.ledDrv(0)
		
		# Open and Close to release plate
		servo.open()
		time.sleep(0.1)
		servo.close()

		# Reset Interrupt on Proximity Sensor
		GPIO.remove_event_detect(self.interruptPin)
		self.p.setInterrupt(0)
		GPIO.add_event_detect(self.interruptPin,GPIO.FALLING,callback=self.sensorEvent)
		self.p.setInterrupt(1)

	def getResult(self):
		return self.resultQueue.get(block=True)

	def evalColour(self,val):
		minError  = np.inf
		minColour = None
		for c in self.refValues.keys():
			(ref,n) = self.refValues[c]
			error = np.mean(((val-ref)**2))
			if(error < minError):
				minError = error
				minColour = c
		return minColour

	def store(self):
		try:
			pickle.dump(self.refValues, open("data.pickle", "wb"))
		except Exception as e:
			print("Error :" + str(e))

	def load(self):
		try:
			colourdict= pickle.load(open("data.pickle", "rb"))
			return colourdict
		except Exception as e:
			colourdict =  {} 
			return colourdict



count = 0
pd = PlateDetector()
while(True):
	try:
		for i in range(0,2,1):
			pd.train("Orange")
		for i in range(0,2,1):
			pd.train("Blue")
		for i in range(0,2,1):
			pd.train("White")
		for i in range(0,2,1):
			pd.train("Pink")

		pd.store()

		print(pd.evalColour(pd.getResult())) 		

		print(pd.refValues)
	except Exception as e:
		print("Error : " + str(e))
		GPIO.cleanup()




'''
s = ss.SpectralSensor()
p = ps.ProximitySensor()


while(1):
        reading = p.readProximity()
         if(reading > 10000):
                s.ledDrv(1)
                s.setBank(3)
                r = s.readAllCal()
                s.ledDrv(0)
                print(r)
                dictData = {'sensorReadings':r}
                payload = json.dumps(dictData)
                MSG_INFO = client.publish("IC.Embedded/IOS/"+tableID,payload)
        time.sleep(0.1)
'''
