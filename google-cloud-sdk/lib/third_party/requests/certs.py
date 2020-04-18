#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""This file replaces certs.py from requests, which uses certifi for
CA certificates. This allows us to remove the certifi dependency from
the requests library.

requests.certs
~~~~~~~~~~~~~~

This module returns the preferred default CA certificate bundle.
"""
import os.path

def where():
    """Return the preferred certificate bundle."""
    return os.path.join(os.path.dirname(__file__), 'cacert.pem')

if __name__ == '__main__':
    print(where())
