from dataclasses import dataclass
from serial import Serial
from crc import Calculator, Crc8
from typing import List, Union, Literal
from datetime import datetime
import logging
from enum import Enum


class DeviceError(Exception):
    pass


class CrcError(DeviceError):
    pass


class ParseError(DeviceError):
    pass


class InvalidReadingError(DeviceError):
    pass


class ReadingType(Enum):
    GLUCOSE = 'Glu'
    KETONE = 'Ket'


class Units(Enum):
    MMOL_L = 'mmol/L'
    MG_DL = 'mg/dL'


@dataclass
class DeviceConfig:
    serial_number: str


@dataclass
class Reading:
    reading_type: ReadingType
    reading: Union[Literal['HI', 'LO'], float]
    units: Units
    time: datetime


class Device:
    OPCODE_CONFIG = b'\xa2'
    OPCODE_GLUCOSE = b'\x80'
    OPCODE_KETONE = b'\xa8'

    def __init__(self, port: Serial):
        self._port = port
        self._crc = Calculator(Crc8.MAXIM_DOW)
        self._logger = logging.getLogger(__name__)

    def _read_response(self) -> List[List[str]]:
        """Reads and validates a response from the glucose meter"""
        response = self._read_raw_response()
        self._validate_crc(response)
        return self._parse_response(response)

    def _read_raw_response(self) -> bytes:
        """Reads raw response from the device"""
        # Make sure we're at the start of a response
        self._port.read_until(b'[\r\n')
        response = b'[\r\n' + self._port.read_until(b']\r\n')
        return response

    def _validate_crc(self, response: bytes) -> None:
        """Validates CRC of response"""
        if len(response) < 7:
            raise CrcError('Response too short for CRC validation')

        try:
            provided_crc = int(response[-7:-5], 16)
            expected_crc = self._crc.checksum(response[:-7])

            if expected_crc != provided_crc:
                raise CrcError(
                    f'CRC mismatch: expected {expected_crc:02X}, got {provided_crc:02X}')

        except ValueError as e:
            raise CrcError(f'Invalid CRC format: {e}')

    def _parse_response(self, response: bytes) -> List[List[str]]:
        """Parses response data into a list of fields"""
        data = response[3:-9]

        entries = []

        for row in data.split(b'\r\n'):
            fields = row.split(b',')
            entries.append([field.strip().decode('ascii') for field in fields])

        return entries

    def _send_command(self, opcode: bytes) -> List[List[str]]:
        """Sends an opcode to the glucose meter and reads a response"""
        self._logger.debug(f'Sending opcode: {opcode.hex()}')
        self._port.write(opcode)
        response = self._read_response()
        self._logger.debug(f'Got response: {response}')
        return response

    def _parse_date_time(self, date: str, time: str) -> datetime:
        """Parses a date/time from the glucose meter"""
        try:
            return datetime(
                year=int('20' + date[0:2], 10),
                month=int(date[2:4], 10),
                day=int(date[4:6], 10),
                hour=int(time[0:2], 10),
                minute=int(time[2:4], 10),
                second=0
            )
        except (ValueError, IndexError) as e:
            raise ParseError(f"Invalid datetime format: '{date}' '{time}'")

    def _decode_reading(self, response: List[List[str]]) -> List[Reading]:
        readings = []
        for row in response:
            if len(row) < 6:
                raise ParseError(f'Incomplete row, expecting 5 fields: {row}')

            if row[0].lower() == 'glu':
                reading_type = ReadingType.GLUCOSE
            elif row[0].lower() == 'ket':
                reading_type = ReadingType.KETONE
            else:
                raise InvalidReadingError(f'invalid reading type: {row[0]}')

            reading = row[1].upper()

            if reading != 'HI' and reading != 'LO':
                reading = float(reading)

            if row[2].lower() == 'mmol/l':
                units = Units.MMOL_L
            elif row[2].lower() == 'mg/dl':
                units = Units.MG_DL
            else:
                raise InvalidReadingError(f'invalid units: {row[2]}')

            date_part = row[4]
            time_part = row[5]
            date = self._parse_date_time(date_part, time_part)

            readings.append(Reading(reading_type, reading, units, date))
        return readings

    def read_config(self) -> DeviceConfig:
        response = self._send_command(self.OPCODE_CONFIG)
        if len(response) != 1:
            raise ParseError(f'Expected 1 row, got {len(response)}')
        row = response[0]
        if len(row) < 4:
            raise ParseError(f'Row is too short, expected 4 fields: {row}')
        return DeviceConfig(row[3])

    def read_glucose_readings(self) -> List[Reading]:
        response = self._send_command(self.OPCODE_GLUCOSE)
        return self._decode_reading(response)

    def read_ketone_readings(self) -> List[Reading]:
        response = self._send_command(self.OPCODE_KETONE)
        return self._decode_reading(response)
