import unittest
import utils


class TestUtils(unittest.TestCase):

    def test_fqdn(self):
        self.assertTrue(utils.is_fqdn("a1zlvbsytboce2-ats.iot.ap-southeast-2.amazonaws.com"))


if __name__ == '__main__':
    unittest.main()
