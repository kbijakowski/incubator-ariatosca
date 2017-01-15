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
import json
from collections import namedtuple
from types import NoneType

from sqlalchemy import (
    TypeDecorator,
    VARCHAR
)

from sqlalchemy.ext import mutable

from . import exceptions


class _MutableType(TypeDecorator):
    """
    Dict representation of type.
    """
    @property
    def python_type(self):
        raise NotImplementedError

    def process_literal_param(self, value, dialect):
        pass

    impl = VARCHAR

    def process_bind_param(self, value, dialect):
        if value is not None:
            value = json.dumps(value)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            value = json.loads(value)
        return value


class Dict(_MutableType):
    @property
    def python_type(self):
        return dict


class List(_MutableType):
    @property
    def python_type(self):
        return list


class _StrictDictMixin(object):
    ANY_TYPE = 'any_type'

    _key_cls = ANY_TYPE
    _value_cls = ANY_TYPE

    @classmethod
    def coerce(cls, key, value):
        "Convert plain dictionaries to MutableDict."
        try:
            if not isinstance(value, cls):
                if isinstance(value, dict):
                    for k, v in value.items():
                        cls._assert_strict_key(k)
                        cls._assert_strict_value(v)
                    return cls(value)
                return mutable.MutableDict.coerce(key, value)
            else:
                return value
        except ValueError as e:
            raise exceptions.StorageError('SQL Storage error: {0}'.format(str(e)))

    def __setitem__(self, key, value):
        self._assert_strict_key(key)
        self._assert_strict_value(value)
        super(_StrictDictMixin, self).__setitem__(key, value)

    def setdefault(self, key, value):
        self._assert_strict_key(key)
        self._assert_strict_value(value)
        super(_StrictDictMixin, self).setdefault(key, value)

    def update(self, *a, **kw):
        if isinstance(a, dict):
            for k, v in a.items():
                self._assert_strict_key(k)
                self._assert_strict_value(v)
        for k, v in kw.items():
            self._assert_strict_key(k)
            self._assert_strict_value(v)
        super(_StrictDictMixin, self).update(*a, **kw)

    @classmethod
    def _assert_strict_key(cls, key):
        if not isinstance(key, cls._key_cls):
            raise exceptions.StorageError("Key type was set strictly to {0}, but was {1}".format(
                cls._key_cls, type(key)
            ))

    @classmethod
    def _assert_strict_value(cls, value):
        if not isinstance(value, cls._value_cls):
            raise exceptions.StorageError("Value type was set strictly to {0}, but was {1}".format(
                cls._value_cls, type(value)
            ))


class _MutableDict(mutable.MutableDict):
    """
    Enables tracking for dict values.
    """

    @classmethod
    def coerce(cls, key, value):
        "Convert plain dictionaries to MutableDict."
        try:
            return mutable.MutableDict.coerce(key, value)
        except ValueError as e:
            raise exceptions.StorageError('SQL Storage error: {0}'.format(str(e)))


class _StrictListMixin(object):
    ANY_TYPE = 'any_type'

    _item_cls = ANY_TYPE

    @classmethod
    def coerce(cls, key, value):
        "Convert plain dictionaries to MutableDict."
        try:
            if not isinstance(value, cls):
                if isinstance(value, list):
                    for item in value:
                        cls._assert_item(item)
                    return cls(value)
                return mutable.MutableList.coerce(key, value)
            else:
                return value
        except ValueError as e:
            raise exceptions.StorageError('SQL Storage error: {0}'.format(str(e)))

    def __setitem__(self, index, value):
        """Detect list set events and emit change events."""
        self._assert_item(value)
        super(_StrictListMixin, self).__setitem__(index, value)

    def append(self, x):
        self._assert_item(x)
        super(_StrictListMixin, self).append(x)

    def extend(self, x):
        self._assert_item(x)
        super(_StrictListMixin, self).extend(x)

    def insert(self, i, x):
        self._assert_item(x)
        super(_StrictListMixin, self).insert(i, x)

    @classmethod
    def _assert_item(cls, item):
        if not isinstance(item, cls._item_cls):
            raise exceptions.StorageError("Key type was set strictly to {0}, but was {1}".format(
                cls._item_cls, type(item)
            ))


class _MutableList(mutable.MutableList):

    @classmethod
    def coerce(cls, key, value):
        "Convert plain dictionaries to MutableDict."

        try:
            if not isinstance(value, cls):
                if isinstance(value, list):
                    return cls(value)

                return mutable.Mutable.coerce(key, value)
            else:
                return value

        except ValueError as e:
            raise exceptions.StorageError('SQL Storage error: {0}'.format(str(e)))

_strict_dict_id = namedtuple('strict_dict_id', 'key_cls, value_cls')
_strict_map = {}


def StrictDict(key_cls, value_cls):
    strict_dict_map_key = _strict_dict_id(key_cls=key_cls, value_cls=value_cls)
    if strict_dict_map_key not in _strict_map:
        strict_dict_cls = type(
            'StrictDict_{0}_{1}'.format(key_cls.__name__, value_cls.__name__),
            (Dict, ),
            {}
        )
        type(
            'StrictMutableDict_{0}_{1}'.format(key_cls.__name__, value_cls.__name__),
            (_StrictDictMixin, _MutableDict),
            {'_key_cls': key_cls, '_value_cls': value_cls}
        ).associate_with(strict_dict_cls)
        _strict_map[strict_dict_map_key] = strict_dict_cls

    return _strict_map[strict_dict_map_key]


def StrictList(item_cls):
    if item_cls not in _strict_map:
        strict_list_cls = type(
            'StrictList_{0}'.format(item_cls.__name__),
            (List, ),
            {}
        )
        type(
            'StrictMutableList_{0}'.format(item_cls.__name__),
            (_StrictListMixin, _MutableList),
            {'_item_cls': item_cls}
        ).associate_with(strict_list_cls)
        _strict_map[item_cls] = strict_list_cls

    return _strict_map[item_cls]

_MutableList.associate_with(List)
_MutableDict.associate_with(Dict)
