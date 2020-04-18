# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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
"""Helpers for parsing flags and arguments."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.kms import maps
from googlecloudsdk.command_lib.util import completers
from googlecloudsdk.command_lib.util import parameter_info_lib
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources
from googlecloudsdk.core.util import times

KEY_RING_COLLECTION = 'cloudkms.projects.locations.keyRings'
LOCATION_COLLECTION = 'cloudkms.projects.locations'

# Collection names.
CRYPTO_KEY_COLLECTION = 'cloudkms.projects.locations.keyRings.cryptoKeys'
CRYPTO_KEY_VERSION_COLLECTION = '%s.cryptoKeyVersions' % CRYPTO_KEY_COLLECTION
IMPORT_JOB_COLLECTION = 'cloudkms.projects.locations.keyRings.importJobs'
# list command aggregators


class ListCommandParameterInfo(parameter_info_lib.ParameterInfoByConvention):

  def GetFlag(self,
              parameter_name,
              parameter_value=None,
              check_properties=True,
              for_update=False):
    return super(ListCommandParameterInfo, self).GetFlag(
        parameter_name,
        parameter_value=parameter_value,
        check_properties=check_properties,
        for_update=for_update,
    )


class ListCommandCompleter(completers.ListCommandCompleter):

  def ParameterInfo(self, parsed_args, argument):
    return ListCommandParameterInfo(
        parsed_args,
        argument,
        self.collection,
        updaters=COMPLETERS_BY_CONVENTION,
    )


# kms completers


class LocationCompleter(ListCommandCompleter):

  def __init__(self, **kwargs):
    super(LocationCompleter, self).__init__(
        collection=LOCATION_COLLECTION,
        list_command='kms locations list --uri',
        **kwargs)


class KeyRingCompleter(ListCommandCompleter):

  def __init__(self, **kwargs):
    super(KeyRingCompleter, self).__init__(
        collection=KEY_RING_COLLECTION,
        list_command='kms keyrings list --uri',
        flags=['location'],
        **kwargs)


class KeyCompleter(ListCommandCompleter):

  def __init__(self, **kwargs):
    super(KeyCompleter, self).__init__(
        collection=CRYPTO_KEY_COLLECTION,
        list_command='kms keys list --uri',
        flags=['location', 'keyring'],
        **kwargs)


class KeyVersionCompleter(ListCommandCompleter):

  def __init__(self, **kwargs):
    super(KeyVersionCompleter, self).__init__(
        collection=CRYPTO_KEY_VERSION_COLLECTION,
        list_command='kms keys versions list --uri',
        flags=['location', 'key', 'keyring'],
        **kwargs)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class ImportJobCompleter(ListCommandCompleter):

  def __init__(self, **kwargs):
    super(ImportJobCompleter, self).__init__(
        collection=IMPORT_JOB_COLLECTION,
        list_command='beta kms import-jobs list --uri',
        flags=['location', 'keyring'],
        **kwargs)


# completers by parameter name convention

COMPLETERS_BY_CONVENTION = {
    'location': (LocationCompleter, False),
    'keyring': (KeyRingCompleter, False),
    'key': (KeyCompleter, False),
    'import-jobs': (ImportJobCompleter, False),
}


# Flags.
def AddLocationFlag(parser, resource='resource'):
  parser.add_argument(
      '--location',
      completer=LocationCompleter,
      help='Location of the {0}.'.format(resource))


def AddKeyRingFlag(parser, resource='resource'):
  parser.add_argument(
      '--keyring',
      completer=KeyRingCompleter,
      help='Key ring of the {0}.'.format(resource))


def AddCryptoKeyFlag(parser, help_text=None):
  parser.add_argument(
      '--key', completer=KeyCompleter, help=help_text or 'The containing key.')


def AddKeyResourceFlags(parser, help_text=None):
  AddLocationFlag(parser, 'keyring')
  AddKeyRingFlag(parser, 'key')
  AddCryptoKeyFlag(parser, help_text)


def AddCryptoKeyVersionFlag(parser, help_action, required=False):
  parser.add_argument(
      '--version',
      required=required,
      completer=KeyVersionCompleter,
      help='Version {0}.'.format(help_action))


def AddCryptoKeyPrimaryVersionFlag(parser, help_action, required=False):
  parser.add_argument(
      '--primary-version',
      required=required,
      completer=KeyVersionCompleter,
      help='Primary version {0}.'.format(help_action))


def AddRotationPeriodFlag(parser):
  parser.add_argument(
      '--rotation-period',
      type=arg_parsers.Duration(lower_bound='1d'),
      help=('Automatic rotation period of the key. See '
            '$ gcloud topic datetimes for information on duration formats.'))


def AddNextRotationTimeFlag(parser):
  parser.add_argument(
      '--next-rotation-time',
      type=arg_parsers.Datetime.Parse,
      help=('Next automatic rotation time of the key. See '
            '$ gcloud topic datetimes for information on time formats.'))


def AddRemoveRotationScheduleFlag(parser):
  parser.add_argument(
      '--remove-rotation-schedule',
      action='store_true',
      help='Remove any existing rotation schedule on the key.')


def AddSkipInitialVersionCreationFlag(parser):
  parser.add_argument(
      '--skip-initial-version-creation',
      default=None,
      action='store_true',
      dest='skip_initial_version_creation',
      help=('Skip creating the first version in a key and setting it as '
            'primary during creation.'))


def AddPlaintextFileFlag(parser, help_action):
  parser.add_argument(
      '--plaintext-file',
      help='File path of the plaintext file {0}.'.format(help_action),
      required=True)


def AddCiphertextFileFlag(parser, help_action):
  parser.add_argument(
      '--ciphertext-file',
      help='File path of the ciphertext file {0}.'.format(help_action),
      required=True)


def AddSignatureFileFlag(parser, help_action):
  parser.add_argument(
      '--signature-file',
      help='Path to the signature file {}.'.format(help_action),
      required=True)


def AddInputFileFlag(parser, help_action):
  parser.add_argument(
      '--input-file',
      help='Path to the input file {}.'.format(help_action),
      required=True)


def AddRsaAesWrappedKeyFileFlag(parser, help_action):
  parser.add_argument(
      '--rsa-aes-wrapped-key-file',
      help='Path to the wrapped RSA AES key file {}.'.format(help_action))


def AddOutputFileFlag(parser, help_action):
  parser.add_argument(
      '--output-file', help='Path to the output file {}.'.format(help_action))


def AddAadFileFlag(parser):
  parser.add_argument(
      '--additional-authenticated-data-file',
      help=
      'File path to the optional file containing the additional authenticated '
      'data.')


def AddProtectionLevelFlag(parser):
  parser.add_argument(
      '--protection-level',
      choices=['software', 'hsm', 'external'],
      default='software',
      help='Protection level of the key.')


def AddRequiredProtectionLevelFlag(parser):
  parser.add_argument(
      '--protection-level',
      choices=['software', 'hsm'],
      help='Protection level of the import job.',
      required=True)


def AddAttestationFileFlag(parser):
  parser.add_argument(
      '--attestation-file',
      help='Path to the output attestation file.')


def AddDefaultAlgorithmFlag(parser):
  parser.add_argument(
      '--default-algorithm',
      choices=sorted(maps.ALL_ALGORITHMS),
      help='The default algorithm for the crypto key. For more information '
      'about choosing an algorithm, see '
      'https://cloud.google.com/kms/docs/algorithms.')


def AddRequiredImportMethodFlag(parser):
  parser.add_argument(
      '--import-method',
      choices=sorted(maps.IMPORT_METHOD_MAPPER.choices)[1:],
      help='The wrapping method to be used for incoming key material. For more '
      'information about choosing an import method, see '
      'https://cloud.google.com/kms/docs/key-wrapping.',
      required=True)


def AddOptionalPublicKeyFileArgument(parser):
  parser.add_argument(
      '--public-key-file',
      help='Optional path to the public key of the ImportJob, used to wrap the '
      'key for import. If missing, the public key will be fetched on your '
      'behalf.')


def AddOptionalTargetKeyFileArgument(parser):
  parser.add_argument(
      '--target-key-file',
      help='Optional path to the unwrapped target key to import into a Cloud '
      'KMS key version. If specified, the key will be securely wrapped before '
      'transmission to Google.')


def AddDigestAlgorithmFlag(parser, help_action):
  parser.add_argument(
      '--digest-algorithm',
      choices=sorted(maps.DIGESTS),
      help=help_action,
      required=True)


def AddImportedVersionAlgorithmFlag(parser):
  parser.add_argument(
      '--algorithm',
      choices=sorted(maps.ALGORITHMS_FOR_IMPORT),
      help='The algorithm to assign to the new key version. For more '
      'information about supported algorithms, see '
      'https://cloud.google.com/kms/docs/algorithms.',
      required=True)


def AddExternalKeyUriFlag(parser):
  parser.add_argument(
      '--external-key-uri',
      suggestion_aliases=['--key-uri'],
      help='The URI of the external key for keys with protection level'
      ' "external".')


def AddStateFlag(parser):
  parser.add_argument('--state', dest='state', help='State of the key version.')


# Arguments
def AddKeyRingArgument(parser, help_action):
  parser.add_argument(
      'keyring',
      completer=KeyRingCompleter,
      help='Name of the key ring {0}.'.format(help_action))


def AddCryptoKeyArgument(parser, help_action):
  parser.add_argument(
      'key',
      completer=KeyCompleter,
      help='Name of the key {0}.'.format(help_action))


def AddKeyResourceArgument(parser, help_action):
  AddLocationFlag(parser, 'key')
  AddKeyRingFlag(parser, 'key')
  AddCryptoKeyArgument(parser, help_action)


def AddCryptoKeyVersionArgument(parser, help_action):
  parser.add_argument(
      'version',
      completer=KeyVersionCompleter,
      help='Name of the version {0}.'.format(help_action))


def AddKeyVersionResourceArgument(parser, help_action):
  AddKeyResourceFlags(parser)
  AddCryptoKeyVersionArgument(parser, help_action)


def AddPositionalImportJobArgument(parser, help_action):
  parser.add_argument(
      'import_job',
      completer=ImportJobCompleter,
      help='Name of the import job {0}.'.format(help_action))


def AddRequiredImportJobArgument(parser, help_action):
  parser.add_argument(
      '--import-job',
      completer=ImportJobCompleter,
      help='Name of the import job {0}.'.format(help_action),
      required=True)


# Parsing.
def ParseLocationName(args):
  return resources.REGISTRY.Parse(
      args.location,
      params={'projectsId': properties.VALUES.core.project.GetOrFail},
      collection=LOCATION_COLLECTION)


def ParseKeyRingName(args):
  return resources.REGISTRY.Parse(
      args.keyring,
      params={
          'projectsId': properties.VALUES.core.project.GetOrFail,
          'locationsId': args.MakeGetOrRaise('--location'),
      },
      collection=KEY_RING_COLLECTION)


def ParseCryptoKeyName(args):
  return resources.REGISTRY.Parse(
      args.key,
      params={
          'keyRingsId': args.MakeGetOrRaise('--keyring'),
          'locationsId': args.MakeGetOrRaise('--location'),
          'projectsId': properties.VALUES.core.project.GetOrFail,
      },
      collection=CRYPTO_KEY_COLLECTION)


def ParseCryptoKeyVersionName(args):
  return resources.REGISTRY.Parse(
      args.version,
      params={
          'cryptoKeysId': args.MakeGetOrRaise('--key'),
          'keyRingsId': args.MakeGetOrRaise('--keyring'),
          'locationsId': args.MakeGetOrRaise('--location'),
          'projectsId': properties.VALUES.core.project.GetOrFail,
      },
      collection=CRYPTO_KEY_VERSION_COLLECTION)


def ParseImportJobName(args):
  return resources.REGISTRY.Parse(
      args.import_job,
      params={
          'keyRingsId': args.MakeGetOrRaise('--keyring'),
          'locationsId': args.MakeGetOrRaise('--location'),
          'projectsId': properties.VALUES.core.project.GetOrFail,
      },
      collection=IMPORT_JOB_COLLECTION)


# Get parent type Resource from output of Parse functions above.
def ParseParentFromResource(resource_ref):
  collection_list = resource_ref.Collection().split('.')
  parent_collection = '.'.join(collection_list[:-1])
  params = resource_ref.AsDict()
  del params[collection_list[-1] + 'Id']
  return resources.REGISTRY.Create(parent_collection, **params)


# Set proto fields from flags.
def SetRotationPeriod(args, crypto_key):
  if args.rotation_period is not None:
    crypto_key.rotationPeriod = '{0}s'.format(args.rotation_period)


def SetNextRotationTime(args, crypto_key):
  if args.next_rotation_time is not None:
    crypto_key.nextRotationTime = times.FormatDateTime(args.next_rotation_time)
