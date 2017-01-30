# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from sqlalchemy import (
    Column,
    Text
)

from ...parser.modeling import utils
from ...utils.collections import OrderedDict
from ...utils.console import puts

from . import structure
from . import type

# pylint: disable=no-self-argument, no-member, abstract-method


class ParameterBase(structure.ModelElementBase, structure.ModelMixin):
    """
    Represents a typed value.

    This class is used by both service model and service instance elements.
    """
    __tablename__ = 'parameter'
    name = Column(Text, nullable=False)
    type = Column(Text, nullable=False)

    # Check: value type
    value = Column(Text)
    description = Column(Text)

    @property
    def as_raw(self):
        return OrderedDict((
            ('name', self.name),
            ('type_name', self.type),
            ('value', self._cast_value()),
            ('description', self.description)))

    # TODO: change name
    def _cast_value(self):
        if self.type is None:
            return

        if self.type.lower() == 'str':
            return str(self.value)
        elif self.type.lower() == 'int':
            return int(self.value)
        elif self.type.lower() == 'bool':
            return bool(self.value)
        elif self.type.lower() == 'float':
            return float(self.value)
        else:
            raise Exception('No supported type_name was provided')

    def instantiate(self, context, container):
        return ParameterBase(self.type, self.value, self.description)

    def coerce_values(self, context, container, report_issues):
        if self.value is not None:
            self.value = utils.coerce_value(context, container, self.value, report_issues)


class MetadataBase(structure.ModelElementBase, structure.ModelMixin):
    """
    Custom values associated with the deployment template and its plans.

    This class is used by both service model and service instance elements.

    Properties:

    * :code:`values`: Dict of custom values
    """
    values = Column(type.StrictDict(key_cls=basestring))

    @property
    def as_raw(self):
        return self.values

    def instantiate(self, context, container):
        metadata = MetadataBase()
        metadata.values.update(self.values)
        return metadata

    def dump(self, context):
        puts('Metadata:')
        with context.style.indent:
            for name, value in self.values.iteritems():
                puts('%s: %s' % (name, context.style.meta(value)))
