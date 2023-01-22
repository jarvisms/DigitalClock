#!/usr/bin/python3

import os, pygame, sys, json
from datetime import datetime, timedelta
from time import sleep
import paho.mqtt.client as mqtt

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

displayinfo = pygame.display.Info()
width, height = (displayinfo.current_w, displayinfo.current_h)
pygame.mouse.set_visible(False)
screen = pygame.display.set_mode()
displayupdate = pygame.display.update
pygame.font.init()
weatherdata = {'idx':datetime.min, 'temp_out':float("nan")} # Placeholder

upsidedown = False  # Set this to True to rotate everything - useful for the Pimoroni Screen Mount
mqttclient=mqtt.Client("MQTTClientID")  # Unique for the Broker
_ = mqttclient.connect('MQTTBroker')

def on_connect(client, userdata, flags, rc):
  """Subscribe on connection. This allows for auto-reconnect to also resubscribe"""
  client.subscribe("/weather/pywws")  # Using pywws MQTT Service

def on_message(client,userdata,message):
  """When MQTT message containing weather station data arrives, extract the relevent parts, convert them into a sensible format and store them in the global object"""
  global weatherdata
  payload = json.loads(str(message.payload.decode("utf-8")))
  weatherdata = { 'idx': datetime.fromisoformat(payload['idx']), 'temp_out': float(payload['temp_out']) }

mqttclient.on_connect = on_connect
mqttclient.on_message = on_message
mqttclient.loop_start()

# Seems to work on a Raspberry Pi Screen at 800x480 resolution
font = "digital-7 (mono).ttf"
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
dw, dh = datafont.size("-88.8'C 88/88/88")  # Get size of the rendered time at current fontsize
a = datafontsize*width*0.95/dw    # See what fontsize would fill 95% of the screen width
b = datafontsize*(height-th)*0.95/dh   # See what fontsize would fill 95% of the screen height with the time
datafontsize = int(a if a < b else b) # Take the smaller of the two potential size as an integer
datafont = pygame.font.Font(font, datafontsize)

clr = [255,0,0]
i = 0
inc = 8
_ = screen.fill((0,0,0))

while True:
  now = datetime.now()
  timetext = now.strftime("%H %M %S") if now.second % 2 else now.strftime("%H:%M:%S") # Colons flash on odd/even seconds
  if now - weatherdata['idx'] <= timedelta(minutes=15):
    temp = weatherdata['temp_out']
    datatext = f"{temp: > 5,.1f}'C {now:%d/%m/%y}"
  else:
    datatext = f"{now:%d/%m/%y}"  # If there is no temperature data (or its too old), just show the date
  if clr[i] >= 255:
    clr[i] = 256
  clr[i] += inc
  if clr[i] >= 255:
    clr[i] = 255
    i = (i+1)%3
    inc = -1 * inc
  elif clr[i] <= 0:
    clr[i] = 0
    i = (i-2)%3
    inc = -1 * inc
  background = (255-clr[0], 255-clr[1], 255-clr[2])
  _ = screen.fill(background)
  timesurface = timefont.render(timetext, True, clr, background)
  datasurface = datafont.render(datatext, True, clr, background)
  textsize = tw, th = timesurface.get_size()
  datasize = dw, dh = datasurface.get_size()
  gap = int( (height-th-dh)/3 )  # The total gap evenly split between top, bottom and between the text
  if upsidedown:
    tpos = (int((width-tw)/2), 2*gap + dh)  # Centered Time on first line, but time has coordinates below data due to rotation
    dpos = (int((width-dw)/2), gap)  # Centered Data on second line, but data has coordinates above time due to rotation
    timerect = screen.blit(pygame.transform.rotate(timesurface, 180), tpos) # 180 Rotation for Raspberry Pi Screen in Pimoroni mount
    datarect = screen.blit(pygame.transform.rotate(datasurface, 180), dpos) # 180 Rotation for Raspberry Pi Screen in Pimoroni mount
  else:
    tpos = (int((width-tw)/2), gap)  # Centered Time on first line
    dpos = (int((width-dw)/2), 2*gap + th)  # Centered Data on second line
    timerect = screen.blit(timesurface, tpos)
    datarect = screen.blit(datasurface, dpos)
  displayupdate()
  wait = ( now.replace(microsecond=0) + timedelta(seconds=1) - datetime.now() ).total_seconds()
  sleep(wait if wait > 0 else 0)

mqttclient.loop_stop()
pygame.quit()
