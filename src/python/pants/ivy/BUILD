# Copyright 2014 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).

python_library(
  name = 'ivy',
  sources = globs('*.py'),
  dependencies = [
    '3rdparty/python:six',
    '3rdparty/python/twitter/commons:twitter.common.collections',
    '3rdparty/python/twitter/commons:twitter.common.log',
    'src/python/pants/base:config',
    'src/python/pants/java:executor',
    'src/python/pants/java:util',
    'src/python/pants/net',
    'src/python/pants/util:contextutil',
    'src/python/pants/util:dirutil',
  ]
)
