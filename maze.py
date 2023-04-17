# Quick and dirty raycasting engine
# Author: Peter R. Hague

import pygame
import numpy as np
from glob import glob

# pygame setup
pygame.init()
screen = pygame.display.set_mode((1280, 720))
clock = pygame.time.Clock()
running = True

# game variables
dt = 0
speed = 300 # player movement speed
dtheta = np.pi/4 # player rotation speed
fov = np.pi/3
pixelStep = 1 # How many pixels per ray 
playerPos = pygame.Vector2(9.5,9.5)
playerDir = 0

maze = []
with open("assets/map.csv", "r") as f:
    for line in f:
        maze.append([int(i) for i in line.split(",")])
maze = np.array(maze)

assetdict = {}
for texturefile in glob("assets/*.png"):
    idx = int(texturefile.split(".")[0].split("_")[1]) # textures must be formatted as "<name>_<index>.png" and will all be loaded in
    assetdict[idx] = texturefile
    
walls =[]    
for texturefile in sorted(assetdict):
    rawwall = pygame.image.load(assetdict[texturefile])
    newwall = pygame.Surface((512+pixelStep, 512))
    newwall.blit(rawwall, (0,0))
    newwall.blit(rawwall, (512,0))
    walls.append(newwall)


def drawminimap(screen, maze, playerPos, playerDir, fov):
    pygame.draw.rect(screen, "blue", (1000, 600, 100, 100))
    for y in range(maze.shape[1]):
        for x in range(maze.shape[0]):
            if maze[x, y]>0:
                pygame.draw.rect(screen, "white", (1000+x*5, 600+y*5, 5, 5))
    
    pygame.draw.line(screen, "red", (1000+playerPos.x*5, 600+playerPos.y*5), (1000+playerPos.x*5+np.cos(playerDir)*10, 600+playerPos.y*5+np.sin(playerDir)*10), 2)
    pygame.draw.line(screen, "green", (1000+playerPos.x*5, 600+playerPos.y*5), (1000+playerPos.x*5+np.cos(playerDir+fov/2)*10, 600+playerPos.y*5+np.sin(playerDir+fov/2)*10), 2)
    pygame.draw.line(screen, "green", (1000+playerPos.x*5, 600+playerPos.y*5), (1000+playerPos.x*5+np.cos(playerDir-fov/2)*10, 600+playerPos.y*5+np.sin(playerDir-fov/2)*10), 2)
    
# Prepare a background with a gradient    
background = pygame.Surface((1280, 720))
for y in range(360):
    pygame.draw.line(background, (0,0,128), (0, y), (1280, y), 2)
    col = int(255 - y/300*255)
    pygame.draw.line(background, (max(0,col), max(0,col), max(0,col)), (0, 720-y), (1280, 720-y), 2)

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            
    screen.blit(background, (0,0))

    for col in range(0, 1280, pixelStep):
        ray = playerDir + (col-640)/(1280/fov) # Angle of ray
        gridx, gridy = int(playerPos.x), int(playerPos.y) # Grid position of player
        rx, ry = playerPos.x - float(gridx), playerPos.y - float(gridy) # Position of player in grid cell
        ddistx, ddisty = np.abs(1./np.cos(ray)), np.abs(1./np.sin(ray)) # Distance between grid lines
        stepx, stepy = int(np.sign(np.cos(ray))), int(np.sign(np.sin(ray))) # Direction of ray
        sidedistx, sidedisty= ddistx * (1-rx) if stepx>0 else ddistx * rx, ddisty * (1-ry) if stepy>0 else ddisty * ry # Distance to next grid line
        
        # Find the ray intersection
        hit = False
        while not hit:
            if sidedistx<sidedisty:
                sidedistx += ddistx
                gridx += stepx
                side = 0
            else:
                sidedisty += ddisty
                gridy += stepy
                side = 1
            if maze[gridx, gridy]>0:
                hit = True
                
        distance = sidedistx - ddistx if side==0 else sidedisty - ddisty
        distance *= np.cos(playerDir-ray) # Convert to distance from viewer plane, removes fisheye effect

        # Draw a column of the wall texture
        wallpos = playerPos.x + distance*np.cos(ray) if side==1 else playerPos.y + distance*np.sin(ray)
        wallpos -= np.floor(wallpos)
        if wallpos<=0 or wallpos>=1:
            print(wallpos)
        wallpos *= 512

        height = 360/distance
        
        # Shade and draw the column
        dark = pygame.Surface((pixelStep, 512))
        dark.fill((0,0,0))
        texture = pygame.Surface((pixelStep, 512))
        texture.set_alpha(255/distance)
        texture.blit(walls[maze[gridx, gridy]-1], (0,0), (wallpos, 0, pixelStep, 512))
        dark.blit(texture, (0,0))

        screen.blit(pygame.transform.scale_by(dark, (1,(height*2)/512)), (col, 360-height))
    
    drawminimap(screen, maze, playerPos, playerDir, fov)
    
    # Player movement
    keys = pygame.key.get_pressed()
    newpos = playerPos.copy()
    if keys[pygame.K_w]:
        newpos.x += np.cos(playerDir) * dt
        newpos.y += np.sin(playerDir) * dt
    if keys[pygame.K_s]:
        newpos.x -= np.cos(playerDir) * dt
        newpos.y -= np.sin(playerDir) * dt
    if keys[pygame.K_a]:
        playerDir -= dtheta*dt
    if keys[pygame.K_d]:
        playerDir += dtheta*dt

    # Collision detection
    if maze[int(newpos.x), int(newpos.y)]==0:
        playerPos = newpos

    pygame.display.flip()
    dt = clock.tick(60) / speed

pygame.quit()