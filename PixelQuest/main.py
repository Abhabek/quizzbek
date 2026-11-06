import pygame

pygame.init()

screen = pygame.display.set_mode((900, 600))
pygame.display.set_caption("Pixel Quest: Hexlet Adventure")

clock = pygame.time.Clock()
running = True

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    screen.fill((30, 100, 50))
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
