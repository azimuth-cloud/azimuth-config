""" "Configuration to output a string as a YAML literal with the :|"""

import yaml


class LiteralString(str):
    """Class for a string to be dumped as a literal"""


def literal_representer(dumper, data):
    """Represent given data as a YAML literal string according to YAML standards"""
    return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")


yaml.add_representer(LiteralString, literal_representer)
