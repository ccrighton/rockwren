# SPDX-FileCopyrightText: 2023 Charles Crighton <rockwren@crighton.nz>
#
# SPDX-License-Identifier: GPL-3.0-or-later

import os
import ujson
import io


class JsonDB(dict):  # dicts take a mapping or iterable as their optional first argument

    _db_file = "db.json"

    def __init__(self, file="db.json"):
        self._db_file = file
        super().__init__(())

    def load(self):
        loaded = {}
        try:
            with open(self._db_file, "r") as f:
                loaded = ujson.load(f)
        except OSError:
            "initialise empty"
            with open(self._db_file, "w+") as f:
                ujson.dump(loaded, f)
        self.clear()
        self.update(loaded)

    def save(self):
        with open(self._db_file, "w+") as f:
            ujson.dump(self, f)
