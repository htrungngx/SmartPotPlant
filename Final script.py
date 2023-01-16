
import time
import board
import adafruit_dht
import random
import sys
import RPi.GPIO as GPIO
import serial
import re
from GroveLightSensor import GroveLightSensor
from Adafruit_IO import RequestError, Client, Feed

GPIO.setmode(GPIO.BCM)

#setup adafruit 
ADAFRUIT_IO_USERNAME = 'cyrilmetropolia' 
ADAFRUIT_IO_KEY = 'aio_FLVx78zG4clK1mH3fstd8ZOVEWO1' #Token key for Ada Dashboard
aio = Client(ADAFRUIT_IO_USERNAME, ADAFRUIT_IO_KEY)
        
      
try:
        tempC = aio.feeds('temperature-in-c')
        tempF = aio.feeds('temperature-in-f')
        humidity = aio.feeds('humidity')
        light = aio.feeds('light')
        moisture = aio.feeds('moisture')
except RequestError:
        tempC = aio.create_feed('temperature In C')
        tempF = aio.create_feed('temperature-in-f')
        humidity = aio.create_feed('humidity')
        light = aio.create_feed('light')
        moisture = aio.create_feed('moisture')
        


Relay_GPIO = 21 #PIN for Relay
#Initial pin and voltage for relay
#Function for pumper
def PumperOn():
                GPIO.setup(Relay_GPIO, GPIO.OUT) #Initial GPIO 21
                GPIO.output(Relay_GPIO, GPIO.HIGH) #Turn Relay On
                print("Plant is watering")
                time.sleep(5) #Turn on in 5 seconds
                GPIO.output(Relay_GPIO, GPIO.LOW) #Turn Relay Off
                print("Watering is finished")
                        
#Function for Temp and Humid 
def getTemp_Humid():
        values = []
        #try-except block needed, because sensor is weird and sometimes sends no data
        while True:
                try:
                        dhtDevice = adafruit_dht.DHT22(board.D17, use_pulseio=False) #Initial Lirary and PIN for Temp/Humid Sensor (Digital PIN 17)
                        temperature_c = dhtDevice.temperature #Read Temperature in C unit
                        temperature_f = temperature_c * (9 / 5) + 32 #Converting to F uni
                        humidity = dhtDevice.humidity #Read Humidity value
                        values.append(temperature_c) #Send value to array
                        values.append(temperature_f)
                        values.append(humidity)                              
                        print("Temp: {:.1f} F / {:.1f} C    Humidity: {}% ".format(temperature_f, temperature_c, humidity)) #Print values
                 
                except RuntimeError:
                        break
                       
        #time.sleep(10) #Sleep 10 sec before the next scan
        return values
       
       
#Function for light sensor   
def getLightSensor():
        channel = 0 #Inital at Port A0 ( Board extention )
         
        sensor = GroveLightSensor(channel); #Read value from sensor
         
        #print('Detecting light...') #Print Light value ( "ln" unit )
        print('Light value: {0}'.format(sensor.light))
        
        #time.sleep(5) #Sleep 5 before the next scanning
        
        #return needed, because otherwise the function returns no data and then we cant send the data
        return sensor.light
        

        
        
        
#Function for moisture sensor
def getMoistureSensor():
        ser = serial.Serial('/dev/ttyUSB0', 9600) #Initial to read Moisture Sensor from Arduino at USB0 port
        ser.flush() #Clear cache 
        moisture_value = 0
        while True: 
                try:
                        if ser.in_waiting > 0:
                                line = ser.readline().decode('utf-8').rstrip() # Read value and Decode data
                                print(line) #It will print "Moisture: value %"
                                moisture_value = re.findall("-?\d+",line) #Filtered value only
                                if len(moisture_value) == 1:
                                        moisture_value = moisture_value[0]
                                        moisture_value = int(moisture_value) #convert value as an integer
                                        if moisture_value < 0: #If value < 0, I am not sure it should be < 0 or something else to trigger pumper
                                                print("Plant need water")
                                                PumperOn()
                                                
                                        else: #if bigger. Dont need to water plant
                                                print("Plant is full")
                                        break #to get out of the while loop, otherwise its stuck in here
                                
                except serial.serialutil.SerialException:
                        pass
                
        #return value so it can be sent to adafruit                 
        return moisture_value                






#Main function
if __name__ == '__main__':
        #while loop so our program doesnt stop after going through the main one time
        while True:
 
                #send temp/humidity values to adafruit
                tempHumid = getTemp_Humid()
                if not tempHumid:
                        print("list is empty")
                else:
                        aio.send_data(tempC.key, tempHumid[0])
                        aio.send_data(tempF.key, tempHumid[1])
                        aio.send_data(humidity.key, tempHumid[2])
                        #print("sent dht sensor data!")
                aio.send_data(light.key, getLightSensor())
                        
                #send moisture data to adafruit 
                moistureData = getMoistureSensor()
                time.sleep(3)
                if not moistureData or moistureData == 0:
                        print("list is empty")
                else:
                        aio.send_data(moisture.key, getMoistureSensor()) 
                        #print("sent moisture data!") 
                print(moistureData)

                
                time.sleep(4) #so we dont exceed the adafruit request limit so fast
