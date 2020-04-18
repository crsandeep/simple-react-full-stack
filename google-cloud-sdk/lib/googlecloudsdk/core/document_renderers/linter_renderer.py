# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Cloud SDK markdown document linter renderer."""
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import collections
import io
import re

from googlecloudsdk.core.document_renderers import text_renderer
import six


class LinterRenderer(text_renderer.TextRenderer):
  """Renders markdown to a list of lines where there is a linter error."""

  _HEADINGS_TO_LINT = ["NAME", "EXAMPLES", "DESCRIPTION"]
  _NAME_WORD_LIMIT = 20
  _PERSONAL_PRONOUNS = {"me", "we", "I", "us", "he", "she", "him", "her"}
  # gcloud does not recognize the following flags as not requiring a value so
  # they would be marked as violations in _analyze_example_flags_equals.
  _NON_BOOL_FLAGS_WHITELIST = ["--quiet", "--help"]
  _NON_COMMAND_SURFACE_GROUPS = ["gcloud topic"]

  def __init__(self, *args, **kwargs):
    super(LinterRenderer, self).__init__(*args, **kwargs)
    self._file_out = self._out  # the output file inherited from TextRenderer
    self._null_out = io.StringIO()
    self._buffer = io.StringIO()
    self._out = self._buffer
    self._analyze = {"NAME": self._analyze_name,
                     "EXAMPLES": self._analyze_examples,
                     "DESCRIPTION": self._analyze_description}
    self._heading = ""
    self._prev_heading = ""
    self.example = False
    self.command_name = ""
    self.name_section = ""
    self.command_name_length = 0
    self.command_text = ""
    self.equals_violation_flags = []
    self.nonexistent_violation_flags = []
    self.json_object = collections.OrderedDict()

  def _CaptureOutput(self, heading):
    # check if buffer is full from previous heading
    if self._buffer.getvalue() and self._prev_heading:
      self._Analyze(self._prev_heading, self._buffer.getvalue())
      # refresh the StringIO()
      self._buffer = io.StringIO()
    self._out = self._buffer
    # save heading so can get it in next section
    self._prev_heading = self._heading

  def _DiscardOutput(self, heading):
    self._out = self._null_out

  def _Analyze(self, heading, section):
    self._analyze[heading](section)

  def check_for_personal_pronouns(self, section):
    """Raise violation if the section contains personal pronouns."""
    words_in_section = set(re.compile(r"\w+").findall(section.lower()))
    found_pronouns = words_in_section.intersection(self._PERSONAL_PRONOUNS)
    key_object = "# " + self._heading + "_PRONOUN_CHECK FAILED"
    value_object = ("Please remove the following personal pronouns in the " +
                    self._heading + " section:\n")
    if found_pronouns:
      found_pronouns_list = list(found_pronouns)
      found_pronouns_list.sort()
      value_object += "\n".join(found_pronouns_list)
      self.json_object[key_object] = value_object
    return found_pronouns

  def needs_example(self):
    """Check whether command requires an example."""
    # alpha commands, groups, and certain directories do not need examples."""
    if self.command_metadata and self.command_metadata.is_group:
      return False
    if "alpha" in self.command_name:
      return False
    for name in self._NON_COMMAND_SURFACE_GROUPS:
      if self.command_name.startswith(name):
        return False
    return True

  def Finish(self):
    if self._buffer.getvalue() and self._prev_heading:
      self._Analyze(self._prev_heading, self._buffer.getvalue())
    self._buffer.close()
    self._null_out.close()
    if self.needs_example() and not self.example:
      value_object = (
          "You have not included an example in the Examples section.")
      self.json_object["# EXAMPLE_PRESENT_CHECK FAILED"] = value_object
    for element in self.json_object:
      if self.json_object[element]:
        self._file_out.write(
            six.text_type(element) + ": " +
            six.text_type(self.json_object[element]) + "\n")
      else:
        self._file_out.write(six.text_type(element) + "\n")

  def Heading(self, level, heading):
    self._heading = heading
    if heading in self._HEADINGS_TO_LINT:
      self._CaptureOutput(heading)
    else:
      self._DiscardOutput(heading)

  def Example(self, line):
    # ensure this example is in the EXAMPLES section and it is not a group level
    # command
    if (self.command_metadata and not self.command_metadata.is_group and
        self._heading == "EXAMPLES"):
      # if previous line ended in a backslash, it is not the last line of the
      # command so append new line of command to command_text
      if self.command_text and self.command_text.endswith("\\"):
        self.command_text = self.command_text.rstrip("\\") + line.strip()
      # This is the first line of the command and ignore the `$ ` in it.
      else:
        self.command_text = line.replace("$ ", "")
      # if the current line doesn"t end with a `\`, it is the end of the command
      # so self.command_text is the whole command
      if not line.endswith("\\"):
        # check that the example starts with the command of the help text
        if self.command_text.startswith(self.command_name):
          self.example = True
          self.json_object["# EXAMPLE_PRESENT_CHECK SUCCESS"] = ""
          # self._file_out.write("# EXAMPLE_PRESENT_CHECK SUCCESS\n")
          rest_of_command = self.command_text[self.command_name_length:].split()
          flag_names = []
          for word in rest_of_command:
            word = word.replace("\\--", "--")
            # Stop parsing arguments when ' -- ' is encountered.
            if word == "--":
              break
            if word.startswith("--"):
              flag_names.append(word)
          self._analyze_example_flags_equals(flag_names)
          flags = [flag.partition("=")[0] for flag in flag_names]
          if self.command_metadata and self.command_metadata.flags:
            self._check_valid_flags(flags)

  def _check_valid_flags(self, flags):
    for flag in flags:
      if flag not in self.command_metadata.flags:
        self.nonexistent_violation_flags.append(flag)

  def _analyze_example_flags_equals(self, flags):
    for flag in flags:
      if ("=" not in flag and flag not in self.command_metadata.bool_flags and
          flag not in self._NON_BOOL_FLAGS_WHITELIST):
        self.equals_violation_flags.append(flag)

  def _analyze_name(self, section):
    warnings = self.check_for_personal_pronouns(section)
    if not warnings:
      self.json_object["# NAME_PRONOUN_CHECK SUCCESS"] = ""
    self.command_name = section.strip().split(" -")[0]
    if len(section.replace("\n", " ").strip().split(" - ")) == 1:
      self.name_section = ""
      value_object = "Please add an explanation for the command."
      self.json_object["# NAME_DESCRIPTION_CHECK FAILED"] = value_object
      warnings = True
    else:
      self.name_section = section.strip().split(" -")[1]
      self.json_object["# NAME_DESCRIPTION_CHECK SUCCESS"] = ""
    self.command_name_length = len(self.command_name)
    # check that name section is not too long
    if len(self.name_section.split()) > self._NAME_WORD_LIMIT:
      value_object = ("Please shorten the name section description to "
                      "less than " + six.text_type(self._NAME_WORD_LIMIT) +
                      " words.")
      self.json_object["# NAME_LENGTH_CHECK FAILED"] = value_object
      warnings = True
    else:
      self.json_object["# NAME_LENGTH_CHECK SUCCESS"] = ""
    if not warnings:
      self.json_object["There are no errors for the NAME section."] = ""

  def _analyze_examples(self, section):
    if not self.command_metadata.is_group:
      warnings = self.check_for_personal_pronouns(section)
      if not warnings:
        self.json_object["# EXAMPLES_PRONOUN_CHECK SUCCESS"] = ""
      if self.equals_violation_flags:
        warnings = True
        list_contents = ""
        for flag in range(len(self.equals_violation_flags) - 1):
          list_contents += six.text_type(
              self.equals_violation_flags[flag]) + ", "
        list_contents += six.text_type(self.equals_violation_flags[-1])
        value_object = ("There should be an `=` between the flag name and "
                        "the value for the following flags: " +  list_contents)
        self.json_object["# EXAMPLE_FLAG_EQUALS_CHECK FAILED"] = value_object
        warnings = True
      else:
        self.json_object["# EXAMPLE_FLAG_EQUALS_CHECK SUCCESS"] = ""
      if self.nonexistent_violation_flags:
        warnings = True
        list_contents = ""
        for flag in range(len(self.nonexistent_violation_flags) - 1):
          list_contents += six.text_type(
              self.nonexistent_violation_flags[flag]) + ", "
        list_contents += six.text_type(self.nonexistent_violation_flags[-1])
        key_object = "# EXAMPLE_NONEXISTENT_FLAG_CHECK FAILED"
        value_object = ("The following flags are not valid for the command: " +
                        list_contents)
        self.json_object[key_object] = value_object
      else:
        self.json_object["# EXAMPLE_NONEXISTENT_FLAG_CHECK SUCCESS"] = ""
      if not warnings:
        self.json_object["There are no errors for the EXAMPLES section."] = ""

  def _analyze_description(self, section):
    warnings = self.check_for_personal_pronouns(section)
    if not warnings:
      self.json_object["# DESCRIPTION_PRONOUN_CHECK SUCCESS"] = ""
    if not warnings:
      self.json_object["There are no errors for the DESCRIPTION section."] = ""
