# Copyright 2014 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).

from __future__ import (nested_scopes, generators, division, absolute_import, with_statement,
                        print_function, unicode_literals)

import os
import unittest
from tempfile import mkdtemp
from textwrap import dedent

from twitter.common.dirutil import safe_mkdir, safe_open, safe_rmtree

from pants.base.address import Address, SyntheticAddress
from pants.base.build_graph import BuildGraph
from pants.base.build_root import BuildRoot
from pants.base.build_file_parser import BuildFileCache, BuildFileParser
from pants.base.config import Config
from pants.base.source_root import SourceRoot
from pants.base.target import Target


def make_default_build_file_parser(build_root):
  from pants.base.build_file_aliases import (target_aliases, object_aliases,
                                             applicative_path_relative_util_aliases,
                                             partial_path_relative_util_aliases)
  for alias, target_type in target_aliases.items():
    BuildFileParser.register_target_alias(alias, target_type)

  for alias, obj in object_aliases.items():
    BuildFileParser.register_exposed_object(alias, obj)

  for alias, util in applicative_path_relative_util_aliases.items():
    BuildFileParser.register_applicative_path_relative_util(alias, util)

  for alias, util in partial_path_relative_util_aliases.items():
    BuildFileParser.register_partial_path_relative_util(alias, util)

  return BuildFileParser(root_dir=build_root)


class BaseTest(unittest.TestCase):
  """A baseclass useful for tests requiring a temporary buildroot."""

  def build_path(self, relpath):
    """Returns the canonical BUILD file path for the given relative build path."""
    if os.path.basename(relpath).startswith('BUILD'):
      return relpath
    else:
      return os.path.join(relpath, 'BUILD')

  def create_dir(self, relpath):
    """Creates a directory under the buildroot.

    relpath: The relative path to the directory from the build root.
    """
    safe_mkdir(os.path.join(self.build_root, relpath))

  def create_file(self, relpath, contents='', mode='w'):
    """Writes to a file under the buildroot.

    relpath:  The relative path to the file from the build root.
    contents: A string containing the contents of the file - '' by default..
    mode:     The mode to write to the file in - over-write by default.
    """
    with safe_open(os.path.join(self.build_root, relpath), mode=mode) as fp:
      fp.write(contents)

  def add_to_build_file(self, relpath, target):
    """Adds the given target specification to the BUILD file at relpath.

    relpath: The relative path to the BUILD file from the build root.
    target:  A string containing the target definition as it would appear in a BUILD file.
    """
    self.create_file(self.build_path(relpath), target, mode='a')

  def make_target(self,
                  spec='',
                  target_type=Target,
                  dependencies=None,
                  derived_from=None,
                  **kwargs):
    address = SyntheticAddress(spec)
    target = target_type(name=address.target_name,
                         address=address,
                         build_graph=self.build_graph,
                         **kwargs)
    dependencies = dependencies or []
    self.build_graph.inject_target(target,
                                   dependencies=[dep.address for dep in dependencies],
                                   derived_from=derived_from)
    return target

  def setUp(self):
    self.build_root = mkdtemp(suffix='_BUILD_ROOT')
    BuildRoot().path = self.build_root
    self.create_file('pants.ini')
    self.build_file_parser = make_default_build_file_parser(self.build_root)
    self.build_graph = BuildGraph()
    self.config = Config.load()

  def tearDown(self):
    BuildRoot().reset()
    SourceRoot.reset()
    safe_rmtree(self.build_root)
    BuildFileCache.clear()
    self.build_file_parser.clear_registered_context()

  def target(self, spec):
    """Resolves the given target address to a Target object.

    address: The BUILD target address to resolve.

    Returns the corresponding Target or else None if the address does not point to a defined Target.
    """
    if self.build_graph.get_target_from_spec(spec) is None:
      self.build_file_parser.inject_spec_closure_into_build_graph(spec, self.build_graph)
    return self.build_graph.get_target_from_spec(spec)

  def create_files(self, path, files):
    """Writes to a file under the buildroot with contents same as file name.

     path:  The relative path to the file from the build root.
     files: List of file names.
    """
    for f in files:
      self.create_file(os.path.join(path, f), contents=f)

  def create_library(self, path, target_type, name, sources, **kwargs):
    """Creates a library target of given type at the BUILD file at path with sources

     path: The relative path to the BUILD file from the build root.
     target_type: valid pants target type.
     name: Name of the library target.
     sources: List of source file at the path relative to path.
     **kwargs: Optional attributes that can be set for any library target.
       Currently it includes support for provides, resources, java_sources
    """
    self.create_files(path, sources)
    self.add_to_build_file(path, dedent('''
          %(target_type)s(name='%(name)s',
            sources=%(sources)s,
            %(resources)s
            %(provides)s
            %(java_sources)s
          )
        ''' % dict(target_type=target_type,
                   name=name,
                   sources=repr(sources or []),
                   resources=('resources=[pants("%s")],' % kwargs.get('resources')
                              if kwargs.has_key('resources') else ''),
                   provides=(dedent('''provides=artifact(
                                                  org = 'com.twitter',
                                                  name = '%s',
                                                  repo = pants('build-support/ivy:ivy')
                                                ),
                                     '''% name if kwargs.has_key('provides') else '')),
                   java_sources=('java_sources=[%s]'
                                 % ','.join(map(lambda str_target: 'pants("%s")' % str_target,
                                                kwargs.get('java_sources')))
                                 if kwargs.has_key('java_sources') else ''),
                   )))
    return self.target('%s:%s' % (path, name))

  def create_resources(self, path, name, *sources):
    return self.create_library(path, 'resources', name, sources)