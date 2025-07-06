# Glucofix Tech GK Extract
Extract blood glucose and ketone readings from Glucofix Tech GK meters.

## Why?
Originally, the manufacturer provided a mobile app to extract readings off the
meter. While this worked, the app would crash from time-to-time. Recently, the
app was removed from the Google Play Store, and replaced with a varient which
requires an online account. There is also a desktop varient which uses USB.

This project is an attempt to extract data of the meter without requiring any
online accounts.

## Protocol
The meter communicates using USB ACM, which emulates a serial port.

By capturing the protocol used using Wireshark, we can send the same requests
as the desktop software. The device communicates through a 9600 baud serial
connection, with 1 stop bit, odd parity and 8 data bits.

The software communicates with the device using a simple request/response
model. Requests are sent as a single byte.

Responses are recieved as a stream of characters, enclosed in square brackets.
Each result is seperated using a carridge return and line feed. Entries are
encoded using CSV, with the last entry storing a CRC-8/MAXIM-DOW checksum in
hex.

