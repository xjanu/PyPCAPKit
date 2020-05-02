# -*- coding: utf-8 -*-
# pylint: disable=line-too-long
"""ECDSA Curve Label"""

from aenum import IntEnum, extend_enum

__all__ = ['ECDSACurve']


class ECDSACurve(IntEnum):
    """[ECDSACurve] ECDSA Curve Label"""

    _ignore_ = 'ECDSACurve _'
    ECDSACurve = vars()

    #: [:rfc:`7401`]
    ECDSACurve['RESERVED'] = 0

    #: [:rfc:`7401`]
    ECDSACurve['NIST_P_256'] = 1

    #: [:rfc:`7401`]
    ECDSACurve['NIST_P_384'] = 2

    @staticmethod
    def get(key, default=-1):
        """Backport support for original codes."""
        if isinstance(key, int):
            return ECDSACurve(key)
        if key not in ECDSACurve._member_map_:  # pylint: disable=no-member
            extend_enum(ECDSACurve, key, default)
        return ECDSACurve[key]

    @classmethod
    def _missing_(cls, value):
        """Lookup function used when value is not found."""
        if not (isinstance(value, int) and 0 <= value <= 65535):
            raise ValueError('%r is not a valid %s' % (value, cls.__name__))
        if 3 <= value <= 65535:
            extend_enum(cls, 'Unassigned [%d]' % value, value)
            return cls(value)
        return super()._missing_(value)
