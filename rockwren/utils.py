# SPDX-FileCopyrightText: 2023 Charles Crighton <code@crighton.net.nz>
#
# SPDX-License-Identifier: GPL-3.0-or-later
import io
import re

import ubinascii

from phew import logging


def is_fqdn(hostname: str) -> bool:
    """
    Check that the hostname is a fully qualified domain name
    :param hostname: hostname to check
    :return: True if an FQDN otherwise False
    """
    if not 1 < len(hostname) < 253:
        return False

    # Remove trailing dot
    if hostname[-1] == '.':
        hostname = hostname[0:-1]

    #  Convert to lowercase and split hostname into list of labels
    labels = hostname.lower().split('.')

    #  Each label must be between 1 and 63 octets, contain on letters and numbers and '-' (but not at start or end)
    fqdn = re.compile(r'^[a-z0-9]([a-z-0-9-]*[a-z0-9])?$')

    # Check that all labels match that pattern.
    return all(fqdn.match(label) for label in labels)


def pem_to_der(pem):
    """
    Convert a PEM formatted certificate or key and encode as DER (base64)
    :param pem: PEM formatted key or certificate
    :return:
    """
    # remove -----BEGIN PUB KEY... lines and concatenate
    pem = ''.join(pem.split('\n')[1:-2])
    der = ubinascii.a2b_base64(pem)
    return der


def logstream(stream: io.StringIO):
    """ Log stream line by line to avoid allocating a large chunk of memory"""
    stream.seek(0)
    line = stream.readline()
    logging.error(line)
    while line:
        line = stream.readline()
        logging.error(line)
