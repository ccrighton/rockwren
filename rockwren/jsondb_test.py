# SPDX-FileCopyrightText: 2023 Charles Crighton <rockwren@crighton.nz>
#
# SPDX-License-Identifier: GPL-3.0-or-later

import unittest

import ujson

import jsondb


class TestJsonDbMethods(unittest.TestCase):

    def test_load_save(self):
        db = jsondb.JsonDB()
        db.clear()
        db.save()
        db.load()
        db["first_boot"] = True
        db["ssid"] = "elba-main"
        db["password"] = "blah123"
        db.save()

        with open("db.json") as f:
            s = f.read()
            self.assertEqual(s, '{"first_boot": true, "ssid": "elba-main", "password": "blah123"}' )

    def test_load_save_clear_save(self):
        db = jsondb.JsonDB()
        db.clear()
        db.save()
        db.load()
        db["first_boot"] = True
        db["ssid"] = "elba-main"
        db["password"] = "blah123"
        db.save()

        with open("db.json") as f:
            s = f.read()
            self.assertEqual(s, '{"first_boot": true, "ssid": "elba-main", "password": "blah123"}')

        db.clear()
        db.save()

        with open("db.json") as f:
            s = f.read()
            self.assertEqual(s, '{}')

    def test_load_empty_save(self):
        db = jsondb.JsonDB()
        db.clear()
        db.save()
        db.load()
        db.save()

        with open("db.json") as f:
            s = f.read()
            self.assertEqual(s, '{}')

    def test_load_save_change_save(self):
        db = jsondb.JsonDB()
        db.clear()
        db.save()
        db.load()
        db["first_boot"] = True
        db["ssid"] = "elba-main"
        db["password"] = "blah123"
        db.save()

        with open("db.json") as f:
            s = f.read()
            self.assertEqual(s, '{"first_boot": true, "ssid": "elba-main", "password": "blah123"}')

        db["first_boot"] = False
        db.save()

        with open("db.json") as f:
            s = f.read()
            self.assertEqual(s, '{"first_boot": false, "ssid": "elba-main", "password": "blah123"}')


    def test_m_load_save_change_save(self):
        cert = "-----BEGIN CERTIFICATE-----MIIDWTCCAkGgAwIBAgIUOAWT/5Nyq/xfGR79/FwZfkVhzvAwDQYJKoZIhvcNAQELBQAwTTFL" \
               + "MEkGA1UECwxCQW1hem9uIFdlYiBTZXJ2aWNlcyBPPUFtYXpvbi5jb20gSW5jLiBMPVNlYXR0bGUgU1Q9V2FzaGluZ3RvbiBDP" \
               + "VVTMB4XDTIzMDgxMjAzMjYwMloXDTQ5MTIzMTIzNTk1OVowHjEcMBoGA1UEAwwTQVdTIElvVCBDZXJ0aWZpY2F0ZTCCASIwDQ" \
               + "YJKoZIhvcNAQEBBQADggEPADCCAQoCggEBALsEo4R5/kW4yQw9FpZZafF0jWm4/LWznEbyJuah+7Uev9efSXQqTrZKRBBQdWW" \
               + "BhFc0fJHxX+qpykX1hMbYeCMroN9yjv/P1JrqoJ95BiGzA8W64zqZAEuGcYfzaLP2GsXFWiILJ4haLGZHGNopp3R6gcGyuQKZ" \
               + "rbPDyY3U8xY4E8Z7U6Z8TuYkvohXJ+08V42VJP7MeBuesNOyzXvQDjt2MgutmQJIt8oHvPZ0E73U/MXll59zTLNDerc1fuqDh" \
               + "T6zrt3pLkCWUOI8Ryj2DorzfovyaLEDE1DkcardUHEXghOa9PETWmGmFXWBH62Q0AwvOUaA4qfdWj3FNQT+5mECAwEAAaNgMF" \
               + "4wHwYDVR0jBBgwFoAUso8wJxwg52SOYdPFZeVvVrCHIwcwHQYDVR0OBBYEFKAL0nZha2U7vlwps/1SZ3gUb36VMAwGA1UdEwE" \
               + "B/wQCMAAwDgYDVR0PAQH/BAQDAgeAMA0GCSqGSIb3DQEBCwUAA4IBAQBbWIaWCbKITMpfKv/6mMYtDvkukwdGz9AVXs2hzC6z" \
               + "6yunX9Zdv+Y5BaIu2wjdJP7gmlSnsHmqAD9h79CskSjD4EJqVn4tlBft0KDXpcmrFXfF2NX0XADUlwg9pSrttmLG7kC+8QQUJ" \
               + "gCnM5tRQ27deKg+XZPlI40IPJxGseiN1MgzoXlBzYsMJYNyAlJVfql2yc5WVYNbUAHIDJ3HWp9Jj0hjOj2lMOVPvQgUPG08kR" \
               + "tIBGh7K9pYQajM8wntjKNffCSViXG1Hr7tKWXyGjn9hGgLfusprx5OF7wljW1shsR2kZYNOfNeTjlJz6Pxp/QCgC/JCSTayeK" \
               + "xi2KBHql+-----END CERTIFICATE-----"

        db = jsondb.JsonDB()
        db.clear()
        db.save()
        db.load()
        db["first_boot"] = True
        db["ssid"] = "elba-main"
        db["password"] = "blah123"
        db["mqtt_client_cert"] = cert
        db.save()

        with open("db.json") as f:
            s = f.read()
            self.assertEqual(cert, ujson.loads(s)['mqtt_client_cert'])

        db["first_boot"] = False
        db.save()

        with open("db.json") as f:
            s = f.read()
            self.assertEqual(False, ujson.loads(s)['first_boot'])
            self.assertEqual(cert, ujson.loads(s)['mqtt_client_cert'])



if __name__ == '__main__':
    unittest.main()
