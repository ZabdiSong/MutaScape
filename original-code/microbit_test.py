import serial

ser = serial.Serial("COM3", 115200)

while True:

    value = ser.readline().decode().strip()

    if value:
        print(value)