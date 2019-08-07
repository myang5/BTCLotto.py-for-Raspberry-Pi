#To run you need to have cgminer running already, then run
#sudo python btclotto.py <local ip>

import socket
import urllib
import time
import math
import board


from neopixel import *


# LED strip configuration:
LED_COUNT      = 8      # Number of LED pixels.
LED_PIN        = board.D18      # GPIO pin connected to the pixels (18 uses PWM!).
LED_BRIGHTNESS = 0.2     #0 for darkest and 1 for brightest
AUTO_WRITE     = False

BLOCK = '000000000000000000e04b20fb1ddd3305d4e7112a9c4247e59d224a89f96d5a'
FOUND = 0
STATUS_MSG = ""

def loser(strip, wait_ms=20):
	for j in range(32):
                strip[0] = (255,255,0)
                strip[1] = (255,255,0)
                strip[2] = (0,0,0)
                strip[3] = (0,8*j,0)
                strip[4] = (0,8*j,0)
                strip[5] = (0,0,0)
                strip[6] = (0,0,0)
                strip[7] = (0,0,0)
                strip.show()
                time.sleep(0.05)
                strip[6] = (255,255,0)
                strip[7] = (255,255,0)
                strip[2] = (0,0,0)
                strip[3] = (0,8*j,0)
                strip[4] = (0,8*j,0)
                strip[5] = (0,0,0)
                strip[0] = (0,0,0)
                strip[1] = (0,0,0)
                strip.show()
                time.sleep(0.05)
	for q in range(8):
                strip.fill((255,0,0))
                strip.show()
                time.sleep(0.3)
                strip.fill((0,0,0))
                strip.show()
                time.sleep(0.3)

def winner(strip, wait_ms=20):
        for j in range(32):
                strip[0] = (255,255,0)
                strip[1] = (255,255,0)
                strip[2] = (0,0,0)
                strip[3] = (0,8*j,0)
                strip[4] = (0,8*j,0)
                strip[5] = (0,0,0)
                strip[6] = (0,0,0)
                strip[7] = (0,0,0)
                strip.show()
                time.sleep(0.05)
                strip[6] = (255,255,0)
                strip[7] = (255,255,0)
                strip[2] = (0,0,0)
                strip[3] = (0,8*j,0)
                strip[4] = (0,8*j,0)
                strip[5] = (0,0,0)
                strip[0] = (0,0,0)
                strip[1] = (0,0,0)
                strip.show()
                time.sleep(0.05)
        for q in range(30):
                strip.fill((0,255,0))
                strip.show()
                time.sleep(0.1)
                strip.fill((0,0,0))
                strip.show()
                time.sleep(0.1)

def dispBlock(strip ,block, wait_ms=20):
	for j in range(1,2):
		for q in range(7):
			r = int(block[j+0+(6*q)]+block[j+1+(6*q)],16)
			g = int(block[j+2+(6*q)]+block[j+3+(6*q)],16)
			b = int(block[j+4+(6*q)]+block[j+5+(6*q)],16)
			strip[q] = (r,g,b)
	strip.show()
	time.sleep(3)




CONV_4G = 4295.0 # 4096 or 4295
CONV_60_SHARE = CONV_4G / 60.0 # 4096 / 60 = 68.27 or 4295 / 60 = 71.58
def value_split(s):
  r = s.split('=')
  if len(r) == 2: return r
  return r[0], ''

def response_split(s):
  try:
    r = s.split(',')
    title = r[0]
    d = dict(map(value_split, r[1:]))
    return title, d
  except ValueError:
    print(s)

# https://github.com/ckolivas/cgminer/blob/master/API-README
def cg_rpc(host, port, command):
  try:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host, port))
    s.sendall(command.encode('utf-8'))
    time.sleep(0.02)
    data = s.recv(8192)
    s.close()
  except Exception as e:
    print(e)
    data = ''
  if data:
    d = data.decode('utf-8').strip('\x00|').split('|')
    return list(map(response_split, d))
  return None

def parse_time(t):
  r = []
  m = t // 60
  if t >= 86400:
    r.append('%d day' % (t // 86400))
    t = t % 86400
  r.append('%02d:%02d:%02d / %d min' % (t // 3600, (t % 3600) // 60, t % 60, m))
  return ' '.join(r)

def lucky(p, base):
  if p == 0.0: p = 0.00001
  return 1.0 - math.exp(-p / float(base)), float(base) / p

def parse_summary(r):
  global FOUND
  global STATUS_MSG
  if not (isinstance(r, (list, tuple)) and len(r) == 2):
    return
  try:
    if not r[0][0] == 'STATUS=S' and r[1][0] == 'SUMMARY':
      return
    d = r[1][1]
    FOUND = int(d['Found Blocks'])
    STATUS_MSG += 'Miner Status\n'
    STATUS_MSG += '  Uptime %s (Net Blocks %s)\n' % (parse_time(int(d['Elapsed'])), d['Network Blocks'])
    STATUS_MSG += '  Local / Work / Remote Speed: %.2f / %.2f / %.2f MHash/s\n' % (float(d['MHS av']), float(d['Work Utility']) * CONV_60_SHARE, float(d['Difficulty Accepted']) / int(d['Elapsed']) * CONV_4G)
    STATUS_MSG += '  Get / Remote Failures / HW Errors: %s / %s / %s\n' % (d['Get Failures'], \
              d['Remote Failures'], d['Hardware Errors'])
    STATUS_MSG += '  Getwork / Local Work / Discarded: %s / %s / %s\n' % (d['Getworks'], d['Local Work'], d['Discarded'])
    total = float(d['Difficulty Stale']) + float(d['Difficulty Rejected']) + float(d['Difficulty Accepted'])
    if total > 0:
      STATUS_MSG += 'Accepted / Rejected / Stale: %.2f (%s) / %.2f (%s) / %.2f (%s)\n' % (\
                     100. * float(d['Difficulty Accepted']) / total, d['Accepted'], \
                     100. * float(d['Difficulty Rejected']) / total, d['Rejected'], \
                     100. * float(d['Difficulty Stale']) / total, d['Stale'])
      STATUS_MSG += '  PPS Luck: %.2f %%\n' % (6000. * float(d['Difficulty Accepted']) / (float(d['Work Utility']) * int(d['Elapsed']))) # 4096 MH is 1 share, 100%*4096
      STATUS_MSG += '  Best Share / D1A: %s / %.2f (%s Blocks Found)\n' % (d['Best Share'], float(d['Difficulty Accepted']), d['Found Blocks'])
    else:
      STATUS_MSG += '  No Submited Shares Currently\n'
  except Exception as e:
    STATUS_MSG += e + '\n'

def get_lastshare(d, remote_time):
  last_share_time = remote_time - int(d['Last Share Time'])
  return last_share_time

def get_lastshare_str(d, remote_time):
  last_share_time = get_lastshare(d, remote_time)
  if last_share_time >= 7200:
    last_share = 'None'
  else:
    last_share = '%d s ago' % (last_share_time)
  return last_share

def parse_pools(r):
  global STATUS_MSG      
  if not isinstance(r, (list, tuple)):
    return
  try:
    if not r[0][0] == 'STATUS=S':
      return
    remote_time = int(r[0][1]['When'])
    for rp in r[1:]:
      if rp[0][0:4] != 'POOL': continue
      d = rp[1]
#      print d
      pool_type = 'Getwork'
      if d.get('Has Stratum', None) == 'true':
        pool_type = 'Stratum'
        if d.get('Stratum Active') == 'true':
          pool_type += ' (Activated)'
      elif d.get('Has GBT', None) == 'true':
        pool_type = 'GBT'
      elif d.get('Long Poll', None) == 'Y':
        pool_type = 'Getwork (LP)'

      last_share = get_lastshare_str(d, remote_time)
      if d['URL'].startswith('stratum+tcp://'): d['URL'] = d['URL'][14:]
      if d['URL'].startswith('http://'): d['URL'] = d['URL'][7:]
      d['URL'] = d['URL'].rstrip('/')

      STATUS_MSG += 'Pool (%s) %s (%s), Prio %s, %s\n' % (d['Status'], d['URL'], d['User'], d['Priority'], pool_type)
      STATUS_MSG += '  Last share %s, Diff %.2f\n' % (last_share, float(d['Last Share Difficulty']))
      STATUS_MSG += '  Get / Remote Failures: %s / %s\n' % (d['Get Failures'], \
              d['Remote Failures'])
      STATUS_MSG += '  Getwork / Discarded: %s / %s\n' % (d['Getworks'], d['Discarded'])
      total = float(d['Difficulty Stale']) + float(d['Difficulty Rejected']) + float(d['Difficulty Accepted'])
      if total > 0:
        STATUS_MSG += '  Accepted / Rejected / Stale: %.2f (%s, D1A %.2f, Best Share %s) / %.2f (%s) / %.2f (%s)\n' % (\
                     100. * float(d['Difficulty Accepted']) / total, d['Accepted'], float(d['Difficulty Accepted']), d.get('Best Share','Unknown'), \
                     100. * float(d['Difficulty Rejected']) / total, d['Rejected'], \
                     100. * float(d['Difficulty Stale']) / total, d['Stale'])
        STATUS_MSG += '  PPS Luck: %.2f %%\n' % (float(d['Difficulty Accepted']) / float(d['Diff1 Shares']) * 100.) # 4096 MH is 1 share, 100%*4096
      else:
        STATUS_MSG += '  No Shares Submitted\n'
#      print d
  except Exception as e:
    STATUS_MSG += e + '\n'

DEVICE_MAPPING = {'AVA': 'Avalon_ASIC', 'ICA': 'Icarus', 'BFL': 'BFL'}
def parse_dev(r):
  global STATUS_MSG      
  if not isinstance(r, (list, tuple)):
    return
  try:
    if not r[0][0] == 'STATUS=S':
      return
    remote_time = int(r[0][1]['When'])
    for rr in r[1:]:
      d = rr[1]
      device_type = 'Unknown'
      status = ''
      temp = d.get('Temperature', '0.00')
      if temp == '0.00': temp = 'Unknown'
      if rr[0].startswith('PGA') or rr[0].startswith('ASC'):
        device_type = DEVICE_MAPPING.get(d.get('Name', ''), 'Unknown FPGA')
        freq = d.get('Frequency', '0.00')
        if freq == '0.00':
          freq = d.get('frequency', 'Unknown')
        status = 'Freq %s, Temp %s C' % (freq, temp)

      if rr[0].startswith('GPU'):
        device_type = 'GPU'
        status = 'GPU %s Mem %s @ %s V, Temp %s C' % (d.get('GPU Clock','Unknown'), d.get('Memory Clock','Unknown'), d.get('GPU Voltage', 'Unknown'), temp)
        if d.get('Fan Speed', '-1') != '-1':
          status += ', Fan %s RPM (%s %%)' % (d['Fan Speed'], d.get('Fan Percent', 'Unknown'))
        elif d.get('Fan Percent', '-1') != -1:
          status += ', Fan %s %%' % (d['Fan Percent'])
        status += ', I: %s, Load %s %%' % (d.get('Intensity', 'Unknown'), d.get('GPU Activity', 'Unknown'))
        if d.get('Powertune', '0') != '0': status += ', PowerTune'

      last_share = get_lastshare(d, remote_time)
      enabled = d.get('Enabled', 'N')
      enabled_str = '*Disabled* ' if enabled != 'Y' else ''
      STATUS_MSG += '%s %sStatus: %s\n' % (device_type, enabled_str, d['Status'])
      if status:
        STATUS_MSG += '  ' + status + '\n'
      if float(d['MHS 5s']) == 0.0 and enabled:
        STATUS_MSG += '  *Warning*: Dead Device?\n'
      STATUS_MSG += '  5s / Avg Speed: %.2f / %.2f MHash/s\n' % (float(d['MHS 5s']), float(d['MHS av']))
      est_shareavg = float(d['Last Share Difficulty']) / (float(d['MHS av']) + 0.00001) * CONV_4G
      STATUS_MSG += '  Total D1W %s, Last share %s, Diff %.2f (Est %.2f sec per share)\n' % (d['Diff1 Work'], get_lastshare_str(d, remote_time), float(d['Last Share Difficulty']), est_shareavg)
      if int(d['Hardware Errors']) > 0:
        STATUS_MSG += '  HW Error: %s (%.2f %%)\n' % (d['Hardware Errors'], 100. * int(d['Hardware Errors']) / (int(d['Hardware Errors']) + int(d['Diff1 Work'])))
      else:
        STATUS_MSG += '  HW Error: None\n'
      STATUS_MSG += '  PPS Luck: %.2f %%\n' % (float(d['Difficulty Accepted']) / float(d['Diff1 Work']) * 100.)
  except Exception as e:
    STATUS_MSG += e + '\n'

def parse_notify(r):
  global STATUS_MSG
  if not isinstance(r, (list, tuple)):
    return
  try:
    if not r[0][0] == 'STATUS=S':
      return
    remote_time = int(r[0][1]['When'])
    notification_count = 0
    STATUS_MSG += 'Notices\n'
    for rr in r[1:]:
      d = rr[1]
      if d['Last Not Well'] == '0': continue
      notification_count += 1
      STATUS_MSG += '  Problem Device %s / %s: %s (%d sec ago)\n' % (d['ID'], d['Name'], d['Reason Not Well'], remote_time - int(d['Last Not Well']))
    if notification_count == 0:
      STATUS_MSG += '  All devices running fine.\n'
  except Exception as e:
    STATUS_MSG += e + '\n'

def parse_coin(r):
  global STATUS_MSG
  if not isinstance(r, (list, tuple)):
    return
  try:
    global BLOCK
    if not r[0][0] == 'STATUS=S':
      return
    if not r[1][0] == 'COIN':
      return
    remote_time = int(r[0][1]['When'])
    d = r[1][1]
    BLOCK = (d['Current Block Hash'][8:64])
    elapsed = int(remote_time - float(d['Current Block Time']))
    luck = lucky(elapsed, 600)
    STATUS_MSG += 'Block Status\n'
    STATUS_MSG += '  Block %s\n' % (d['Current Block Hash'][8:64])
    STATUS_MSG += '  Algo %s, Diff %s\n' % (d['Hash Method'], d['Network Difficulty'])
    STATUS_MSG += '  Received at %s (%d sec ago, Luck %.2f %%)\n' % (time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(float(d['Current Block Time']))), elapsed, luck[0] * 100.0)
  except Exception as e:
    STATUS_MSG += e + '\n'

def parse_config(r):
  global STATUS_MSG
  if not isinstance(r, (list, tuple)):
    return
  try:
    if not r[0][0] == 'STATUS=S':
      return
    if not r[1][0] == 'CONFIG':
      return
    d = r[1][1]
    STATUS_MSG += 'Devices: %s GPU, %s FPGA, %s ASIC\n' % (d.get('GPU Count','0'), d.get('PGA Count','0'),d.get('ASC Count','0'))
    STATUS_MSG += '%s Pool(s) configured with strategy %s\n' % (d['Pool Count'], d['Strategy'])
  except Exception as e:
    STATUS_MSG += e + '\n'

def parse_pools_list(r):
  if not isinstance(r, (list, tuple)):
    return
  ret = []
  try:
    if not r[0][0] == 'STATUS=S':
      return
    remote_time = int(r[0][1]['When'])
    for rp in r[1:]:
      if rp[0][0:4] != 'POOL': continue
      d = rp[1]
      ret.append((d['URL'].replace('://', '://' + urllib.quote(d['User']) + '@'), int(d['Priority'])))
  except:
    pass
  return ret

def conv_prio_dict(p):
  if isinstance(p, (tuple, list, )):
    try:
      pd = dict(p)
    except TypeError: # not able to convert
      pd = zip(p, range(len(p)))
    return pd
  if isinstance(p, dict):
    return p
  return {}

def escape_api(s):
  return s.replace('\\', '\\\\').replace(',', '\\,')

# Note: p2 should have pass
def matching_pools(p1, p2=None):
  p1 = conv_prio_dict(p1)
  p2 = conv_prio_dict(p2)
  p1_s = sorted(p1, key=p1.get)
  # if d['URL'].startswith('stratum+tcp://'): d['URL'] = d['URL'][14:]
  # if d['URL'].startswith('http://'): d['URL'] = d['URL'][7:]

oldblock = '0'

if __name__ == '__main__':
  import sys
  #if len(sys.argv) < 2: raise Exception('Usage: python %s IP [PORT]' % sys.argv[0])
  host = '127.0.0.1'
  port = 4028
  if len(sys.argv) == 3:
    port = int(sys.argv[2])
   # Create NeoPixel object with appropriate configuration.
  strip = NeoPixel(LED_PIN, LED_COUNT, brightness = LED_BRIGHTNESS, auto_write = AUTO_WRITE)

  while True:
          s = cg_rpc(host, port, 'config')
          parse_config(s)
          s = cg_rpc(host, port, 'summary')
          parse_summary(s)
          s = cg_rpc(host, port, 'coin')
          parse_coin(s)
          s = cg_rpc(host, port, 'notify')
          parse_notify(s)
          s = cg_rpc(host, port, 'pools')
          matching_pools(parse_pools_list(s))
          parse_pools(s)
          s = cg_rpc(host, port, 'devs')
          parse_dev(s)
          
          block = BLOCK[1:]
          STATUS_MSG += BLOCK + '\n'
          STATUS_MSG += 'FOUND: ' + str(FOUND) + '\n'
          
          dispBlock(strip, block)
          #print(STATUS_MSG)
          if (block!=oldblock):
                  WINCHECK = 'New block detected.\n'
                  oldblock = block
                  if(FOUND>0):
                          WINCHECK += 'WINNER!\n'
                          #print(WINCHECK)
                          winner(strip)
                  elif(FOUND ==0):
                          WINCHECK += 'loser...\n'
                          #print(WINCHECK)
                          loser(strip)
                  f = open("winlog.txt", "a")
                  f.write(STATUS_MSG)
                  f.write(WINCHECK)
                  f.close
                  WINCHECK = ""
          STATUS_MSG = ""
          time.sleep(1)
  #print s
  # TODO: config, devdetails, stats
