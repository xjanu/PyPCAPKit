# -*- coding: utf-8 -*-

import statistics
import time

import pcapkit
from pcapkit.utilities.logging import logger

logger.setLevel('INFO')

for engine in ['default', 'dpkt', 'scapy', 'pyshark']:
    lid = []
    for index in range(1):
        now = time.time()

        extraction = pcapkit.extract(fin='../sample/in.pcap', store=False, nofile=True, verbose=False, engine=engine)  # type: ignore[arg-type]

        delta = time.time() - now
        # print(f'[{engine}] No. {index:>3d}: {extraction.length} packets extracted in {delta} seconds.')
        lid.append(float(delta))

    avetime = statistics.mean(lid)
    average = avetime / extraction.length
    print(f'Report: [{engine}] {average} seconds per packet ({avetime} seconds per {extraction.length} packets).')
