# SPDX-FileCopyrightText: 2023 Charles Crighton <rockwren@crighton.nz>
#
# SPDX-License-Identifier: GPL-3.0-or-later
""" Simple database: JSON file backed dictionary"""
import ujson


class JsonDB(dict):  # dicts take a mapping or iterable as their optional first argument
    """
    Simple database with dict interface that stores key value pairs in a json formed text file.
    """

    _db_file = "db.json"

    def __init__(self, file="db.json"):
        self._db_file = file
        super().__init__(())

    def load(self) -> None:
        """ Load database file into dictionary. """
        loaded = {}
        try:
            with open(self._db_file, "r") as db_file:
                loaded = ujson.load(db_file)
        except OSError:
            # initialise empty
            with open(self._db_file, "w+") as db_file:
                ujson.dump(loaded, db_file)
        self.clear()
        self.update(loaded)

    def save(self):
        """ Save dictionary state to database file. """
        with open(self._db_file, "w+") as db_file:
            ujson.dump(self, db_file)
