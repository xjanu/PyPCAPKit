# -*- coding: utf-8 -*-
# pylint: disable=import-outside-toplevel
"""Trace TCP Flows
=====================

:mod:`pcapkit.foundation.traceflow` is the interface to trace
TCP flows from a series of packets and connections.

.. note::

   This was implemented as the demand of my mate
   `@gousaiyang <https://github.com/gousaiyang>`__.

"""
from typing import TYPE_CHECKING, TypeVar, overload, Generic

from pcapkit.foundation.traceflow.data.tcp import Buffer, BufferID, Index, Packet, IPAddress
from pcapkit.foundation.traceflow.traceflow import TraceFlow
from pcapkit.protocols.transport.tcp import TCP as TCP_Protocol

__all__ = ['TCP']

if TYPE_CHECKING:
    from ipaddress import IPv4Address, IPv6Address
    from typing import Type

    from dictdumper.dumper import Dumper
    from typing_extensions import Literal


class TCP(TraceFlow[BufferID, Buffer, Index, Packet[IPAddress]], Generic[IPAddress]):
    """Trace TCP flows."""

    ##########################################################################
    # Methods.
    ##########################################################################

    @property
    def name(self) -> 'Literal["Transmission Control Protocol"]':
        """Protocol of current packet."""
        return 'Transmission Control Protocol'

    @property
    def protocol(self) -> 'Type[TCP_Protocol]':
        """Protocol of current reassembly object."""
        return TCP_Protocol

    ##########################################################################
    # Methods.
    ##########################################################################

    def dump(self, packet: 'Packet[IPAddress]') -> 'None':
        """Dump frame to output files.

        Arguments:
            packet (Dict[str, Any]): a flow packet (:term:`trace.packet`)

        """
        # fetch flow label
        output = self.trace(packet, output=True)

        # dump files
        output(packet.frame, name=f'Frame {packet.index}')  # pylint: disable=not-callable

    @overload
    def trace(self, packet: 'Packet[IPAddress]', *, output: 'Literal[True]' = ...) -> 'Dumper': ...
    @overload
    def trace(self, packet: 'Packet[IPAddress]', *, output: 'Literal[False]' = ...) -> 'str': ...

    def trace(self, packet: 'Packet[IPAddress]', *, output: 'bool' = False) -> 'Dumper | str':
        """Trace packets.

        Arguments:
            packet: a flow packet (:term:`trace.packet`)
            output: flag if has formatted dumper

        Returns:
            If ``output`` is :data:`True`, returns the initiated
            :class:`~dictdumper.dumper.Dumper` object, which will dump data to
            the output file named after the flow label; otherwise, returns the
            flow label itself.

        Notes:
            The flow label is formatted as following:

            .. code-block:: python

               f'{packet.src}_{packet.srcport}-{packet.dst}_{info.dstport}-{packet.timestamp}'

        """
        # clear cache
        self.__cached__['submit'] = None

        # Buffer Identifier
        BUFID = (packet.src, packet.srcport, packet.dst, packet.dstport)  # type: BufferID
        # SYN = packet.syn  # Synchronise Flag (Establishment)
        FIN = packet.fin  # Finish Flag (Termination)

        # # when SYN is set, reset buffer of this seesion
        # if SYN and BUFID in self._buffer:
        #     temp = self._buffer.pop(BUFID)
        #     temp['fpout'] = (self._fproot, self._fdpext)
        #     temp['index'] = tuple(temp['index'])
        #     self._stream.append(Info(temp))

        # initialise buffer with BUFID
        if BUFID not in self._buffer:
            label = f'{packet.src}_{packet.srcport}-{packet.dst}_{packet.dstport}-{packet.timestamp}'
            self._buffer[BUFID] = Buffer(
                fpout=self._foutio(fname=f'{self._fproot}/{label}{self._fdpext or ""}', protocol=packet.protocol,
                                   byteorder=self._endian, nanosecond=self._nnsecd),
                index=[],
                label=label,
            )

        # trace frame record
        self._buffer[BUFID].index.append(packet.index)
        fpout = self._buffer[BUFID].fpout
        label = self._buffer[BUFID].label

        # when FIN is set, submit buffer of this session
        if FIN:
            buf = self._buffer.pop(BUFID)
            # fpout, label = buf['fpout'], buf['label']
            self._stream.append(Index(
                fpout=f'{self._fproot}/{label}{self._fdpext}' if self._fdpext is not None else None,
                index=tuple(buf.index),
                label=label,
            ))

        # return label or output object
        return fpout if output else label

    def submit(self) -> 'tuple[Index, ...]':
        """Submit traced TCP flows.

        Returns:
            Traced TCP flow (:term:`trace.index`).

        """
        if (cached := self.__cached__.get('submit')) is not None:
            return cached

        ret = []  # type: list[Index]
        for buf in self._buffer.values():
            ret.append(Index(fpout=f"{self._fproot}/{buf.label}{self._fdpext}" if self._fdpext else None,
                             index=tuple(buf.index),
                             label=buf.label,))
        ret.extend(self._stream)
        ret_submit = tuple(ret)

        self.__cached__['submit'] = ret_submit
        return ret_submit
