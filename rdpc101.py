#!/usr/bin/env python
# -*- mode: python; encoding: utf-8; -*-

import sys
import time
import argparse
import librdpc101

ap = argparse.ArgumentParser()
ap.add_argument('-d', '--device', dest='device', type=int, help='use DEVICEth device, shown in order of -l')
ap.add_argument('-D', '--down', action='store_const', const=librdpc101.RDPC_SEEK_DOWN, dest='seek',
                help='seek downward')
ap.add_argument('-U', '--up', action='store_const', const=librdpc101.RDPC_SEEK_UP, dest='seek', help='seek upward')
ap.add_argument('-m', '--mono', action='store_const', const=False, dest='stereo')
ap.add_argument('-s', '--stereo', action='store_const', const=True, dest='stereo')
ap.add_argument('-l', '--list', action='store_true', help='list devices and its status then exit')
ap.add_argument('-S', '--scan', dest='scan', help='scan stations in specified band')
ap.add_argument('-x', '--expert', dest='expert', action='store_true', help='tune that freq exactly')
ap.add_argument('freq', nargs='?', default=None, help='frequency in kilohertz or megahertz')

args = ap.parse_args()
freq = None

if args.list:
    bm = librdpc101.BandMap()
    devices = sorted(librdpc101.enumerate(), key=lambda x: x['path'])
    i = 0
    for dev in devices:
        with librdpc101.open(dev['path']) as d:
            d.update_status()
            f = d.get_freq()
            print("device %d: %s %s %s %ddB" % (i, bm.get_band_name(f), bm.get_freq_format(f),
                                                d.get_channel_format(), d.get_intensity()))
        i += 1
    sys.exit(0)

if args.freq:
    try:
        f_freq = float(args.freq)
    except ValueError as e:
        print("freq must be numerals")
        ap.print_help()
        sys.exit(1)

    bm = librdpc101.BandMap()
    freq, band, stereo = bm.get_tuning_freq(f_freq, exact=args.expert)
    if not freq:
        print('Frequency out of range')
        ap.print_help()
        sys.exit(1)

path = None
if args.device:
    devices = sorted(librdpc101.enumerate(), key=lambda x: x['path'])
    if args.device >= len(devices):
        print('Device index out of range')
        sys.exit(1)
    nth = devices[args.device]
    if not nth:
        print('Device index out of range')
        sys.exit(1)
    path = nth['path']

with librdpc101.open(path) as dev:
    def show_status(d):
        bm = librdpc101.BandMap()
        f = d.get_freq(True)
        print("%s %s %s %ddB" % (bm.get_band_name(f), bm.get_freq_format(f),
                                d.get_channel_format(), d.get_intensity()))

    if freq:
        bm = librdpc101.BandMap()
        cur_freq = dev.get_freq()
        cur_band = bm.get_band(cur_freq)
        band = bm.get_band(freq)

        if not cur_band or cur_band['band'] != band['band']:
            dev.set_band(band['band'])
        if cur_freq != freq:
            dev.set_freq(freq)
        dev.wait_seeking()
        dev.update_status()
        show_status(dev)
    elif args.seek:
        dev.set_mute(1)
        try:
            dev.set_seek(args.seek)
            dev.wait_seeking()
        finally:
            dev.set_mute(0)
        dev.update_status()
        show_status(dev)
    elif args.scan:
        bandname = args.scan.lower()
        bm = librdpc101.BandMap()

        o_freq = dev.get_freq()
        o_band = bm.get_band(o_freq)

        if bandname[0] == 'a':
            band = bm.get_band_by_index(librdpc101.RFD_AM)
        elif bandname[0] == 'f':
            band = bm.get_band_by_index(librdpc101.RFD_FM)
        else:
            print('unsupported band')
            ap.print_help()
            sys.exit(1)

        dev.set_mute(1)
        try:
            dev.set_band(band['band'])
            dev.set_freq(band['min'])
            dev.wait_seeking()

            p_freq = band['min']
            c_freq = dev.get_freq(True)
            while c_freq < band['max']:
                dev.set_seek(librdpc101.RDPC_SEEK_UP)
                dev.wait_seeking()
                c_freq = dev.get_freq(True)
                if p_freq != c_freq:
                    show_status(dev)
                    p_freq = c_freq
        finally:
            if not o_band or band['band'] != o_band['band']:
                dev.set_band(o_band['band'])
            dev.set_freq(o_freq)
            dev.set_mute(0)

    if args.stereo is not None:
        dev.set_ma(librdpc101.RDPC_MA_STEREO if args.stereo else librdpc101.RDPC_MA_MONO)
