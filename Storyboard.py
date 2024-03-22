import pyray as rl
from pyray import Camera3D, Color, KeyboardKey, Matrix, Rectangle, Vector2, Vector3, Vector4
import time as t
screenWidth = 800
screenHeight = 450
RAYWHITE = Color(245, 245, 245, 255)
BLACK = Color(1, 1, 1, 255)

rl.init_window(screenWidth, screenHeight, "Story")

page2 = rl.load_texture("storyboard_image/bombe_nucleaire.jpg")
page3 = rl.load_texture("storyboard_image/refri-trump-pixel.jpg")
page4 = rl.load_texture("storyboard_image/cookie.jpg")
page5 = rl.load_texture("storyboard_image/on_se_casse.jpg")
font = rl.load_font_ex("storyboard_image/ABC.ttf", 64, 0, 10)

Page = 0

rl.set_target_fps(60)
syc=False
while not rl.window_should_close():
    if rl.is_key_down(rl.KeyboardKey.KEY_SPACE) and syc==False:
        Page+=1
        syc=True
    rl.begin_drawing()

    rl.clear_background(BLACK)

    if Page==1:
        rl.draw_text("2026. La Terre est dans un état critique", 10, int(screenHeight/2 + page4.width/2), 20, RAYWHITE)

    if Page==2:
        rl.draw_texture(page2, int(screenWidth/2 - page2.width/2), 50, RAYWHITE)
        rl.draw_text("L'Europe est ravagé par la guerre nucléaire causée par Poutine", 10, int(screenHeight/2 + page4.width/2), 20, RAYWHITE)

    if Page==3:
        rl.draw_texture(page3, int(screenWidth/2 - page3.width/2), 50, RAYWHITE)
        rl.draw_text("Les Etats-Unis se sont effondrés sous le gouvernement de Trump", 10, int(screenHeight/2 + page4.width/2), 20, RAYWHITE)

    if Page==4:
        rl.draw_texture(page4, int(screenWidth/2 - page4.width/2), 50, RAYWHITE)
        rl.draw_text("Et lorsque le dernier cookie de la boîte disparu mystérieusement", 10, int(screenHeight/2 + page4.width/2), 20, RAYWHITE)

    if Page==5:
        rl.draw_texture(page5, int(screenWidth/2 - page5.width/2), 50, RAYWHITE)
        rl.draw_text("Les Terminales NSI partirent en quête d'un monde meilleur", 10, int(screenHeight/2 + page5.width/2), 20, RAYWHITE)

    rl.end_drawing()
    if syc==True:
        t.sleep(3)
        syc=False
rl.close_window()