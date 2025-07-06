import serial
from .device import Device
import logging
import argparse
import os
import csv


parser = argparse.ArgumentParser(
    prog='Glucofix Tech GK Extract',
    description=(
        'Extract blood glucose and ketone readings from Glucofix Tech'
        'GK meters.'
    ),
)


parser.add_argument(
    'device',
    help='Device to read data from. Example: /dev/tty/ACM0'
)
parser.add_argument(
    'output',
    help='Directory to put extracted data'
)
parser.add_argument(
    '-l',
    '--loglevel',
    default='INFO',
    help='Output log level'
)
args = parser.parse_args()

os.makedirs(args.output, exist_ok=True)

logging.basicConfig(level=args.loglevel)

port = serial.Serial(
    port=args.device,
    baudrate=9600,
    bytesize=serial.EIGHTBITS,
    parity=serial.PARITY_ODD,
    stopbits=serial.STOPBITS_ONE,
    rtscts=True,
    dsrdtr=True
)

device = Device(port)

config = device.read_config()
logging.info(f'Reading device {config.serial_number}')

glucose_readings = device.read_glucose_readings()
logging.info(f'Read {len(glucose_readings)} readings')

ketone_readings = device.read_ketone_readings()
logging.info(f'Read {len(ketone_readings)} readings')

glucose_file = os.path.join(args.output, 'glucose.csv')
with open(glucose_file, 'w') as f:
    writer = csv.writer(f)
    writer.writerow(['Time', 'Reading', 'Units'])
    for reading in glucose_readings:
        writer.writerow([reading.time, reading.reading, reading.units.value])

ketone_file = os.path.join(args.output, 'ketone.csv')
with open(ketone_file, 'w') as f:
    writer = csv.writer(f)
    writer.writerow(['Time', 'Reading', 'Units'])
    for reading in ketone_readings:
        writer.writerow([reading.time, reading.reading, reading.units.value])
