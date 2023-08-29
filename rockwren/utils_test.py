# SPDX-FileCopyrightText: 2023 Charles Crighton <rockwren@crighton.nz>
#
# SPDX-License-Identifier: GPL-3.0-or-later
import unittest

import utils


class TestUtils(unittest.TestCase):

    def test_fqdn(self):
        self.assertTrue(utils.is_fqdn("a1zlvbsytboce2-ats.iot.ap-southeast-2.amazonaws.com"))


if __name__ == '__main__':
    unittest.main()
