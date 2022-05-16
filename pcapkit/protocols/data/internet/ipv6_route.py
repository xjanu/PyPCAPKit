# -*- coding: utf-8 -*-
"""data model for IPv6 Routing Header"""

from typing import TYPE_CHECKING

from pcapkit.corekit.infoclass import Info

if TYPE_CHECKING:
    from ipaddress import IPv6Address

    from pcapkit.const.ipv6.routing import Routing
    from pcapkit.const.reg.transtype import TransType

__all__ = [
    'IPv6_Route',

    'UnknownType', 'SourceRoute', 'Type2', 'RPL',
]


class IPv6_Route(Info):
    """Data model for IPv6-Route protocol."""

    #: Next header.
    next: 'TransType'
    #: Header extension length.
    length: 'int'
    #: Routing type.
    type: 'Routing'
    #: Segments left.
    seg_left: 'int'

    if TYPE_CHECKING:
        #: Type-specific data.
        data: 'UnknownType'

        def __init__(self, next: 'TransType', length: 'int', type: 'Routing', seg_left: 'int'): ...  # pylint: disabl=unused-argument,multiple-statements,super-init-not-called,redefined-builtin,line-too-long


class UnknownType(Info):
    """Data model for IPv6-Route unknown type."""

    #: Data.
    data: 'bytes'

    if TYPE_CHECKING:
        def __init__(self, data: 'bytes') -> 'None': ...  # pylint: disabl=unused-argument,multiple-statements,super-init-not-called,redefined-builtin,line-too-long


class SourceRoute(Info):
    """Data model for IPv6-Route Source Route data type."""

    #: Source addresses.
    ip: 'tuple[IPv6Address, ...]'

    if TYPE_CHECKING:
        def __init__(self, ip: 'tuple[IPv6Address, ...]') -> 'None': ...  # pylint: disabl=unused-argument,multiple-statements,super-init-not-called,redefined-builtin,line-too-long


class Type2(Info):
    """Data model for IPv6-Route Type 2 data type."""

    #: Address.
    ip: 'IPv6Address'

    if TYPE_CHECKING:
        def __init__(self, ip: 'IPv6Address') -> 'None': ...  # pylint: disabl=unused-argument,multiple-statements,super-init-not-called,redefined-builtin,line-too-long


class RPL(Info):
    """Data model for RPL Source data type."""

    #: CmprI.
    cmpr_i: 'int'
    #: CmprE.
    cmpr_e: 'int'
    #: Pad.
    pad: 'int'
    #: IPv6 addresses.
    ip: 'tuple[IPv6Address, ...]'

    if TYPE_CHECKING:
        def __init__(self, cmpr_i: 'int', cmpr_e: 'int', pad: 'int', ip: 'tuple[IPv6Address, ...]') -> 'None': ...  # pylint: disabl=unused-argument,multiple-statements,super-init-not-called,redefined-builtin,line-too-long
