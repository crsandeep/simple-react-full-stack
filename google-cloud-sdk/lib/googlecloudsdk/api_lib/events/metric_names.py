# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""Events CSI metric names."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

# Reserved CSI metric prefix for eventflow
_EVENTS_PREFIX = 'events_'

# Time to get a trigger
GET_TRIGGER = _EVENTS_PREFIX + 'get_trigger'

# Time to create a trigger
CREATE_TRIGGER = _EVENTS_PREFIX + 'create_trigger'

# Time to list triggers
LIST_TRIGGERS = _EVENTS_PREFIX + 'list_triggers'

# Time to delete a trigger
DELETE_TRIGGER = _EVENTS_PREFIX + 'delete_trigger'

# Time to get a source
GET_SOURCE = _EVENTS_PREFIX + 'get_source'

# Time to create a source
CREATE_SOURCE = _EVENTS_PREFIX + 'create_source'

# Time to delete a source
DELETE_SOURCE = _EVENTS_PREFIX + 'delete_source'

# Time to list source CRDs
LIST_SOURCE_CRDS = _EVENTS_PREFIX + 'list_source_crds'

# Time to update a namespace
UPDATE_NAMESPACE = _EVENTS_PREFIX + 'update_namespace'

# Time to create a secret
CREATE_OR_REPLACE_SECRET = _EVENTS_PREFIX + 'create_or_replace_secret'
