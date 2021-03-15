from pyax12.connection import Connection

servos_serial = Connection(port="/dev/ttyUSB0", baudrate= 1000000)

available_ids= servos_serial.scan()





for id in available_ids:
    print(id)
