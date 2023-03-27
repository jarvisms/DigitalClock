#!/usr/bin/python3

import os, pygame, json, signal
from datetime import datetime, timedelta, timezone
from time import sleep
from os.path import join, dirname, abspath
from configparser import ConfigParser
import paho.mqtt.client as mqtt

def on_connect(client, userdata, flags, rc):
  """Subscribe on connection. This allows for auto-reconnect to also resubscribe"""
  client.subscribe([(energytopic + "/#",0),(weathertopic,0)])  # Using pywws and glowmarkt glow IHD/CAD MQTT Services

def on_message(client,userdata,message):
  """When MQTT messages containing energy or weather data arrives, store them in the global object"""
  global data
  payload = json.loads(str(message.payload.decode("utf-8")))
  if message.topic == weathertopic and 'temp_out' in payload:
    data['weather'].update({ 'idx': datetime.fromisoformat(payload['idx']).replace(tzinfo=timezone.utc), 'temp_out': float(payload['temp_out']) })
  elif message.topic.startswith(energytopic):
    for u in payload.keys() & ("electricitymeter","gasmeter"):
      ci = payload[u]["energy"]["import"]["cumulative"]
      ts = datetime.fromisoformat(payload[u]["timestamp"].replace("Z","+00:00"))
      if ( ci is not None ) and ( ci != data[u]["cumulative"] ):
        data[u]["previouscumulative"] = data[u]["cumulative"]
        data[u]["previoustimestamp"] = data[u]["timestamp"]
        data[u]["cumulative"] = ci
        data[u]["timestamp"] = ts
      if "power" in payload[u]:
        data[u]["power"] = payload[u]["power"]["value"]
      elif (ts-data[u]["timestamp"]).total_seconds() <= 120 and (dt := (data[u]["timestamp"] - data[u]["previoustimestamp"]).total_seconds()) <= 120:
        data[u]["power"] = 3600*(data[u]["cumulative"] - data[u]["previouscumulative"]) / dt
      else:
        data[u]["power"] = 0
        data[u]["timestamp"] = ts

def colours(idx, step=1):
  """Given a number idx, returns a RGB colour derived from that number which is repeatable.
  Step defines how much the RGB values will increment for each increment of the idx.
  For a given idx and Step, the output is always the same."""
  idx = int(idx % (1536 / step))  # 256*6=1536 total cycle length of 6 phases
  halfphase = 256 // step   # 6 half-phases in a full cycle
  fullphase = 512 // step   # 3 full-phases in a full cycle
  ud,m = divmod(idx, halfphase)   # ud = up/down direction from whether it's odd or even, m is the 0-255 value in that half-phase
  if ud % 2:                     # Odd => Down
    v = min(256 - m * step, 255)  # Counting downwards 255-->0. 256 is replaced with 255
  else:                          # Even => Up
    v = min(m * step, 255)        # Counting upwards 0-->255. 256 is replaced with 255
  colour=[None,None,None]
  colour[ ( 2+ ud) %3 ] = v   # Rotates 6 times for each cycle, 3 up and 3 down with variable numbers
  colour[ ( 1- ( idx // fullphase ) ) %3 ] = 0   # Rotates 3 times for each cycle
  colour[ ( 3- ( (idx + halfphase) // fullphase ) ) %3 ] = 255    # Rotates 3 times for each cycle, but in antiphase, i.e. half-phase out.
  return colour

def quitter(signum, frame):
  global run
  print(f"Signal handler called with signal {signum} - {signal.Signals(signum).name}")
  run = False

run = True
signal.signal(signal.SIGINT, quitter)
signal.signal(signal.SIGTERM, quitter)
cfg = ConfigParser()
cfg.read( join( dirname(abspath(__file__)), "Clock.cfg" ))
weathertopic = cfg.get('MQTT','WeatherTopic',fallback='/weather/pywws')
energytopic = cfg.get('MQTT','EnergyTopic',fallback='/glow/')
upsidedown = cfg.getboolean('DEFAULT','upsidedown', fallback=False)  # Set this to True to rotate everything - useful for the Pimoroni Screen Mount
#drivers = ('X11', 'dga', 'ggi','vgl','aalib','directfb', 'fbcon', 'svgalib')
drivers = ('directfb', 'fbcon', 'svgalib')

os.putenv('SDL_FBDEV','/dev/fb0')
os.environ["SDL_FBDEV"] = "/dev/fb0"

found = False
for driver in drivers:
  if not os.getenv('SDL_VIDEODRIVER'):
    os.putenv('SDL_VIDEODRIVER',driver)
  try:
    pygame.display.init()
    print(f"Success with {driver}")
  except pygame.error:
    print(f"{driver} Failed")
    continue
  found = True
  break

if not found:
  raise Exception('No suitable video driver found.')

data = { u: { "timestamp":datetime.min.replace(tzinfo=timezone.utc), "cumulative":float("nan"), "previoustimestamp": datetime.min.replace(tzinfo=timezone.utc), "previouscumulative":float("nan"), "power":0.0} for u in ("electricitymeter","gasmeter")}
data.update( { "weather": { 'idx': datetime.min.replace(tzinfo=timezone.utc), 'temp_out': float("nan") }})

displayinfo = pygame.display.Info()
width, height = (displayinfo.current_w, displayinfo.current_h)
pygame.mouse.set_visible(False)
screen = pygame.display.set_mode()
displayupdate = pygame.display.update
pygame.font.init()
weatherdata = {'idx':datetime.min, 'temp_out':float("nan")} # Placeholder

mqttclient=mqtt.Client(cfg.get('MQTT','clientid', fallback=None))  # Unique for the Broker
mqttclient.on_connect = on_connect
mqttclient.on_message = on_message
mqttclient.username_pw_set(cfg.get('MQTT','username', fallback=None),cfg.get('MQTT','password', fallback=None))
_ = mqttclient.connect(cfg.get('MQTT','broker'))
mqttclient.loop_start()

# Seems to work on a Raspberry Pi Screen at 800x480 resolution
font = cfg.get('DEFAULT','font', fallback='digital-7 (mono).ttf')
timefontsize = 200
timefont = pygame.font.Font(font, timefontsize)
tw, th = timefont.size("23:59:59")  # Get size of the rendered time at current fontsize
a = timefontsize*width*0.95/tw    # See what fontsize would fill 95% of the screen width
b = timefontsize*height*0.95/th   # See what fontsize would fill 95% of the screen height (This takes priority)
timefontsize = int(a if a < b else b) # Take the smaller of the two potential size as an integer
timefont = pygame.font.Font(font, timefontsize)

tw, th = timefont.size("23:59:59")  # Get size of the rendered time at current fontsize
datafontsize = 200
datafont = pygame.font.Font(font, datafontsize)
dw, dh = datafont.size("-88.8'C 88/88/88")  # Get size of the rendered weather data and date at current fontsize
ew, eh=  datafont.size("88,888W 88,888W")  # Get size of the rendered energy data at current fontsize
a = datafontsize*width*0.95/max(dw,ew)    # See what fontsize would fill 95% of the screen width
b = datafontsize*(height-th)*0.95/(dh+eh)   # See what fontsize would fill 95% of the screen height with the time
datafontsize = int(a if a < b else b) # Take the smaller of the two potential size as an integer
datafont = pygame.font.Font(font, datafontsize)

_ = screen.fill((0,0,0))

while run:
  now = datetime.now(tz=timezone.utc)
  timetext = now.astimezone().strftime("%H %M %S") if now.second % 2 else now.astimezone().strftime("%H:%M:%S") # Colons flash on odd/even seconds
  if now - data['weather']['idx'] <= timedelta(minutes=15):
    temp = data['weather']['temp_out']
    datatext = f"{temp: > 5,.1f}'C {now:%d/%m/%y}"
  else:
    datatext = f"{now:%d/%m/%y}"  # If there is no temperature data (or its too old), just show the date
  if now - data['electricitymeter']['timestamp'] <= timedelta(minutes=15):
    elec = data['electricitymeter']['power']*1000
    electext = f"{elec: >5,.0f}W "
  else:
    electext = "        "  # If there is no elec data (or its too old), just show a blank space
  if now - data['gasmeter']['timestamp'] <= timedelta(minutes=15):
    gas = data['gasmeter']['power']*1000
    gastext = f" {gas: >5,.0f}W"
  else:
    gastext = "        "  # If there is no gas data (or its too old), just show a blank space
  energytext = electext+gastext
  clr = colours(now.timestamp(), 8)
  background = (255-clr[0], 255-clr[1], 255-clr[2])
  _ = screen.fill(background)
  timesurface = timefont.render(timetext, True, clr, background)
  datasurface = datafont.render(datatext, True, clr, background)
  energysurface = datafont.render(energytext, True, clr, background)
  textsize = tw, th = timesurface.get_size()
  datasize = dw, dh = datasurface.get_size()
  energysize = ew, eh = energysurface.get_size()
  gap = int( (height-th-dh-eh)/3 )  # The total gap evenly split between top, bottom and between the text
  if upsidedown:
    tpos = (int((width-tw)/2), 2*gap + dh + eh)  # Centered Time on first line, but time has coordinates below data due to rotation
    dpos = (int((width-dw)/2), gap + eh)  # Centered Data on second line, but data has coordinates above time due to rotation
    epos = (int((width-ew)/2), gap)  # Centered Data on third line, but energy has coordinates above time due to rotation
    timerect = screen.blit(pygame.transform.rotate(timesurface, 180), tpos) # 180 Rotation for Raspberry Pi Screen in Pimoroni mount
    datarect = screen.blit(pygame.transform.rotate(datasurface, 180), dpos) # 180 Rotation for Raspberry Pi Screen in Pimoroni mount
    energyrect = screen.blit(pygame.transform.rotate(energysurface, 180), epos) # 180 Rotation for Raspberry Pi Screen in Pimoroni mount
  else:
    tpos = (int((width-tw)/2), gap)  # Centered Time on first line
    dpos = (int((width-dw)/2), 2*gap + th)  # Centered Data on second line
    epos = (int((width-ew)/2), 2*gap + th + dh)  # Centered Data on third line
    timerect = screen.blit(timesurface, tpos)
    datarect = screen.blit(datasurface, dpos)
    energyrect = screen.blit(energysurface, epos)
  displayupdate()
  wait = ( now.replace(microsecond=0) + timedelta(seconds=1) - datetime.now(tz=timezone.utc) ).total_seconds()
  sleep(wait if wait > 0 else 0)

mqttclient.loop_stop()
pygame.quit()
