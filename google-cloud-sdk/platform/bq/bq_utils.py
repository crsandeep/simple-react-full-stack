#!/usr/bin/env python
"""A library of functions to handle bq flags consistently."""

import os
from absl import app
from absl import flags

FLAGS = flags.FLAGS


def GetBigqueryRcFilename():
  """Return the name of the bigqueryrc file to use.

  In order, we look for a flag the user specified, an environment
  variable, and finally the default value for the flag.

  Returns:
    bigqueryrc filename as a string.
  """
  return ((FLAGS['bigqueryrc'].present and FLAGS.bigqueryrc) or
          os.environ.get('BIGQUERYRC') or FLAGS.bigqueryrc)


def ProcessBigqueryrc():
  """Updates FLAGS with values found in the bigqueryrc file."""
  ProcessBigqueryrcSection(None, FLAGS)


def ProcessBigqueryrcSection(section_name, flag_values):
  """Read the bigqueryrc file into flag_values for section section_name.

  Args:
    section_name: if None, read the global flag settings.
    flag_values: FLAGS instance.

  Raises:
    UsageError: Unknown flag found.
  """

  bigqueryrc = GetBigqueryRcFilename()
  if not os.path.exists(bigqueryrc):
    return
  with open(bigqueryrc) as rcfile:
    in_section = not section_name
    for line in rcfile:
      if line.lstrip().startswith('[') and line.rstrip().endswith(']'):
        next_section = line.strip()[1:-1]
        in_section = section_name == next_section
        continue
      elif not in_section:
        continue
      elif line.lstrip().startswith('#') or not line.strip():
        continue
      flag, equalsign, value = line.partition('=')
      # if no value given, assume stringified boolean true
      if not equalsign:
        value = 'true'
      flag = flag.strip()
      value = value.strip()
      while flag.startswith('-'):
        flag = flag[1:]
      # We want flags specified at the command line to override
      # those in the flagfile.
      if flag not in flag_values:
        raise app.UsageError(
            'Unknown flag %s found in bigqueryrc file in section %s' %
            (flag, section_name if section_name else 'global'))
      if not flag_values[flag].present:
        flag_values[flag].parse(value)
      else:
        flag_type = flag_values[flag].flag_type()
        if flag_type.startswith('multi'):
          old_value = getattr(flag_values, flag)
          flag_values[flag].parse(value)
          setattr(flag_values, flag, old_value + getattr(flag_values, flag))
