"""Use the original independent input, command and delivered-map auditor."""
from common import base_module


def audit():
    return base_module('audit').audit()
