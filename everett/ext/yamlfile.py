# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""This module holds the ConfigYamlEnv environment.

To use this, you must install the optional requirements::

    $ pip install everett[yaml]

"""

import os

import yaml

from everett import ConfigurationError
from everett.manager import get_key_from_envs, listify


class ConfigYamlEnv(object):
    """Source for pulling configuration from YAML files

    This requires optional dependencies. You can install them with::

        $ pip install everett[yaml]


    Takes a path or list of possible paths to look for a YAML file. It uses
    the first YAML file it can find.

    If it finds no YAML files in the possible paths, then this configuration
    source will be a no-op.

    This will expand ``~`` as well as work relative to the current working
    directory.

    This example looks just for the YAML file specified in the environment::

        from everett.manager import ConfigManager
        from everett.ext.yamlfile import ConfigYamlEnv

        config = ConfigManager([
            ConfigYamlEnv(os.environ.get('FOO_YAML'))
        ])

    If there's no ``FOO_YAML`` in the environment, then the path will be
    ignored.

    Here's an example that looks for the YAML file specified in the environment
    variable ``FOO_YAML`` and failing that will look for ``.antenna.yaml`` in
    the user's home directory::

        from everett.manager import ConfigManager
        from everett.ext.yamlfile import ConfigYamlEnv

        config = ConfigManager([
            ConfigYamlEnv([
                os.environ.get('FOO_YAML'),
                '~/.antenna.yaml'
            ])
        ])

    This example looks for a ``config/local.yaml`` file which overrides values
    in a ``config/base.yaml`` file both are relative to the current working
    directory::

        from everett.manager import ConfigManager
        from everett.ext.yamlfile import ConfigYamlEnv

        config = ConfigManager([
            ConfigYamlEnv('config/local.yaml'),
            ConfigYamlEnv('config/base.yaml')
        ])


    Note how you can have multiple ``ConfigYamlEnv`` files. This is how you
    can set Everett up to have values in one YAML file override values in
    another YAML file.

    Everett looks for keys and values in YAML files. YAML files can be split
    into multiple documents, but Everett only looks at the first one.

    Keys are case-insensitive. You can do namespaces either in the key itself
    using ``_`` as a separator or as nested mappings.

    All values should be double-quoted.

    Here's an example::

        foo: "bar"
        FOO2: "bar"
        namespace_foo: "bar"
        namespace:
            namespace2:
                foo: "bar"

    Giving you these namespaced keys:

    * ``FOO``
    * ``FOO2``
    * ``NAMESPACE_FOO``
    * ``NAMESPACE_NAMEPSACE2_FOO``

    """
    def __init__(self, possible_paths):
        self.cfg = {}
        possible_paths = listify(possible_paths)

        for path in possible_paths:
            if not path:
                continue

            path = os.path.abspath(os.path.expanduser(path.strip()))
            if path and os.path.isfile(path):
                self.cfg = self.parse_yaml_file(path)
                break

    def parse_yaml_file(self, path):
        with open(path, 'r') as fp:
            data = yaml.safe_load(fp)

        if not data:
            return {}

        def traverse(namespace, d):
            cfg = {}
            for key, val in d.items():
                if isinstance(d[key], dict):
                    cfg.update(traverse(namespace + [key], d[key]))
                else:
                    if not isinstance(val, str):
                        # All values should be double-quoted strings so they
                        # parse as strings; anything else is a configuration
                        # error at parse-time
                        raise ConfigurationError(
                            'Invalid value %r in file %s: values must be double-quoted strings' % (
                                val, path
                            )
                        )

                    cfg['_'.join(namespace + [key]).upper()] = val

            return cfg

        return traverse([], data)

    def get(self, key, namespace=None):
        return get_key_from_envs(self.cfg, key, namespace)