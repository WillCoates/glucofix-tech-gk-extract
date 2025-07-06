from unittest import TestCase
from unittest.mock import Mock
from glucofix_tech_gk_extract.device import Device, DeviceError, CrcError, Reading, ReadingType, Units, InvalidReadingError, ParseError
from serial import Serial
from datetime import datetime


class TestDevice(TestCase):
    def setUp(self):
        self.mock_port = Mock(spec=Serial)
        self.device = Device(self.mock_port)

    def test_read_config_success(self):
        # Response should not include initial [\r\n
        mock_response = (
            b'0000000000000,58,59,      DEMOSN, B.0\r\n'
            b'E6\r\n'
            b']\r\n'
        )

        self.mock_port.read_until.side_effect = [
            b'',
            mock_response
        ]

        result = self.device.read_config()

        self.assertEqual(result.serial_number, 'DEMOSN')

    def test_read_config_bad_crc(self):
        mock_response = (
            b'0000000000000,58,59,      DEMOSN, B.0\r\n'
            b'6E\r\n'
            b']\r\n'
        )

        self.mock_port.read_until.side_effect = [
            b'',
            mock_response
        ]

        with self.assertRaises(CrcError):
            self.device.read_config()

    def test_read_glucose_readings_success(self):
        mock_response = (
            b'Glu, 5.2,mmol/L,00,240101,0800\r\n'
            b'Glu, 125, mg/dL,00,240609,1812\r\n'
            b'Glu,  HI,mmol/L,00,250203,1232\r\n'
            b'Glu,  LO,mmol/L,00,250603,1232\r\n'
            b'D8\r\n'
            b']\r\n'
        )

        expected_results = [
            Reading(ReadingType.GLUCOSE, 5.2, Units.MMOL_L,
                    datetime(2024, 1, 1, 8, 0, 0)),
            Reading(ReadingType.GLUCOSE, 125, Units.MG_DL,
                    datetime(2024, 6, 9, 18, 12, 0)),
            Reading(ReadingType.GLUCOSE, 'HI', Units.MMOL_L,
                    datetime(2025, 2, 3, 12, 32, 0)),
            Reading(ReadingType.GLUCOSE, 'LO', Units.MMOL_L,
                    datetime(2025, 6, 3, 12, 32, 0)),
        ]

        self.mock_port.read_until.side_effect = [
            b'',
            mock_response
        ]

        result = self.device.read_glucose_readings()

        self.assertListEqual(
            result,
            expected_results
        )

    def test_read_glucose_readings_throws(self):
        test_cases = [
            ('invalid unit', InvalidReadingError,
             b'Glu,10.2,    %,00,240101,0800\r\n67\r\n]\r\n'),
            ('invalid reading type', InvalidReadingError,
             b'Hug,10.2,mmol/L,00,240101,0800\r\nA4\r\n]\r\n'),
            ('not enough columns', ParseError,
             b'Glu,10.2,mmol/L,240101,0800\r\n94\r\n]\r\n'),
            ('bad crc', CrcError, b'Glu,10.2,mmol/L,00,240101,0800\r\nFF\r\n]\r\n'),
        ]

        for (name, expected_exception, mock_response) in test_cases:
            with self.subTest(name):
                self.mock_port.read_until.side_effect = [
                    b'',
                    mock_response
                ]

                with self.assertRaises(expected_exception):
                    self.device.read_glucose_readings()

    def test_read_ketone_readings_success(self):
        mock_response = (
            b'Ket, 0.2,mmol/L,00,240101,0800\r\n'
            b'Ket,  HI,mmol/L,00,240609,1812\r\n'
            b'F0\r\n'
            b']\r\n'
        )

        expected_results = [
            Reading(ReadingType.KETONE, 0.2, Units.MMOL_L,
                    datetime(2024, 1, 1, 8, 0, 0)),
            Reading(ReadingType.KETONE, 'HI', Units.MMOL_L,
                    datetime(2024, 6, 9, 18, 12, 0)),
        ]

        self.mock_port.read_until.side_effect = [
            b'',
            mock_response
        ]

        result = self.device.read_ketone_readings()

        self.assertListEqual(
            result,
            expected_results
        )

    def test_read_ketone_readings_throws(self):
        test_cases = [
            ('invalid unit', InvalidReadingError,
             b'Ket, 1.2,    %,00,240101,0800\r\n4A\r\n]\r\n'),
            ('invalid reading type', InvalidReadingError,
             b'Hug, 1.2,mmol/L,00,240101,0800\r\n1D\r\n]\r\n'),
            ('not enough columns', ParseError,
             b'Ket, 1.2,mmol/L,240101,0800\r\nA4\r\n]\r\n'),
            ('bad crc', CrcError, b'Ket, 1.2,mmol/L,00,240101,0800\r\nFF\r\n]\r\n'),
        ]

        for (name, expected_exception, mock_response) in test_cases:
            with self.subTest(name):
                self.mock_port.read_until.side_effect = [
                    b'',
                    mock_response
                ]

                with self.assertRaises(expected_exception):
                    self.device.read_ketone_readings()
