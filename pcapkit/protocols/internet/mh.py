# -*- coding: utf-8 -*-
# pylint: disable=fixme
"""mobility header

:mod:`pcapkit.protocols.internet.mh` contains
:class:`~pcapkit.protocols.internet.mh.MH` only,
which implements extractor for Mobility Header
(MH) [*]_, whose structure is described as below:

======= ========= ================== ===============================
Octets      Bits        Name                    Description
======= ========= ================== ===============================
  0           0   ``mh.next``                 Next Header
  1           8   ``mh.length``               Header Length
  2          16   ``mh.type``                 Mobility Header Type
  3          24                               Reserved
  4          32   ``mh.chksum``               Checksum
  6          48   ``mh.data``                 Message Data
======= ========= ================== ===============================

.. [*] https://en.wikipedia.org/wiki/Mobile_IP#Changes_in_IPv6_for_Mobile_IPv6

"""
import collections
import datetime
import ipaddress
import math
from tokenize import Name
from typing import TYPE_CHECKING, cast, overload

from pcapkit.const.mh.access_type import AccessType as Enum_AccessType
from pcapkit.const.mh.ack_status_code import ACKStatusCode as Enum_ACKStatusCode
from pcapkit.const.mh.ani_suboption import ANISuboption as Enum_ANISuboption
from pcapkit.const.mh.auth_subtype import AuthSubtype as Enum_AuthSubtype
from pcapkit.const.mh.binding_ack_flag import BindingACKFlag as Enum_BindingACKFlag
from pcapkit.const.mh.binding_revocation import BindingRevocation as Enum_BindingRevocation
from pcapkit.const.mh.binding_update_flag import BindingUpdateFlag as Enum_BindingUpdateFlag
from pcapkit.const.mh.cga_extension import CGAExtension as Enum_CGAExtension
from pcapkit.const.mh.cga_type import CGAType as Enum_CGAType
from pcapkit.const.mh.dhcp_support_mode import DHCPSupportMode as Enum_DHCPSupportMode
from pcapkit.const.mh.dns_status_code import DNSStatusCode as Enum_DNSStatusCode
from pcapkit.const.mh.dsmip6_tls_packet import DSMIP6TLSPacket as Enum_DSMIP6TLSPacket
from pcapkit.const.mh.dsmipv6_home_address import DSMIPv6HomeAddress as Enum_DSMIPv6HomeAddress
from pcapkit.const.mh.enumerating_algorithm import EnumeratingAlgorithm as Enum_EnumeratingAlgorithm
from pcapkit.const.mh.fb_ack_status import FlowBindingACKStatus as Enum_FlowBindingACKStatus
from pcapkit.const.mh.fb_action import FlowBindingAction as Enum_FlowBindingAction
from pcapkit.const.mh.fb_indication_trigger import \
    FlowBindingIndicationTrigger as Enum_FlowBindingIndicationTrigger
from pcapkit.const.mh.fb_type import FlowBindingType as Enum_FlowBindingType
from pcapkit.const.mh.flow_id_status import FlowIDStatus as Enum_FlowIDStatus
from pcapkit.const.mh.flow_id_suboption import FlowIDSuboption as Enum_FlowIDSuboption
from pcapkit.const.mh.handoff_type import HandoffType as Enum_HandoffType
from pcapkit.const.mh.handover_ack_flag import HandoverACKFlag as Enum_HandoverACKFlag
from pcapkit.const.mh.handover_ack_status import HandoverACKStatus as Enum_HandoverACKStatus
from pcapkit.const.mh.handover_initiate_flag import \
    HandoverInitiateFlag as Enum_HandoverInitiateFlag
from pcapkit.const.mh.home_address_reply import HomeAddressReply as Enum_HomeAddressReply
from pcapkit.const.mh.lla_code import LLACode as Enum_LLACode
from pcapkit.const.mh.lma_mag_suboption import \
    LMAControlledMAGSuboption as Enum_LMAControlledMAGSuboption
from pcapkit.const.mh.mn_group_id import MNGroupID as Enum_MNGroupID
from pcapkit.const.mh.mn_id_subtype import MNIDSubtype as Enum_MNIDSubtype
from pcapkit.const.mh.operator_id import OperatorID as Enum_OperatorID
from pcapkit.const.mh.option import Option as Enum_Option
from pcapkit.const.mh.packet import Packet as Enum_Packet
from pcapkit.const.mh.qos_attribute import QoSAttribute as Enum_QoSAttribute
from pcapkit.const.mh.revocation_status_code import \
    RevocationStatusCode as Enum_RevocationStatusCode
from pcapkit.const.mh.revocation_trigger import RevocationTrigger as Enum_RevocationTrigger
from pcapkit.const.mh.status_code import StatusCode as Enum_StatusCode
from pcapkit.const.mh.traffic_selector import TrafficSelector as Enum_TrafficSelector
from pcapkit.const.mh.upa_status import \
    UpdateNotificationACKStatus as Enum_UpdateNotificationACKStatus
from pcapkit.const.mh.upn_reason import UpdateNotificationReason as Enum_UpdateNotificationReason
from pcapkit.const.reg.transtype import TransType as Enum_TransType
from pcapkit.protocols.data.internet.mh import MH as Data_MH
from pcapkit.protocols.data.internet.mh import \
    AlternateCareofAddressOption as Data_AlternateCareofAddressOption
from pcapkit.protocols.data.internet.mh import AuthOption as Data_AuthOption
from pcapkit.protocols.data.internet.mh import \
    BindingAuthorizationDataOption as Data_BindingAuthorizationDataOption
from pcapkit.protocols.data.internet.mh import \
    BindRefreshAdviceOption as Data_BindRefreshAdviceOption
from pcapkit.protocols.data.internet.mh import CGAExtension as Data_CGAExtension
from pcapkit.protocols.data.internet.mh import CGAParameter as Data_CGAParameter
from pcapkit.protocols.data.internet.mh import CGAParametersOption as Data_CGAParametersOption
from pcapkit.protocols.data.internet.mh import \
    CGAParametersRequestOption as Data_CGAParametersRequestOption
from pcapkit.protocols.data.internet.mh import LinkLayerAddressOption as Data_LinkLayerAddressOption
from pcapkit.protocols.data.internet.mh import MesgIDOption as Data_MesgIDOption
from pcapkit.protocols.data.internet.mh import MNIDOption as Data_MNIDOption
from pcapkit.protocols.data.internet.mh import \
    MobileNetworkPrefixOption as Data_MobileNetworkPrefixOption
from pcapkit.protocols.data.internet.mh import MultiPrefixExtension as Data_MultiPrefixExtension
from pcapkit.protocols.data.internet.mh import NonceIndicesOption as Data_NonceIndicesOption
from pcapkit.protocols.data.internet.mh import PadOption as Data_PadOption
from pcapkit.protocols.data.internet.mh import UnassignedOption as Data_UnassignedOption
from pcapkit.protocols.data.internet.mh import UnknownExtension as Data_UnknownExtension
from pcapkit.protocols.internet.internet import Internet
from pcapkit.protocols.schema.internet.mh import MH as Schema_MH
from pcapkit.protocols.schema.internet.mh import \
    AlternateCareofAddressOption as Schema_AlternateCareofAddressOption
from pcapkit.protocols.schema.internet.mh import AuthOption as Schema_AuthOption
from pcapkit.protocols.schema.internet.mh import \
    BindingAuthorizationDataOption as Schema_BindingAuthorizationDataOption
from pcapkit.protocols.schema.internet.mh import \
    BindRefreshAdviceOption as Schema_BindRefreshAdviceOption
from pcapkit.protocols.schema.internet.mh import CGAExtension as Schema_CGAExtension
from pcapkit.protocols.schema.internet.mh import CGAParameter as Schema_CGAParameter
from pcapkit.protocols.schema.internet.mh import CGAParametersOption as Schema_CGAParametersOption
from pcapkit.protocols.schema.internet.mh import \
    CGAParametersRequestOption as Schema_CGAParametersRequestOption
from pcapkit.protocols.schema.internet.mh import \
    LinkLayerAddressOption as Schema_LinkLayerAddressOption
from pcapkit.protocols.schema.internet.mh import MesgIDOption as Schema_MesgIDOption
from pcapkit.protocols.schema.internet.mh import MNIDOption as Schema_MNIDOption
from pcapkit.protocols.schema.internet.mh import \
    MobileNetworkPrefixOption as Schema_MobileNetworkPrefixOption
from pcapkit.protocols.schema.internet.mh import MultiPrefixExtension as Schema_MultiPrefixExtension
from pcapkit.protocols.schema.internet.mh import NonceIndicesOption as Schema_NonceIndicesOption
from pcapkit.protocols.schema.internet.mh import PadOption as Schema_PadOption
from pcapkit.protocols.schema.internet.mh import UnassignedOption as Schema_UnassignedOption
from pcapkit.protocols.schema.internet.mh import UnknownExtension as Schema_UnknownExtension
from pcapkit.utilities.exceptions import ProtocolError, UnsupportedCall
from pcapkit.utilities.warnings import ProtocolWarning, warn

if TYPE_CHECKING:
    from datetime import datetime as dt_type
    from enum import IntEnum as StdlibEnum
    from ipaddress import IPv6Address, IPv6Network
    from typing import IO, Any, Callable, DefaultDict, NoReturn, Optional, Type

    from aenum import IntEnum as AenumEnum
    from mypy_extensions import DefaultArg, KwArg, NamedArg
    from typing_extensions import Literal

    from pcapkit.corekit.multidict import OrderedMultiDict
    from pcapkit.corekit.protochain import ProtoChain
    from pcapkit.protocols.data.internet.mh import Option as Data_Option
    from pcapkit.protocols.protocol import Protocol
    from pcapkit.protocols.schema.internet.mh import Option as Schema_Option
    from pcapkit.protocols.schema.internet.mh import Packet as Schema_Packet
    from pcapkit.protocols.schema.schema import Schema

    Option = OrderedMultiDict[Enum_Option, Data_Option]
    Extension = OrderedMultiDict[Enum_CGAExtension, Data_CGAExtension]

    PacketParser = Callable[[Schema_Packet, NamedArg(Schema_MH, 'header')], Data_MH]
    PacketConstructor = Callable[[Enum_Packet, DefaultArg(Optional[Data_MH]),
                                 KwArg(Any)], Schema_Packet]

    OptionParser = Callable[[Schema_Option, NamedArg(Option, 'options')], Data_Option]
    OptionConstructor = Callable[[Enum_Option, DefaultArg(Optional[Data_Option]),
                                  KwArg(Any)], Schema_Option]

    ExtensionParser = Callable[[Schema_CGAExtension, NamedArg(Extension, 'extensions')], Data_CGAExtension]
    ExtensionConstructor = Callable[[Enum_CGAExtension, DefaultArg(Optional[Data_CGAExtension]),
                                     KwArg(Any)], Schema_CGAExtension]

__all__ = ['MH']

NTPTimestamp = collections.namedtuple('NTPTimestamp', 'seconds fraction')
NTPTimestamp.__doc__ = """NTP timestamp format, c.f., :rfc:`1305`."""


class MH(Internet[Data_MH, Schema_MH],
         schema=Schema_MH, data=Data_MH):
    """This class implements Mobility Header."""

    ##########################################################################
    # Defaults.
    ##########################################################################

    #: DefaultDict[Enum_Packet, str | tuple[PacketParser, PacketConstructor]]:
    #: Message type to method mapping. Method names are expected to be referred
    #: to the class by ``_read_packet_${name}`` and/or ``_make_packet_${name}``,
    #: and if such name not found, the value should then be a method that can
    #: parse the packet by itself.
    __packet__ = collections.defaultdict(
        lambda: 'unknown',
        {

        },
    )  # type: DefaultDict[Enum_Packet | int, str | tuple[PacketParser, PacketConstructor]]

    #: DefaultDict[Enum_Option, str | tuple[OptionParser, OptionConstructor]]:
    #: Option type to method mapping. Method names are expected to be referred
    #: to the class by ``_read_option_${name}`` and/or ``_make_opt_${name}``,
    #: and if such name not found, the value should then be a method that can
    #: parse the option by itself.
    __option__ = collections.defaultdict(
        lambda: 'none',
        {
            Enum_Option.Pad1: 'pad',
            Enum_Option.PadN: 'pad',
            Enum_Option.Binding_Refresh_Advice: 'bra',
            Enum_Option.Alternate_Care_of_Address: 'aca',
            Enum_Option.Nonce_Indices: 'ni',
            Enum_Option.Authorization_Data: 'bad',
            Enum_Option.Mobile_Network_Prefix_Option: 'mnp',
            Enum_Option.Mobility_Header_Link_Layer_Address_option: 'lla',
            Enum_Option.MN_ID_OPTION_TYPE: 'mn_id',
            Enum_Option.AUTH_OPTION_TYPE: 'auth',
            Enum_Option.MESG_ID_OPTION_TYPE: 'mesg_id',
            Enum_Option.CGA_Parameters_Request: 'cga_pr',
            Enum_Option.CGA_Parameters: 'cga_param',
        },
    )  # type: DefaultDict[Enum_Option | int, str | tuple[OptionParser, OptionConstructor]]

    #: DefaultDict[Enum_CGAExtension, str | tuple[ExtensionParser, ExtensionConstructor]]:
    #: CGA extension type to method mapping. Method names are expected to be referred
    #: to the class by ``_read_extension_${name}`` and/or ``_make_ext_${name}``,
    #: and if such name not found, the value should then be a method that can
    #: parse the CGA extension by itself.
    __extension__ = collections.defaultdict(
        lambda: 'none',
        {
            Enum_CGAExtension.Multi_Prefix: 'multiprefix',
        },
    )  # type: DefaultDict[Enum_CGAExtension | int, str | tuple[ExtensionParser, ExtensionConstructor]]

    ##########################################################################
    # Properties.
    ##########################################################################

    @property
    def name(self) -> 'Literal["Mobility Header"]':
        """Name of current protocol."""
        return 'Mobility Header'

    @property
    def length(self) -> 'int':
        """Header length of current protocol."""
        return self._info.length

    @property
    def payload(self) -> 'Protocol | NoReturn':
        """Payload of current instance.

        Raises:
            UnsupportedCall: if the protocol is used as an IPv6 extension header

        """
        if self._extf:
            raise UnsupportedCall(f"'{self.__class__.__name__}' object has no attribute 'payload'")
        return super().payload

    @property
    def protocol(self) -> 'Optional[str] | NoReturn':
        """Name of next layer protocol (if any).

        Raises:
            UnsupportedCall: if the protocol is used as an IPv6 extension header

        """
        if self._extf:
            raise UnsupportedCall(f"'{self.__class__.__name__}' object has no attribute 'protocol'")
        return super().protocol

    @property
    def protochain(self) -> 'ProtoChain | NoReturn':
        """Protocol chain of current instance.

        Raises:
            UnsupportedCall: if the protocol is used as an IPv6 extension header

        """
        if self._extf:
            raise UnsupportedCall(f"'{self.__class__.__name__}' object has no attribute 'protochain'")
        return super().protochain

    ##########################################################################
    # Methods.
    ##########################################################################

    def read(self, length: 'Optional[int]' = None, *, version: 'Literal[4, 6]' = 4,  # pylint: disable=arguments-differ,unused-argument
             extension: bool = False, **kwargs: 'Any') -> 'Data_MH':  # pylint: disable=unused-argument
        """Read Mobility Header.

        Structure of MH header [:rfc:`6275`]:

        .. code-block:: text

           +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
           | Payload Proto |  Header Len   |   MH Type     |   Reserved    |
           +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
           |           Checksum            |                               |
           +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+                               |
           |                                                               |
           .                                                               .
           .                       Message Data                            .
           .                                                               .
           |                                                               |
           +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

        Args:
            length: Length of packet data.
            version: IP protocol version.
            extension: If the protocol is used as an IPv6 extension header.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            Parsed packet data.

        """
        if length is None:
            length = len(self)
        schema = self.__header__

        mh = Data_MH(
            next=schema.next,
            length=(schema.length + 1) * 8,
            type=schema.type,
            chksum=schema.chksum,
            data=schema.data,
        )

        if extension:
            return mh
        return self._decode_next_layer(mh, schema.next, length - mh.length)

    def make(self,
             next: 'Enum_TransType | StdlibEnum | AenumEnum | str | int' = Enum_TransType.UDP,
             next_default: 'Optional[int]' = None,
             next_namespace: 'Optional[dict[str, int] | dict[int, str] | Type[StdlibEnum] | Type[AenumEnum]]' = None,  # pylint: disable=line-too-long
             next_reversed: 'bool' = False,
             type: 'Enum_Packet | StdlibEnum | AenumEnum | str | int' = Enum_Packet.Binding_Refresh_Request,
             type_default: 'Optional[int]' = None,
             type_namespace: 'Optional[dict[str, int] | dict[int, str] | Type[StdlibEnum] | Type[AenumEnum]]' = None,  # pylint: disable=line-too-long
             type_reversed: 'bool' = False,
             chksum: 'bytes' = b'',
             data: 'bytes' = b'\x00\x00',  # minimum length
             payload: 'Protocol | Schema | bytes' = b'',
             **kwargs: 'Any') -> 'Schema_MH':
        """Make (construct) packet data.

        Args:
            **kwargs: Arbitrary keyword arguments.

        Returns:
            Constructed packet data.

        """
        next_val = self._make_index(next, next_default, namespace=next_namespace,  # type: ignore[call-overload]
                                    reversed=next_reversed, pack=False)
        type_val = self._make_index(type, type_default, namespace=type_namespace,  # type: ignore[call-overload]
                                    reversed=type_reversed, pack=False)

        return Schema_MH(
            next=next_val,
            length=math.ceil((len(data) + 6) / 8) - 1,
            type=type_val,
            chksum=chksum,
            data=data,
            payload=payload,
        )

    ##########################################################################
    # Data models.
    ##########################################################################

    @overload
    def __post_init__(self, file: 'IO[bytes] | bytes', length: 'Optional[int]' = ..., *,  # pylint: disable=arguments-differ
                      extension: 'bool' = ..., **kwargs: 'Any') -> 'None': ...

    @overload
    def __post_init__(self, **kwargs: 'Any') -> 'None': ...  # pylint: disable=arguments-differ

    def __post_init__(self, file: 'Optional[IO[bytes] | bytes]' = None, length: 'Optional[int]' = None, *,  # pylint: disable=arguments-differ
                      extension: 'bool' = False, **kwargs: 'Any') -> 'None':
        """Post initialisation hook.

        Args:
            file: Source packet stream.
            length: Length of packet data.
            extension: If the protocol is used as an IPv6 extension header.
            **kwargs: Arbitrary keyword arguments.

        See Also:
            For construction argument, please refer to :meth:`make`.

        """
        #: bool: If the protocol is used as an IPv6 extension header.
        self._extf = extension

        # call super __post_init__
        super().__post_init__(file, length, extension=extension, **kwargs)  # type: ignore[arg-type]

    def __length_hint__(self) -> 'Literal[6]':
        """Return an estimated length for the object."""
        return 6

    @classmethod
    def __index__(cls) -> 'Enum_TransType':  # pylint: disable=invalid-index-returned
        """Numeral registry index of the protocol.

        Returns:
            Numeral registry index of the protocol in `IANA`_.

        .. _IANA: https://www.iana.org/assignments/protocol-numbers/protocol-numbers.xhtml

        """
        return Enum_TransType.Mobility_Header  # type: ignore[return-value]

    ##########################################################################
    # Utilities.
    ##########################################################################

    @classmethod
    def _make_data(cls, data: 'Data_MH') -> 'dict[str, Any]':  # type: ignore[override]
        """Create key-value pairs from ``data`` for protocol construction.

        Args:
            data: protocol data

        Returns:
            Key-value pairs for protocol construction.

        """
        return {
            'next': data.next,
            'type': data.type,
            'chksum': data.chksum,
            'data': data.data,
            'payload': cls._make_payload(data),
        }

    def _read_mh_options(self, options_schema: 'list[Schema_Option]') -> 'Option':
        """Read MH options.

        Structure of MH option [:rfc:`6275`]:

        .. code-block:: text

            0                   1                   2                   3
            0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
           +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
           |  Option Type  | Option Length |   Option Data...
           +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

        Args:
            options_schema: Parsed MH options.

        Returns:
            Parsed MH options data.

        """
        options = OrderedMultiDict()  # type: Option

        for schema in options_schema:
            type = schema.type
            name = self.__option__[type]

            if isinstance(name, str):
                meth_name = f'_read_opt_{name}'
                meth = cast('OptionParser',
                            getattr(self, meth_name, self._read_opt_none))
            else:
                meth = name[0]
            data = meth(schema, options=options)

            # record option data
            options.add(type, data)

        return options

    def _read_opt_none(self, schema: 'Schema_UnassignedOption', *
                             options: 'Option') -> 'Data_UnassignedOption':
        """Read MH unassigned option.

        Args:
            schema: Parsed option schema.
            options: Parsed MH options.

        Returns:
            Constructed option data.

        """
        data = Data_UnassignedOption(
            type=schema.type,
            length=schema.length + 2,
            data=schema.data,
        )
        return data

    def _read_opt_pad(self, schema: 'Schema_PadOption', *,
                      options: 'Option') -> 'Data_PadOption':
        """Read MH padding option.

        Structure of MH padding option [:rfc:`6275`]:

        * ``Pad1`` option:

          .. code-block:: text

              0
              0 1 2 3 4 5 6 7
             +-+-+-+-+-+-+-+-+
             |   Type = 0    |
             +-+-+-+-+-+-+-+-+

        * ``PadN`` option:

          .. code-block:: text

              0                   1
              0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5
             +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+- - - - - - - - -
             |   Type = 1    | Option Length | Option Data
             +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+- - - - - - - - -

        Args:
            schema: Parsed option schema.
            options: Parsed MH options.

        Returns:
            Constructed option data.

        """
        code, clen = schema.type, schema.length

        if code not in (Enum_Option.Pad1, Enum_Option.PadN):
            raise ProtocolError(f'{self.alias}: [OptNo {code}] invalid format')
        if code == Enum_Option.Pad1 and clen != 0:
            raise ProtocolError(f'{self.alias}: [OptNo {code}] invalid format')
        if code == Enum_Option.PadN and clen == 0:
            raise ProtocolError(f'{self.alias}: [OptNo {code}] invalid format')

        if code == Enum_Option.Pad1:
            size = 1
        else:
            size = clen + 2

        data = Data_PadOption(
            type=schema.type,
            length=size,
        )
        return data

    def _read_opt_bra(self, schema: 'Schema_BindRefreshAdviceOption', *,
                      options: 'Option') -> 'Data_BindRefreshAdviceOption':
        """Read MH binding refresh advice option.

        Structure of MH Binding Refresh Advice option [:rfc:`6275`]:

        .. code-block:: text

            0                   1                   2                   3
            0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
                                           +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
                                           |   Type = 2    |   Length = 2  |
           +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
           |       Refresh Interval        |
           +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

        Args:
            schema: Parsed option schema.
            options: Parsed MH options.

        Returns:
            Constructed option data.

        """
        if schema.length != 2:
            raise ProtocolError(f'{self.alias}: [Opt {schema.type}] invalid format')

        data = Data_BindRefreshAdviceOption(
            type=schema.type,
            length=schema.length + 2,
            interval=schema.interval,
        )
        return data

    def _read_opt_aca(self, schema: 'Schema_AlternateCareofAddressOption', *,
                      options: 'Option') -> 'Data_AlternateCareofAddressOption':
        """Read MH alternate care-of address option.

        Structure of MH Alternate Care-of Address option [:rfc:`6275`]:

        .. code-block:: text

            0                   1                   2                   3
            0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
                                           +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
                                           |   Type = 3    |  Length = 16  |
           +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
           |                                                               |
           +                                                               +
           |                                                               |
           +                   Alternate Care-of Address                   +
           |                                                               |
           +                                                               +
           |                                                               |
           +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

        Args:
            schema: Parsed option schema.
            options: Parsed MH options.

        Returns:
            Constructed option data.

        """
        if schema.length != 16:
            raise ProtocolError(f'{self.alias}: [Opt {schema.type}] invalid format')

        data = Data_AlternateCareofAddressOption(
            type=schema.type,
            length=schema.length + 2,
            address=schema.address,
        )
        return data

    def _read_opt_ni(self, schema: 'Schema_NonceIndicesOption', *,
                     options: 'Option') -> 'Data_NonceIndicesOption':
        """Read MH nonce indices option.

        Structure of MH Nonce Indices option [:rfc:`6275`]:

        .. code-block:: text

            0                   1                   2                   3
            0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
                                           +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
                                           |   Type = 4    |   Length = 4  |
           +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
           |         Home Nonce Index      |     Care-of Nonce Index       |
           +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

        Args:
            schema: Parsed option schema.
            options: Parsed MH options.

        Returns:
            Constructed option data.

        """
        if schema.length != 4:
            raise ProtocolError(f'{self.alias}: [Opt {schema.type}] invalid format')

        data = Data_NonceIndicesOption(
            type=schema.type,
            length=schema.length + 2,
            home=schema.home,
            careof=schema.careof,
        )
        return data

    def _read_opt_bad(self, schema: 'Schema_BindingAuthorizationDataOption', *,
                      options: 'Option') -> 'Data_BindingAuthorizationDataOption':
        """Read MH binding authorization data option.

        Structure of MH Binding Authorization Data option [:rfc:`6275`]:

        .. code-block:: text

            0                   1                   2                   3
            0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
                                           +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
                                           |   Type = 5    | Option Length |
           +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
           |                                                               |
           +                                                               +
           |                         Authenticator                         |
           +                                                               +
           |                                                               |
           +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

        Args:
            schema: Parsed option schema.
            options: Parsed MH options.

        Returns:
            Constructed option data.

        """
        if schema.length % 8 != 0:
            raise ProtocolError(f'{self.alias}: [Opt {schema.type}] invalid format')

        data = Data_BindingAuthorizationDataOption(
            type=schema.type,
            length=schema.length + 2,
            data=schema.data,
        )
        return data

    def _read_opt_mnp(self, schema: 'Schema_MobileNetworkPrefixOption', *,
                      options: 'Option') -> 'Data_MobileNetworkPrefixOption':
        """Read MH mobile network prefix option.

        Structure of MH Mobile Network Prefix option [:rfc:`3963`]:

        .. code-block:: text

            0                   1                   2                   3
            0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
           +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
           |      Type     |   Length      |   Reserved    | Prefix Length |
           +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
           |                                                               |
           +                                                               +
           |                                                               |
           +                   Mobile Network Prefix                       +
           |                                                               |
           +                                                               +
           |                                                               |
           +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

        Args:
            schema: Parsed option schema.
            options: Parsed MH options.

        Returns:
            Constructed option data.

        """
        if schema.length != 18:
            raise ProtocolError(f'{self.alias}: [Opt {schema.type}] invalid format')

        prefix = cast('IPv6Network',
                      ipaddress.ip_network((schema.prefix, schema.prefix_length)))

        data = Data_MobileNetworkPrefixOption(
            type=schema.type,
            length=schema.length + 2,
            prefix=prefix,
        )
        return data

    def _read_opt_lla(self, schema: 'Schema_LinkLayerAddressOption', *,
                      options: 'Option') -> 'Data_LinkLayerAddressOption':
        """Read MH link-layer address (MH-LLA) option.

        Structure of MH Link-Layer Address option [:rfc:`5568`]:

        .. code-block:: text

            0                   1                   2                   3
            0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
                                         +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
                                         |     Type      |     Length    |
           +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
           | Option-Code   |                  LLA                     ....
           +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

        Args:
            schema: Parsed option schema.
            options: Parsed MH options.

        Returns:
            Constructed option data.

        """
        if schema.code != Enum_LLACode.MH:
            raise ProtocolError(f'{self.alias}: [Opt {schema.type}] invalid format')

        data = Data_LinkLayerAddressOption(
            type=schema.type,
            length=schema.length + 2,
            code=schema.code,
            lla=schema.lla,
        )
        return data

    def _read_opt_mn_id(self, schema: 'Schema_MNIDOption', *,
                       options: 'Option') -> 'Data_MNIDOption':
        """Read MH mobile node identifier option.

        Structure of MH Mobile Node Identifier option [:rfc:`4283`]:

        .. code-block:: text

           0                   1                   2                   3
           0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
                                           +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
                                           |  Option Type  | Option Length |
           +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
           |  Subtype      |          Identifier ...
           +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

        Args:
            schema: Parsed option schema.
            options: Parsed MH options.

        Returns:
            Constructed option data.

        """
        data = Data_MNIDOption(
            type=schema.type,
            length=schema.length + 2,
            subtype=schema.subtype,
            identifier=schema.identifier,
        )
        return data

    def _read_opt_auth(self, schema: 'Schema_AuthOption', *,
                       options: 'Option') -> 'Data_AuthOption':
        """Read MH mobility message authentication option.

        Structure of MH Mobility Message Authentication option [:rfc:`4285`]:

        .. code-block:: text

           0                   1                   2                   3
           0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
                           +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
                           |  Option Type  | Option Length |  Subtype      |
           +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
           |                  Mobility SPI                                 |
           +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
           |                  Authentication Data ....
           +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

        Args:
            schema: Parsed option schema.
            options: Parsed MH options.

        Returns:
            Constructed option data.

        """
        if (schema.length + 1) % 4 != 0:
            raise ProtocolError(f'{self.alias}: [Opt {schema.type}] invalid format')

        data = Data_AuthOption(
            type=schema.type,
            length=schema.length + 2,
            subtype=schema.subtype,
            spi=schema.spi,
            data=schema.data,
        )
        return data

    def _read_opt_mesg_id(self, schema: 'Schema_MesgIDOption', *,
                          options: 'Option') -> 'Data_MesgIDOption':
        """Read MH mobility message replay protection option.

        Structure of MH Mobility Message Replay Protection option [:rfc:`4285`]:

        .. code-block:: text

           0                   1                   2                   3
           0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
                                       +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
                                       |      Option Type  | Option Length |
           +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
           |                  Timestamp ...                                |
           +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
           |                  Timestamp                                    |
           +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

        Args:
            schema: Parsed option schema.
            options: Parsed MH options.

        Returns:
            Constructed option data.

        """
        if (schema.length) % 8 != 0:
            raise ProtocolError(f'{self.alias}: [Opt {schema.type}] invalid format')

        data = Data_MesgIDOption(
            type=schema.type,
            length=schema.length + 2,
            timestamp=schema.timestamp,
            ntp_timestamp=NTPTimestamp(schema.seconds, schema.fraction),
        )
        return data

    def _read_opt_cga_pr(self, schema: 'Schema_CGAParametersRequestOption', *,
                         options: 'Option') -> 'Data_CGAParametersRequestOption':
        """Read MH CGA parameters request option.

        Structure of MH CGA Parameters Request option [:rfc:`4866`]:

        .. code-block:: text

            0                   1                   2                   3
            0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
                                           +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
                                           |  Option Type  | Option Length |
                                           +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

        Args:
            schema: Parsed option schema.
            options: Parsed MH options.

        Returns:
            Constructed option data.

        """
        if schema.length != 0:
            raise ProtocolError(f'{self.alias}: [Opt {schema.type}] invalid format')

        data = Data_CGAParametersRequestOption(
            type=schema.type,
            length=schema.length + 2,
        )
        return data

    def _read_opt_cga_param(self, schema: 'Schema_CGAParametersOption', *,
                            options: 'Option') -> 'Data_CGAParametersOption':
        """Read MH CGA parameters option.

        Structure of MH CGA Parameters option [:rfc:`4866`]:

        .. code-block:: text

            0                   1                   2                   3
            0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
                                           +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
                                           |  Option Type  | Option Length |
           +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
           |                                                               |
           :                                                               :
           :                          CGA Parameters                       :
           :                                                               :
           |                                                               |
           +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

        Args:
            schema: Parsed option schema.
            options: Parsed MH options.

        Returns:
            Constructed option data.

        """
        for param in schema.parameters:
            if param.collision_count not in (0, 1, 2):
                raise ProtocolError(f'{self.alias}: [Opt {schema.type}] invalid format')

        data = Data_CGAParametersOption(
            type=schema.type,
            length=schema.length + 2,
            parameters=tuple(Data_CGAParameter(
                modifier=param.modifier,
                prefix=param.prefix,
                collision_count=param.collision_count,
                public_key=param.public_key,
                extensions=self._read_cga_extensions(param.extensions),
            ) for param in schema.parameters),
        )
        return data




    def _read_cga_extensions(self, extensions_schema: 'list[Schema_CGAExtension]') -> 'Extension':
        """Read CGA extensions.

        Structure of CGA extensions [:rfc:`4581`]:

        .. code-block:: text

            0                   1                   2                   3
            0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
           +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
           |         Extension Type        |   Extension Data Length       |
           +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
           |                                                               |
           ~                       Extension Data                          ~
           |                                                               |
           +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

        Args:
            extensions_schema: Parsed CGA extensions.

        Returns:
            Parsed CGA extensions data.

        """
        extensions = OrderedMultiDict()  # type: Extension

        for schema in extensions_schema:
            type = schema.type
            name = self.__extension__[type]

            if isinstance(name, str):
                meth_name = f'_read_ext_{name}'
                meth = cast('ExtensionParser',
                            getattr(self, meth_name, self._read_ext_none))
            else:
                meth = name[0]
            data = meth(schema, extensions=extensions)

            # record extension data
            extensions.add(type, data)

        return extensions

    def _read_ext_none(self, schema: 'Schema_UnknownExtension', *,
                       extensions: 'Extension') -> 'Data_UnknownExtension':
        """Read unknown CGA extension.

        Args:
            schema: Parsed extension schema.
            extensions: Parsed MH CGA extensions.

        Returns:
            Constructed extension data.

        """
        data = Data_UnknownExtension(
            type=schema.type,
            length=schema.length + 2,
            data=schema.data,
        )
        return data

    def _read_ext_multiprefix(self, schema: 'Schema_MultiPrefixExtension', *,
                                extensions: 'Extension') -> 'Data_MultiPrefixExtension':
        """Read multi-prefix CGA extension.

        Structure of Multi-Prefix CGA extension [:rfc:`5535`]::

        .. code-block:: text

            0                   1                   2                   3
            0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
           +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
           |         Extension Type        |   Extension Data Length       |
           +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
           |P|                         Reserved                            |
           +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
           |                                                               |
           +                           Prefix[1]                           +
           |                                                               |
           +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
           |                                                               |
           +                           Prefix[2]                           +
           |                                                               |
           +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
           .                               .                               .
           .                               .                               .
           .                               .                               .
           +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
           |                                                               |
           +                           Prefix[n]                           +
           |                                                               |
           +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

        Args:
            schema: Parsed extension schema.
            extensions: Parsed MH CGA extensions.

        Returns:
            Constructed extension data.

        """
        data = Data_MultiPrefixExtension(
            type=schema.type,
            length=schema.length + 2,
            flag=bool(schema.flags['P']),
            prefixes=tuple(schema.prefixes),
        )
        return data



    def _make_mh_options(self, options: 'Option | list[Schema_Option | tuple[Enum_Option, dict[str, Any]] | bytes]') -> 'tuple[list[Schema_Option | bytes], int]':
        """Make options for MH.

        Args:
            options: MH options.

        Returns:
            Tuple of options and total length of options.

        """
        total_length = 0
        if isinstance(options, list):
            options_list = []  # type: list[Schema_Option | bytes]
            for schema in options:
                if isinstance(schema, bytes):
                    code = Enum_Option.get(int.from_bytes(schema[0:1], 'big', signed=False))

                    data = schema  # type: Schema_Option | bytes
                    data_len = len(data)
                elif isinstance(schema, Schema):
                    data = schema
                    data_len = len(schema.pack())
                else:
                    code, args = cast('tuple[Enum_Option, dict[str, Any]]', schema)
                    name = self.__option__[code]
                    if isinstance(name, str):
                        meth_name = f'_make_opt_{name}'
                        meth = cast('OptionConstructor',
                                    getattr(self, meth_name, self._make_opt_none))
                    else:
                        meth = name[1]

                    data = meth(code, **args)
                    data_len = len(data.pack())

                options_list.append(data)
                total_length += data_len
            return options_list, total_length

        options_list = []
        for code, option in options.items(multi=True):
            name = self.__option__[code]
            if isinstance(name, str):
                meth_name = f'_make_opt_{name}'
                meth = cast('OptionConstructor',
                            getattr(self, meth_name, self._make_opt_none))
            else:
                meth = name[1]

            data = meth(code, option)
            data_len = len(data.pack())

            options_list.append(data)
            total_length += data_len
        return options_list, total_length

    def _make_opt_none(self, type: 'Enum_Option', option: 'Optional[Data_UnassignedOption]' = None, *,
                             data: 'bytes' = b'',
                             **kwargs: 'Any') -> 'Schema_UnassignedOption':
        """Make MH unassigned option.

        Args:
            type: Option type.
            option: Option data model.
            data: Option data.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            Constructed option schema.

        """
        if option is not None:
            data = option.data

        return Schema_UnassignedOption(
            type=type,
            length=len(data),
            data=data,
        )

    def _make_opt_pad(self, type: 'Enum_Option', option: 'Optional[Data_PadOption]' = None, *,
                      length: 'int' = 0,
                      **kwargs: 'Any') -> 'Schema_PadOption':
        """Make MH pad option.

        Args:
            type: Option type.
            option: Option data model.
            length: Padding length.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            Constructed option schema.

        """
        if  option is not None:
            length = option.length

        if type == Enum_Option.Pad1 and length != 0:
            # raise ProtocolError(f'{self.alias}: [OptNo {type}] invalid format')
            warn(f'{self.alias}: [OptNo {type}] invalid format', ProtocolWarning)
            type = Enum_Option.PadN  # type: ignore[assignment]
        if type == Enum_Option.PadN and length == 0:
            # raise ProtocolError(f'{self.alias}: [OptNo {type}] invalid format')
            warn(f'{self.alias}: [OptNo {type}] invalid format', ProtocolWarning)
            type = Enum_Option.Pad1  # type: ignore[assignment]

        return Schema_PadOption(
            type=type,
            length=length,
        )

    def _make_opt_bra(self, type: 'Enum_Option', option: 'Optional[Data_BindRefreshAdviceOption]' = None, *,
                      interval: 'int' = 0,
                      **kwargs: 'Any') -> 'Schema_BindRefreshAdviceOption':
        """Make MH binding refresh advice option.

        Args:
            type: Option type.
            option: Option data model.
            interval: Refresh interval.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            Constructed option schema.

        """
        if option is not None:
            interval = option.interval

        return Schema_BindRefreshAdviceOption(
            type=type,
            length=2,
            interval=interval,
        )

    def _make_opt_aca(self, type: 'Enum_Option', option: 'Optional[Data_AlternateCareofAddressOption]' = None, *,
                      address: 'bytes | str | int | IPv6Address' = '::',
                      **kwargs: 'Any') -> 'Schema_AlternateCareofAddressOption':
        """Make MH alternate care-of address option.

        Args:
            type: Option type.
            option: Option data model.
            address: Alternate care-of address.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            Constructed option schema.

        """
        if option is not None:
            address = option.address

        return Schema_AlternateCareofAddressOption(
            type=type,
            length=16,
            address=address,
        )

    def _make_opt_ni(self, type: 'Enum_Option', option: 'Optional[Data_NonceIndicesOption]' = None, *,
                     home: 'int' = 0,
                     careof: 'int' = 0,
                     **kwargs: 'Any') -> 'Schema_NonceIndicesOption':
        """Make MH nonce indices option.

        Args:
            type: Option type.
            option: Option data model.
            home: Home nonce index.
            careof: Care-of nonce index.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            Constructed option schema.

        """
        if option is not None:
            home = option.home
            careof = option.careof

        return Schema_NonceIndicesOption(
            type=type,
            length=4,
            home=home,
            careof=careof,
        )

    def _make_opt_bad(self, type: 'Enum_Option', option: 'Optional[Data_BindingAuthorizationDataOption]' = None, *,
                      data: 'bytes' = b'',
                      **kwargs: 'Any') -> 'Schema_BindingAuthorizationDataOption':
        """Make MH binding authorization data option.

        Args:
            type: Option type.
            option: Option data model.
            data: Authenticator.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            Constructed option schema.

        """
        if option is not None:
            data = option.data

        if len(data) % 8 != 0:
            raise ProtocolError(f'{self.alias}: [OptNo {type}] invalid format')

        return Schema_BindingAuthorizationDataOption(
            type=type,
            length=len(data),
            data=data,
        )

    def _make_opt_mnp(self, type: 'Enum_Option', option: 'Optional[Data_MobileNetworkPrefixOption]' = None, *,
                      prefix: 'bytes | str | IPv6Network' = '::/0',
                      **kwargs: 'Any') -> 'Schema_MobileNetworkPrefixOption':
        """Make MH mobile network prefix option.

        Args:
            type: Option type.
            option: Option data model.
            prefix: Mobile network prefix.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            Constructed option schema.

        """
        if option is not None:
            prefix = option.prefix

        prefix_val = ipaddress.ip_network(prefix)
        if prefix_val.version != 6:
            raise ProtocolError(f'{self.alias}: [OptNo {type}] invalid movile network prefix: {prefix!r}')
        prefix_length = prefix_val.prefixlen
        prefix_addr = prefix_val.network_address

        return Schema_MobileNetworkPrefixOption(
            type=type,
            length=18,
            prefix_length=prefix_length,
            prefix=prefix_addr,
        )

    def _make_opt_lla(self, type: 'Enum_Option', option: 'Optional[Data_LinkLayerAddressOption]' = None, *,
                      address: 'bytes' = b'',
                      **kwargs: 'Any') -> 'Schema_LinkLayerAddressOption':
        """Make MH link-layer address option.

        Args:
            type: Option type.
            option: Option data model.
            address: Link-layer address.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            Constructed option schema.

        """
        if option is not None:
            address = option.lla

        return Schema_LinkLayerAddressOption(
            type=type,
            length=len(address) + 1,
            code=Enum_LLACode.MH,  # type: ignore[arg-type]
            lla=address,
        )

    def _make_opt_mn_id(self, type: 'Enum_Option', option: 'Optional[Data_MNIDOption]' = None, *,
                       subtype: 'Enum_MNIDSubtype | StdlibEnum | AenumEnum | str | int' = Enum_MNIDSubtype.IPv6_Address,
                       subtype_default: 'Optional[int]' = None,
                       subtype_namespace: 'Optional[dict[str, int] | dict[int, str] | Type[StdlibEnum] | Type[AenumEnum]]' = None,  # pylint: disable=line-too-long
                       subtype_reversed: 'bool' = False,
                       identifier: 'bytes | str | IPv6Address | int' = '::',
                       **kwargs: 'Any') -> 'Schema_MNIDOption':
        """Make MH mobile node identifier option.

        Args:
            type: Option type.
            option: Option data model.
            subtype: MN-ID subtype.
            subtype_default: MN-ID subtype default value.
            subtype_namespace: MN-ID subtype namespace.
            subtype_reversed: MN-ID subtype reversed flag.
            identifier: Identifier.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            Constructed option schema.

        """
        if option is not None:
            subtype_val = option.subtype
            identifier = option.identifier
        else:
            subtype_val = self._make_index(subtype, subtype_default, namespace=subtype_namespace,  # type: ignore[call-overload]
                                           reversed=subtype_reversed, pack=False)

        if isinstance(identifier, ipaddress.IPv6Address):
            id_len = 16
        elif isinstance(identifier, int):
            id_len = math.ceil(identifier.bit_length() / 8)
        else:
            id_len = len(identifier)

        return Schema_MNIDOption(
            type=type,
            length=1 + id_len,
            subtype=subtype_val,
            identifier=identifier,
        )

    def _make_opt_auth(self, type: 'Enum_Option', option: 'Optional[Data_AuthOption]' = None, *,
                       subtype: 'Enum_AuthSubtype | StdlibEnum | AenumEnum | str | int' = Enum_AuthSubtype.MN_HA,
                       subtype_default: 'Optional[int]' = None,
                       subtype_namespace: 'Optional[dict[str, int] | dict[int, str] | Type[StdlibEnum] | Type[AenumEnum]]' = None,  # pylint: disable=line-too-long
                       subtype_reversed: 'bool' = False,
                       spi: 'int' = 0,
                       data: 'bytes' = b'',
                       **kwargs: 'Any') -> 'Schema_AuthOption':
        """Make MH authentication option.

        Args:
            type: Option type.
            option: Option data model.
            subtype: Authentication subtype.
            subtype_default: Authentication subtype default value.
            subtype_namespace: Authentication subtype namespace.
            subtype_reversed: Authentication subtype reversed flag.
            spi: Security parameter index.
            data: Authentication data.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            Constructed option schema.

        """
        if option is not None:
            subtype_val = option.subtype
            spi = option.spi
            data = option.data
        else:
            subtype_val = self._make_index(subtype, subtype_default, namespace=subtype_namespace,  # type: ignore[call-overload]
                                           reversed=subtype_reversed, pack=False)

        if (len(data) + 6) % 4 != 0:
            raise ProtocolError(f'{self.alias}: [OptNo {type}] invalid format')

        return Schema_AuthOption(
            type=type,
            length=5 + len(data),
            subtype=subtype_val,
            spi=spi,
            data=data,
        )

    def _make_opt_mesg_id(self, type: 'Enum_Option', option: 'Optional[Data_MesgIDOption]' = None, *,
                          timestamp: 'Optional[NTPTimestamp]' = None,
                          interval: 'Optional[dt_type]' = None,
                          **kwargs: 'Any') -> 'Schema_MesgIDOption':
        """Make MH mobility message replay protection option.

        Args:
            type: Option type.
            option: Option data model.
            timestamp: NTP timestamp, c.f., :rfc:`1305`.
            interval: Timestamp interval (since UNIX-epoch).
            **kwargs: Arbitrary keyword arguments.

        Returns:
            Constructed option schema.

        """
        if option is not None:
            timestamp = option.ntp_timestamp

        if timestamp is None:
            interval = interval or datetime.datetime.now(datetime.timezone.utc)

            int_ts = interval.timestamp()
            ts_sec = math.floor(int_ts)
            ts_frc = math.ceil(((int_ts - ts_sec) * 1_000_000)) * 2**32

            timestamp = NTPTimestamp(seconds=ts_sec + 2_208_988_800,  # 70 years
                                     fraction=ts_frc)

        return Schema_MesgIDOption(
            type=type,
            length=8,
            seconds=timestamp.seconds,
            fraction=timestamp.fraction,
        )

    def _make_opt_cga_pr(self, type: 'Enum_Option', option: 'Optional[Data_CGAParametersRequestOption]' = None,
                         **kwargs: 'Any') -> 'Schema_CGAParametersRequestOption':
        """Make MH CGA parameters request option.

        Args:
            type: Option type.
            option: Option data model.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            Constructed option schema.

        """
        return Schema_CGAParametersRequestOption(
            type=type,
            length=0,
        )

    def _make_opt_cga_param(self, type: 'Enum_Option', option: 'Optional[Data_CGAParametersOption]' = None, *,
                            parameters: 'Optional[list[Schema_CGAParameter | Data_CGAParameter | dict[str, Any] | bytes]]' = None,
                            **kwargs: 'Any') -> 'Schema_CGAParametersOption':
        """Make MH CGA paramters option.

        Args:
            type: Option type.
            option: Option data model.
            parameters: CGA parameters.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            Constructed option schema.

        """
        if option is not None:
            parameters = cast('list[Data_CGAParameter]', option.parameters)  # type: ignore[assignment]

        if parameters is None:
            parameters = []

        param = []  # type: list[Schema_CGAParameter | bytes]
        length = 0
        for data in parameters:
            if isinstance(data, bytes):
                length += len(data)
                param.append(data)
            elif isinstance(data, Schema_CGAParameter):
                length += len(data)
                param.append(data)
            elif isinstance(data, Data_CGAParameter):
                ext, _ = self._make_cga_extensions(data.extensions)
                schema = Schema_CGAParameter(
                    modifier=data.modifier,
                    prefix=data.prefix,
                    collision_count=data.collision_count,
                    public_key=data.public_key,
                    extensions=ext,
                )

                length += len(schema)
                param.append(schema)
            else:
                raise ProtocolError(f'{self.alias}: [OptNo {type}] unknown CGA parameter format: {data}')

        return Schema_CGAParametersOption(
            type=type,
            length=length,
            parameters=param,
        )




    def _make_cga_extensions(self, extensions: 'Extension | list[Schema_CGAExtension | tuple[Enum_CGAExtension, dict[str, Any]] | bytes]') -> 'tuple[list[Schema_CGAExtension | bytes], int]':
        """Make CGA extensions for MH.

        Args:
            extensions: CGA extensions.

        Returns:
            Tuple of extensions and total length of extensions.

        """
        total_length = 0
        if isinstance(extensions, list):
            extensions_list = []  # type: list[Schema_CGAExtension | bytes]
            for schema in extensions:
                if isinstance(schema, bytes):
                    code = Enum_CGAExtension.get(int.from_bytes(schema[0:2], 'big', signed=False))

                    data = schema  # type: Schema_CGAExtension | bytes
                    data_len = len(data)
                elif isinstance(schema, Schema):
                    data = schema
                    data_len = len(schema.pack())
                else:
                    code, args = cast('tuple[Enum_CGAExtension, dict[str, Any]]', schema)
                    name = self.__extension__[code]
                    if isinstance(name, str):
                        meth_name = f'_make_ext_{name}'
                        meth = cast('ExtensionConstructor',
                                    getattr(self, meth_name, self._make_ext_none))
                    else:
                        meth = name[1]

                    data = meth(code, **args)
                    data_len = len(data.pack())

                extensions_list.append(data)
                total_length += data_len
            return extensions_list, total_length

        extensions_list = []
        for code, extension in extensions.items(multi=True):
            name = self.__extension__[code]
            if isinstance(name, str):
                meth_name = f'_make_ext_{name}'
                meth = cast('ExtensionConstructor',
                            getattr(self, meth_name, self._make_ext_none))
            else:
                meth = name[1]

            data = meth(code, extension)
            data_len = len(data.pack())

            extensions_list.append(data)
            total_length += data_len
        return extensions_list, total_length

    def _make_ext_none(self, type: 'Enum_CGAExtension', option: 'Optional[Data_UnknownExtension]' = None, *,
                       data: 'bytes' = b'',
                       **kwargs: 'Any') -> 'Schema_UnknownExtension':
        """Make CGA extension.

        Args:
            type: Extension type.
            option: Extension data model.
            data: Extension data.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            Constructed extension schema.

        """
        if option is not None:
            data = option.data

        return Schema_UnknownExtension(
            type=type,
            length=len(data),
            data=data,
        )

    def _make_ext_multiprefix(self, type: 'Enum_CGAExtension', option: 'Optional[Data_MultiPrefixExtension]' = None, *,
                              flag: 'bool' = False,
                              prefixes: 'Optional[list[int]]' = None,
                              **kwargs: 'Any') -> 'Schema_MultiPrefixExtension':
        """Make CGA multi-prefix extension.

        Args:
            type: Extension type.
            option: Extension data model.
            flag: Public key flag.
            prefixes: Prefixes.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            Constructed extension schema.

        """
        if option is not None:
            flag = option.flag
            prefixes = cast('list[int]', option.prefixes)
        else:
            prefixes = prefixes or []

        return Schema_MultiPrefixExtension(
            type=type,
            length=1 + len(prefixes) * 16,
            flags={
                'P': int(flag),
            },
            prefixes=prefixes,
        )
