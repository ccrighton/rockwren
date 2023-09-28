# SPDX-FileCopyrightText: 2023 Charles Crighton <code@crighton.net.nz>
#
# SPDX-License-Identifier: GPL-3.0-or-later
import sys
import unittest
from unittest import mock
from unittest.mock import patch

from .context import rockwren

sys.modules['ubinascii'] = __import__('binascii')
sys.modules['ujson'] = __import__('json')
spi_mock = mock.Mock()
machine_mock = mock.MagicMock()
machine_mock.Pin = mock.MagicMock()
machine_mock.SPI = mock.MagicMock(return_value=spi_mock)
gc_mock = mock.MagicMock()
patch.dict("sys.modules", machine=machine_mock).start()
patch.dict("sys.modules", gc=gc_mock).start()
patch.dict("sys.modules", uasyncio=mock.MagicMock()).start()
patch.dict("sys.modules", usocket=mock.MagicMock()).start()
patch.dict("sys.modules", ntptime=mock.MagicMock()).start()
patch.dict("sys.modules", ubinascii=mock.MagicMock()).start()
patch.dict("sys.modules", ujson=mock.MagicMock()).start()

from rockwren import utils

class TestUtils(unittest.TestCase):

    def test_fqdn(self):
        self.assertTrue(utils.is_fqdn("a1zlvbsytboce2-ats.iot.ap-southeast-2.amazonaws.com"))


if __name__ == '__main__':
    unittest.main()
