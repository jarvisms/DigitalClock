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

size = width, height = (pygame.display.Info().current_w, pygame.display.Info().current_h)
pygame.mouse.set_visible(False)
screen = pygame.display.set_mode(size, pygame.FULLSCREEN)
pygame.font.init()

# Seems to work on a Raspberry Pi Screen at 800x480 resolution
fontsize = 200
font = "digital-7 (mono).ttf"
myfont = pygame.font.Font(font, fontsize)

while True:
  now = datetime.now()
  timetext = now.strftime("%H:%M:%S")
  _ = screen.fill( (0,0,0) )  # black
  textsurface = myfont.render(timetext, True, (255, 0, 255))  # Magenta
  textsize = tw, th = textsurface.get_size()
  pos = tuple(map( lambda s, t : (s-t)/2, size, textsize))  # Centered
  _ = screen.blit(textsurface,pos)
  pygame.display.update()
  wait = now.replace(microsecond=0) + timedelta(seconds=1) - now
  sleep(wait.total_seconds())