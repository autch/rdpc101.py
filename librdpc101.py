# -*- mode: python; encoding: utf-8; -*-

import hid

RDPC101_VENDORID = 0x10c4
RDPC101_PRODUCTID	= 0x818a

RDPC_STATE_INDEX_MA = 1
RDPC_STATE_INDEX_SIGINTENSITY = 2
RDPC_STATE_INDEX_FREQ_HI = 3
RDPC_STATE_INDEX_FREQ_LO = 4

RDPC_SETFREQ = 0x02
RDPC_MUTE = 0x05
RDPC_MA = 0x06
RDPC_SEEK = 0x09
RDPC_BAND = 0x0a
RDPC_UNKNOWN2 = 0x13

RDPC_MA_MONO = 0x00
RDPC_MA_STEREO = 0x01

RDPC_MA_SEEKING_MASK = (1 << 4)

RDPC_BAND_FM = 0x02
RDPC_BAND_AM = 0x80

RDPC_SEEK_UP = 0x01
RDPC_SEEK_DOWN = 0x02

RFD_AM = 0
RFD_FM = 1
RFD_TV = 2

def enumerate():
  return hid.enumerate(RDPC101_VENDORID, RDPC101_PRODUCTID)

class BandMap:
  def __init__(self):
    self.band_map = [
      { 'band': RDPC_BAND_AM,  'min': 522, 'max': 1629, 'step': 9 },
      { 'band': RDPC_BAND_FM,  'min': 7600, 'max': 9000, 'step': 10 },
      { 'band': RDPC_BAND_FM,  'min': 9005, 'max': 10800, 'step': 5 }
    ]

  def get_band(self, freq):
    for b in self.band_map:
      if b['min'] <= freq and freq <= b['max']:
        return b
    return None
  
  def get_band_by_index(self, idx):
    return self.band_map[idx]

  def get_band_name(self, freq):
    band = self.get_band(freq)
    if band['band'] == RDPC_BAND_FM:
      return 'FM'
    elif band['band'] == RDPC_BAND_AM:
      return 'AM'
    return '??'

  def get_freq_format(self, freq):
    band = self.get_band(freq)
    if band['band'] == RDPC_BAND_FM:
      return '%3d.%2.2d MHz' % (freq / 100, freq % 100)
    elif band['band'] == RDPC_BAND_AM:
      return '%6d kHz' % (freq)
    return '---- Hz'

class RDPC101:
  def __init__(self, path = None):
    self.hid_dev = hid.device()
    if path:
      self.hid_dev.open_path(path)
    else:
      self.hid_dev.open(RDPC101_VENDORID, RDPC101_PRODUCTID)
    self.report_pkt = None

  def close(self):
    self.hid_dev.close()

  def update_status(self):
    self.report_pkt = self.hid_dev.read(1024)

  def get_freq(self):
    if not self.report_pkt:
      self.update_status()
    return ((self.report_pkt[RDPC_STATE_INDEX_FREQ_HI] << 8) |
      self.report_pkt[RDPC_STATE_INDEX_FREQ_LO])

  def get_channels(self):
    if not self.report_pkt:
      self.update_status()
    return self.report_pkt[RDPC_STATE_INDEX_MA]

  def get_intensity(self):
    if not self.report_pkt:
      self.update_status()
    return self.report_pkt[RDPC_STATE_INDEX_SIGINTENSITY]

  def get_seeking(self):
    self.update_status()
    return (self.report_pkt[RDPC_STATE_INDEX_MA] & RDPC_MA_SEEKING_MASK) != 0

  def _send_feature(self, packet):
    return self.hid_dev.send_feature_report(packet)

  # mono = 0x00, stereo = 0x01
  def set_ma(self, ma):
    return self._send_feature([RDPC_MA, ma, 0x00])

  # mute off = 0, mute on = 1
  def set_mute(self, mute):
    return self._send_feature([RDPC_MUTE, mute, 0x00])

  # fm = 0x02, am = 0x80
  def set_band(self, band):
    return self._send_feature([RDPC_BAND, band, 0x02])

  # in kilohertz
  def set_freq(self, freq):
    return self._send_feature([RDPC_SETFREQ, (freq >> 8) & 0xff, freq & 0xff])

  # up = 0x01, down = 0x02
  def set_seek(self, direction):
    return self._send_feature([RDPC_SEEK, direction, 0x00])

  def get_channel_format(self):
    ch = self.get_channels()
    if ch == RDPC_MA_MONO:
      return 'Mono'
    elif ch == RDPC_MA_STEREO:
      return 'Stereo'
    return '----'
