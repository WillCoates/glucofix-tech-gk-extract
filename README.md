# Glucofix Tech GK Extract
Extract blood glucose and ketone readings from Glucofix Tech GK meters.

## Why?
Originally, the manufacturer provided a mobile app to extract readings from the
meter. While this worked, the app would crash from time to time. Recently, the
app was removed from the Google Play Store and replaced with a varient which
requires an online account. There is also a desktop varient which uses USB but
also requires an online account.

This project is an attempt to extract data of the meter without requiring any
online accounts.

## Usage

On Linux:
```sh
python3 -m venv venv
source ./venv/bin/activate
pip install -r requirements.txt
# Change /dev/ttyACM0 to device created when connecting meter
python -m glucofix_tech_gk_extract /dev/ttyACM0 ./output
```

Windows instructions coming soon...

## Protocol
The meter communicates using USB ACM, which emulates a serial port. By
capturing the protocol used using Wireshark, we can send the same requests as
the desktop software.

**Serial parameters:**
- 9600 baud
- 8 data bits
- 1 stop bit
- Odd parity
- RTS/CTS and DSR/DTR flow control

**Communication format:**
- Request/response model
- Requests are single-byte opcodes
- Responses are enclosed in square brackets `[...]`
- Each result is seperated by a carridge return and line feed `\r\n`
- Entries are CSV-encoded
- Last entry is a CRC-8/MAXIM-DOW checksum in hex
