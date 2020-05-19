# Light three different LEDs based on temperature level (high, medium, low) (GPIO9, GPIO8, GPIO7)
# Measuring Temp on Raspberry with a 1K thermistor of beta 3800, 330nF capacitor and two resistors of 1K Ohms resistance

import RPi.GPIO as GPIO
import math
import time
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(7, GPIO.OUT)
GPIO.setup(8, GPIO.OUT)
GPIO.setup(9, GPIO.OUT)


class ADC:
    pin1 = 18
    pin2 = 23
    C = 0.0
    R1 = 0.0
    Vt = 0.0
    Vs = 0.0
    T5 = 0.0

    def __init__(self, C=0.33, R1=1000.0, Vt=1.346, Vs=3.25):
        self.C = C
        self.R1 = R1
        self.Vt = Vt
        self.Vs = Vs
        self.T5 = (C * R1 * 5) / 1000000.0

    # empty the capacitor ready to start filling it up
    def discharge(self):
        GPIO.setup(self.pin1, GPIO.IN)
        GPIO.setup(self.pin2, GPIO.OUT)
        GPIO.output(self.pin2, False)
        time.sleep(self.T5)  # 5T for 99% discharge

    # return the time taken for the voltage on the capacitor to count as a digital input HIGH
    def charge_time(self):
        GPIO.setup(self.pin2, GPIO.IN)
        GPIO.setup(self.pin1, GPIO.OUT)
        GPIO.output(self.pin1, True)
        t1 = time.time()
        while not GPIO.input(self.pin1):
            pass
        t2 = time.time()
        return (t2 - t1) * 1000000  # microseconds

    # Take an analog reading as the time taken to charge after first discharging the capacitor
    def analog_read(self):
        self.discharge()
        t = self.charge_time()
        self.discharge()
        return t

    # Convert the time taken to charge the capacitor into a value of resistance
    # To reduce errors in timing, do it a few times and take the median value.
    def read_resistance(self):
        n = 7
        readings = []
        for i in range(0, n):
            reading = self.analog_read()
            readings.append(reading)
            readings.sort()
        t = readings[int(n / 2)]
        T = -t / math.log(1.0 - (self.Vt / self.Vs))
        RC = T
        r = (RC / self.C) - self.R1
        return r

    def read_temp_centigrade(self, B=3800.0, R0=1000.0):
        R = self.read_resistance()
        t0 = 273.15  # 0 deg C in K
        t25 = t0 + 25.0  # 25 deg C in K
        # Steinhart-Hart equation
        inv_T = 1 / t25 + 1 / B * math.log(R / R0)
        T = (1 / inv_T - t0)
        return T

    def read_temp_fahrenheit(self, B=3800.0, R0=1000.0):
        return self.read_temp_centigrade(B, R0) * 9 / 5 + 32


value = ADC()

while True:
    # Taking B value of thermistor to be 3800 and value of resistance to be 1K Ohms
    Temp = value.read_temp_centigrade(3800, 1000)
    print(Temp)
    if Temp <= 15:
        GPIO.output(7, True)
        GPIO.output(8, False)
        GPIO.output(9, False)

    elif (Temp > 15) & (Temp <= 35):
        GPIO.output(7, False)
        GPIO.output(8, True)
        GPIO.output(9, False)

    elif Temp > 35:
        GPIO.output(7, False)
        GPIO.output(8, False)
        GPIO.output(9, True)

    time.sleep(1)
