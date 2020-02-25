#!/usr/bin/python3

import os, pygame, sys
from datetime import datetime, timedelta
from time import sleep

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
size = width, height = (displayinfo.current_w, displayinfo.current_h)
pygame.mouse.set_visible(False)
screen = pygame.display.set_mode(size, pygame.FULLSCREEN)
displayupdate = pygame.display.update
pygame.font.init()

# Seems to work on a Raspberry Pi Screen at 800x480 resolution
fontsize = 200
font = "digital-7 (mono).ttf"
myfont = pygame.font.Font(font, fontsize)
tw, th = myfont.size("23:59:59")  # Get size of the rendered time at current fontsize
a = fontsize*width*0.95/tw    # See what fontsize would fill 95% of the screen width
b = fontsize*height*0.95/th   # See what fontsize would fill 95% of the screen height
fontsize = int(a if a < b else b) # Take the smaller of the two potential size as an integer
myfont = pygame.font.Font(font, fontsize)

clr = [255,0,0]
i = 0
inc = 8
sec = True
_ = screen.fill((0,0,0))
while True:
  now = datetime.now()
  timetext = now.strftime("%H:%M:%S") if sec else now.strftime("%H %M %S")
  sec = not sec
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
  textsurface = myfont.render(timetext, True, clr, background)
  #textsurface = myfont.render(timetext, True, clr, (0,0,0))
  textsize = tw, th = textsurface.get_size()
  pos = ((width-tw)/2, (height-th)/2)  # Centered
  textrect = screen.blit(textsurface,pos)
  displayupdate()
  #displayupdate(textrect)
  wait = ( now.replace(microsecond=0) + timedelta(seconds=1) - datetime.now() ).total_seconds()
  sleep(wait if wait > 0 else 0)
