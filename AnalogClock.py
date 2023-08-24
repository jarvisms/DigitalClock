import pygame
from math import sin, cos, radians
from datetime import datetime, timedelta, timezone

pygame.display.init()
screen = pygame.display.set_mode((600, 600), pygame.RESIZABLE)
pygame.display.set_caption('Analogue Clock')
run = True

def set_sizes(screen_width, screen_height):
  global diameter, offset_w, offset_h, ticklength, tickthickness, tickradius, hourhandlength, minhandlength, sechandlength
  diameter = min(screen_width, screen_height)
  offset_w = (screen_width - diameter) // 2
  offset_h = (screen_height - diameter) // 2
  ticklength = diameter // 20
  tickthickness = ticklength // 3
  tickradius = diameter//2 - ticklength//2
  hourhandlength = (diameter//2) - (ticklength*4)
  minhandlength  = (diameter//2) - ticklength
  sechandlength  = tickradius

def draw_ticks():
  clockface = pygame.Surface( (diameter,diameter), flags=pygame.SRCALPHA) # This surface will be the clock face with tick marks
  clockface.fill((0,0,0))
  for angle in range(0, 360, 6):  # Loop round all minute markers
    if angle % 90 == 0: # 3,6,9,12 O'clock will be longer lines
      dashsurface = pygame.Surface( (tickthickness, ticklength), flags=pygame.SRCALPHA )  # Surface for the dash itself
    elif angle % 30 == 0: # All other hours will be smaller
      dashsurface = pygame.Surface( (tickthickness, tickthickness), flags=pygame.SRCALPHA )  # Surface for the dash itself
    else:   # Individual minutes will be small 
      dashsurface = pygame.Surface( (tickthickness//2 , tickthickness//2), flags=pygame.SRCALPHA )  # Surface for the dash itself
    dashsurface.fill((128, 128, 128)) # Fill the dash with grey
    dashsurface = pygame.transform.rotate(dashsurface, -angle)  # Rotate according to the position on the clock face
    x = diameter//2 + tickradius*cos(radians(angle - 90)) - dashsurface.get_width()//2   # Move it to the location around the radius of the clock
    y = diameter//2 + tickradius*sin(radians(angle - 90)) - dashsurface.get_height()//2  # Move it to the location around the radius of the clock
    clockface.blit(dashsurface, (x,y) )   # Blit the dash into the clock face
  return clockface  # Return the clock face with just dashes on

def clock_hand(radius, angle, thickness, color):
  clockface = pygame.Surface( (diameter,diameter), flags=pygame.SRCALPHA) # This surface will be the clock face with a clock hand
  handsurface = pygame.Surface( (thickness, radius), flags=pygame.SRCALPHA ) # Tall upright surface representing the hand
  handsurface.fill(color) # Fill it with the chosen colour of the clock hand
  handsurface = pygame.transform.rotate(handsurface, -angle)  # Rotate according to the angle the hand would be at
  x = diameter//2 + radius*cos(radians(angle - 90))//2 - handsurface.get_width()//2   # Move the centre of the hand so that one end is on the center point
  y = diameter//2 + radius*sin(radians(angle - 90))//2 - handsurface.get_height()//2  # Move the centre of the hand so that one end is on the center point
  clockface.blit(handsurface, (x,y) )
  return clockface

pygame.event.set_blocked(None)  # Ignore all events
pygame.event.set_allowed(pygame.QUIT) # Only pay attention to the QUIT event
pygame.event.set_allowed(pygame.VIDEORESIZE) # ...and pay attention to the VIDEORESIZE event
set_sizes(*screen.get_size())
face = draw_ticks() # Generate the clock face

while run:
  for event in pygame.event.get():
    if event.type == pygame.QUIT: # Check for QUIT event
      print("Quit")
      run = False
    if event.type == pygame.VIDEORESIZE: # Check for window resizing
      print(f"Resize: {event.w} x {event.h}")
      screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
      set_sizes(event.w, event.h)
      face = draw_ticks()
  now = datetime.now(tz=timezone.utc) # Grab current time
  nowlocal = now.astimezone() # Convert to local time
  # Hour hand increments 30° per hour, 1/2° per minute and 1/120° per second
  hourhand = clock_hand(hourhandlength, (nowlocal.hour + nowlocal.minute/60 + nowlocal.second/3600) * 30, ticklength//2, (255, 0, 0))
  # Minute hand increments 6° per min and 1/10° per second
  minutehand = clock_hand(minhandlength, (nowlocal.minute + nowlocal.second/60)*6, tickthickness, (0, 0, 255))
  # Second hand increments 6° per second
  secondhand = clock_hand(sechandlength, (nowlocal.second + nowlocal.microsecond/1000000)*6, tickthickness//5, (0, 255, 0))
  screen.blits( ((face,(offset_w, offset_h)), (hourhand,(offset_w, offset_h)), (minutehand,(offset_w, offset_h)), (secondhand,(offset_w, offset_h))) )
  pygame.draw.circle(screen, (128,128,128), (offset_w+diameter//2, offset_h+diameter//2), diameter//40 ) # Put a circle in the middle
  pygame.display.update() # Show it all on the screen
  wait = int(( now + timedelta(seconds=0.05) - datetime.now(tz=timezone.utc) ).total_seconds() * 1000)  # Work out how many milliseconds to wait for about 20 FPS
  pygame.time.wait(wait if wait > 0 else 0) # Wait that long, but if its been too long, dont wait at all

pygame.quit()
