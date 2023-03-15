# -*- coding: utf-8 -*-
"""miscellaneous field class"""

import collections
import copy
import io
from typing import TYPE_CHECKING, TypeVar, cast

from pcapkit.corekit.fields.field import NoValue, _Field
from pcapkit.utilities.exceptions import FieldValueError, NoDefaultValue

__all__ = [
    'ConditionalField', 'PayloadField',
    'ListField', 'OptionField',
]

if TYPE_CHECKING:
    from collections import defaultdict
    from enum import IntEnum as StdlibEnum
    from typing import IO, Any, Callable, Optional, Type

    from aenum import IntEnum as AenumEnum

    from pcapkit.corekit.fields.field import Field, NoValueType
    from pcapkit.protocols.protocol import Protocol
    from pcapkit.protocols.schema.schema import Schema

_TC = TypeVar('_TC')
_TP = TypeVar('_TP', bound='Protocol')
_TL = TypeVar('_TL', 'Schema', '_Field', 'bytes')


class ConditionalField(_Field[_TC]):
    """Conditional value for protocol fields.

    Args:
        field: field instance.
        condition: field condition function (this function should return a bool
            value and accept the current packet :class:`pcapkit.corekit.infoclass.Info`
            as its only argument).

    """

    @property
    def name(self) -> 'str':
        """Field name."""
        return self._field.name

    @name.setter
    def name(self, value: 'str') -> 'None':
        """Set field name."""
        self._field.name = value

    @property
    def default(self) -> '_TC | NoValueType':
        """Field default value."""
        return self._field.default

    @default.setter
    def default(self, value: '_TC | NoValueType') -> 'None':
        """Set field default value."""
        self._field.default = value

    @default.deleter
    def default(self) -> 'None':
        """Delete field default value."""
        self._field.default = NoValue

    @property
    def template(self) -> 'str':
        """Field template."""
        return self._field.template

    @property
    def length(self) -> 'int':
        """Field size."""
        return self._field.length

    @property
    def optional(self) -> 'bool':
        """Field is optional."""
        return True

    @property
    def field(self) -> 'Field[_TC]':
        """Field instance."""
        return self._field

    def __init__(self, field: 'Field[_TC]',  # pylint: disable=super-init-not-called
                 condition: 'Callable[[dict[str, Any]], bool]') -> 'None':
        self._field = field  # type: Field[_TC]
        self._condition = condition

    def __call__(self, packet: 'dict[str, Any]') -> 'ConditionalField':
        """Update field attributes.

        Arguments:
            packet: packet data.

        Notes:
            This method will return a new instance of :class:`ConditionalField`
            instead of updating the current instance.

        """
        new_self = copy.copy(self)
        if new_self._condition(packet):
            new_self._field(packet)
        return new_self

    def pre_process(self, value: '_TC', packet: 'dict[str, Any]') -> 'Any':  # pylint: disable=unused-argument
        """Process field value before construction (packing).

        Arguments:
            value: field value.
            packet: packet data.

        Returns:
            Processed field value.

        """
        return self._field.pre_process(value, packet)

    def pack(self, value: 'Optional[_TC]', packet: 'dict[str, Any]') -> 'bytes':
        """Pack field value into :obj:`bytes`.

        Args:
            value: field value.
            packet: packet data.

        Returns:
            Packed field value.

        """
        if not self._condition(packet):
            return b''
        return self._field.pack(value, packet)

    def post_process(self, value: 'Any', packet: 'dict[str, Any]') -> '_TC':  # pylint: disable=unused-argument
        """Process field value after parsing (unpacking).

        Args:
            value: field value.
            packet: packet data.

        Returns:
            Processed field value.

        """
        return self._field.post_process(value, packet)

    def unpack(self, buffer: 'bytes | Schema', packet: 'dict[str, Any]') -> '_TC':
        """Unpack field value from :obj:`bytes`.

        Args:
            buffer: field buffer.
            packet: packet data.

        Returns:
            Unpacked field value.

        """
        if not self._condition(packet):
            return self._field.default  # type: ignore[return-value]
        return self._field.unpack(buffer, packet)

    def test(self, packet: 'dict[str, Any]') -> 'bool':
        """Test field condition.

        Arguments:
            packet: current packet

        Returns:
            bool: test result

        """
        return self._condition(packet)


class PayloadField(_Field[_TP]):
    """Payload value for protocol fields.

    Args:
        length: field size (in bytes); if a callable is given, it should return
            an integer value and accept the current packet as its only argument.
        default: field default value.
        protocol: payload protocol.
        callback: callback function to be called upon
            :meth:`self.__call__ <pcapkit.corekit.fields.field._Field.__call__>`.

    """

    @property
    def template(self) -> 'str':
        """Field template."""
        return self._template

    @property
    def length(self) -> 'int':
        """Field size."""
        return self._length

    @property
    def optional(self) -> 'bool':
        """Field is optional."""
        return True

    @property
    def protocol(self) -> 'Type[_TP]':
        """Payload protocol."""
        if self._protocol is None:
            from pcapkit.protocols.misc.raw import Raw  # type: ignore[unreachable] # pylint: disable=import-outside-top-level # isort:skip
            return Raw
        return self._protocol

    @protocol.setter
    def protocol(self, protocol: 'Type[_TP] | str') -> 'None':
        """Set payload protocol.

        Arguments:
            protocol: payload protocol

        """
        if isinstance(protocol, str):
            from pcapkit.protocols import __proto__  # pylint: disable=import-outside-top-level
            protocol = cast('Type[_TP]', __proto__.get(protocol))
        self._protocol = protocol

    def __init__(self, length: 'int | Callable[[dict[str, Any]], Optional[int]]' = lambda _: None,
                 default: '_TP | NoValueType | bytes' = NoValue,
                 protocol: 'Optional[Type[_TP]]' = None,
                 callback: 'Callable[[PayloadField[_TP], dict[str, Any]], None]' = lambda *_: None) -> 'None':
        self._name = '<payload>'
        self._default = default  # type: ignore[assignment]
        self._protocol = protocol  # type: ignore[assignment]
        self._callback = callback

        self._length_callback = None
        if not isinstance(length, int):
            self._length_callback, length = length, 0
        self._length = length
        self._template = '0s'

    def __call__(self, packet: 'dict[str, Any]') -> 'PayloadField':
        """Update field attributes.

        Args:
            packet: packet data.

        Notes:
            This method will return a new instance of :class:`PayloadField`
            instead of updating the current instance.

        """
        new_self = copy.copy(self)
        new_self._callback(self, packet)
        if new_self._length_callback is not None:
            new_self._length = new_self._length_callback(packet)  # type: ignore[assignment]
        return new_self

    def pack(self, value: 'Optional[_TP | Schema | bytes]', packet: 'dict[str, Any]') -> 'bytes':
        """Pack field value into :obj:`bytes`.

        Args:
            value: field value.
            packet: packet data.

        Returns:
            Packed field value.

        """
        if value is None:
            if self._default is NoValue:
                raise NoDefaultValue(f'Field {self.name} has no default value.')
            value = cast('_TP', self._default)

        from pcapkit.protocols.schema.schema import \
            Schema  # pylint: disable=import-outside-top-level
        if isinstance(value, bytes):
            return value
        if isinstance(value, Schema):
            return value.pack()
        return value.data  # type: ignore[union-attr]

    def unpack(self, buffer: 'bytes | IO[bytes]', packet: 'dict[str, Any]') -> '_TP':  # type: ignore[override]
        """Unpack field value from :obj:`bytes`.

        Args:
            buffer: field buffer.
            packet: packet data.

        Returns:
            Unpacked field value.

        """
        if self._protocol is None:
            if isinstance(buffer, bytes):  # type: ignore[unreachable]
                return cast('_TP', buffer)
            return cast('_TP', buffer.read())

        if isinstance(buffer, bytes):
            file = io.BytesIO(buffer)  # type: IO[bytes]
        else:
            file = buffer
        return self._protocol(file, self.length)  # type: ignore[abstract]


class ListField(_Field[list[_TL]]):
    """Field list for protocol fields.

    Args:
        length: field size (in bytes); if a callable is given, it should return
            an integer value and accept the current packet as its only argument.
        item_type: field type of the contained items.
        callback: callback function to be called upon
            :meth:`self.__call__ <pcapkit.corekit.fields.field._Field.__call__>`.

    This field is used to represent a list of fields, as in the case of lists of
    constrant-length-field items in a protocol.

    """

    @property
    def optional(self) -> 'bool':
        """Field is optional."""
        return True

    def __init__(self, length: 'int | Callable[[dict[str, Any]], Optional[int]]' = lambda _: None,
                 item_type: 'Optional[Field]' = None,
                 callback: 'Callable[[ListField, dict[str, Any]], None]' = lambda *_: None) -> 'None':
        self._name = '<list>'
        self._callback = callback
        self._item_type = item_type

        self._length_callback = None
        if not isinstance(length, int):
            self._length_callback, length = length, -1
        self._length = length
        self._template = '0s'

    def __call__(self, packet: 'dict[str, Any]') -> 'ListField':
        """Update field attributes.

        Args:
            packet: packet data.

        Notes:
            This method will return a new instance of :class:`ListField`
            instead of updating the current instance.

        """
        new_self = copy.copy(self)
        new_self._callback(self, packet)
        if new_self._length_callback is not None:
            new_self._length = new_self._length_callback(packet)  # type: ignore[assignment]
        return new_self

    def pack(self, value: 'Optional[list[_TL]]', packet: 'dict[str, Any]') -> 'bytes':
        """Pack field value into :obj:`bytes`.

        Args:
            value: field value.
            packet: packet data.

        Returns:
            Packed field value.

        """
        if value is None:
            return b''

        from pcapkit.protocols.schema.schema import \
            Schema  # pylint: disable=import-outside-top-level

        temp = []  # type: list[bytes]
        for item in value:
            if isinstance(item, bytes):
                temp.append(item)
            elif isinstance(item, Schema):
                temp.append(item.pack())
            elif self._item_type is not None:
                temp.append(self._item_type.pack(item, packet))
            else:
                raise FieldValueError(f'Field {self.name} has invalid value.')
        return b''.join(temp)

    def unpack(self, buffer: 'bytes | IO[bytes]', packet: 'dict[str, Any]') -> 'bytes | list[_TL]':  # type: ignore[override]
        """Unpack field value from :obj:`bytes`.

        Args:
            buffer: field buffer.
            packet: packet data.

        Returns:
            Unpacked field value.

        """
        length = self.length
        if isinstance(buffer, bytes):
            file = io.BytesIO(buffer)  # type: IO[bytes]
        else:
            file = buffer

        if self._item_type is not None:
            field = self._item_type(packet)

            temp = []  # type: list[_TL]
            while length:
                length -= field.length
                if length < 0:
                    raise FieldValueError(f'Field {self.name} has invalid length.')

                buffer = file.read(field.length)
                temp.append(field.unpack(buffer, packet))
            return temp
        return file.read(length)


class OptionField(ListField):
    """Field list for protocol options.

    Args:
        length: field size (in bytes); if a callable is given, it should return
            an integer value and accept the current packet as its only argument.
        base_schema: base schema for option fields.
        type_name: name of the option type field.
        registry: option registry, as in a mapping from option types (enumeration
            values) to option schemas, with the default value being the unknown
            option schema.
        callback: callback function to be called upon
            :meth:`self.__call__ <pcapkit.corekit.fields.field._Field.__call__>`.

    This field is used to represent a list of fields, as in the case of lists of
    options and/or parameters in a protocol.

    """

    @property
    def base_schema(self) -> 'Type[Schema]':
        """Base schema."""
        return self._base_schema

    @property
    def type_name(self) -> 'str':
        """Type name."""
        return self._type_name

    @property
    def registry(self) -> 'dict[int, Type[Schema]]':
        """Option registry."""
        return self._registry

    def __init__(self, length: 'int | Callable[[dict[str, Any]], Optional[int]]' = lambda _: None,
                 base_schema: 'Optional[Type[Schema]]' = None,
                 type_name: 'str' = 'type',
                 registry: 'Optional[defaultdict[int | StdlibEnum | AenumEnum, Type[Schema]]]' = None,
                 callback: 'Callable[[ListField, dict[str, Any]], None]' = lambda *_: None) -> 'None':
        super().__init__(length, None, callback)
        self._name = '<option>'

        if base_schema is None:
            raise FieldValueError('Field <option> has no base schema.')
        self._base_schema = base_schema

        if not hasattr(self._base_schema, type_name):
            raise FieldValueError(f'Field <option> has no type field "{type_name}".')
        self._type_name = type_name

        if registry is None:
            raise FieldValueError('Field <option> has no registry.')
        self._registry = registry

    def unpack(self, buffer: 'bytes | IO[bytes]', packet: 'dict[str, Any]') -> 'list[Schema]':  # type: ignore[override]
        """Unpack field value from :obj:`bytes`.

        Args:
            buffer: field buffer.
            packet: packet data.

        Returns:
            Unpacked field value.

        """
        length = self.length
        if isinstance(buffer, bytes):
            file = io.BytesIO(buffer)  # type: IO[bytes]
        else:
            file = buffer

        temp = []  # type: list[Schema]
        while length:
            # unpack option type using base schema
            meta = self._base_schema.unpack(file, length, packet)
            code = cast('int', meta[self._type_name])
            schema = self._registry[code]

            # rewind to the beginning of the option
            file.seek(-len(meta), io.SEEK_CUR)

            # unpack option using option schema
            data = schema.unpack(file, length, packet)
            temp.append(data)

            # update length
            length -= len(data)
        return temp
