import pyray as rl
from pyray import Color, Rectangle, Vector2

from colors import GREEN, WHITE
from player import Player
from system import Planet, System

def rescale(cockpit_rec: Rectangle) -> Rectangle:
    """Rescales a rectangle in image cockpit dimensions to screen dimensions"""
    scale_x = rl.get_render_width() / 1280
    scale_y = rl.get_render_height() / 720
    return Rectangle(cockpit_rec.x*scale_x, cockpit_rec.y*scale_y, cockpit_rec.width*scale_x, cockpit_rec.height*scale_y)

def draw_text_centered(text: str, rect: Rectangle, font_size: int, color: Color):
    size = rl.measure_text_ex(rl.get_font_default(), text, font_size, font_size/10.0)

    x = rect.x + rect.width/2 - size.x/2
    y = rect.y + rect.height/2 - size.y/2

    rl.draw_text(text, int(x), int(y), font_size, color)

class Cockpit:
    def __init__(self):
        self.vaisseau = rl.load_texture("assets/cockpit.png")

        self.scan_percent = 0.0

    def draw(self, player: Player, sys: System, selected: Planet | None):
        rl.draw_texture_pro(
            self.vaisseau,
            Rectangle(0, 0, 1280, 720), Rectangle(0, 0, rl.get_render_width(), rl.get_render_height()),
            Vector2(0, 0), 0.0, WHITE
        )

        if selected == None:
            return

        top_left_screen = rescale(Rectangle(507, 453, 101, 23))
        top_right_screen = rescale(Rectangle(668, 452, 103, 25))
        bottom_screen = rescale(Rectangle(554, 496, 171, 60))

        font_size = min(int(20 * (rl.get_render_width()/1920)), int(20 * (rl.get_render_height()/1080)))
        font_size = (font_size // 5) * 5 # take the smaller multiple of 5 to get crisp text

        if selected == sys.bodies[0]:
            # THE SUN
            draw_text_centered("15000 °C", bottom_screen, 2*font_size, Color(0xcd, 0x64, 0, 0xff))
        elif selected.scanned:
            draw_text_centered(f"{selected.eau}% H²0", top_left_screen, font_size, GREEN)
            draw_text_centered(f"{selected.oxygen}% de 0²", top_right_screen, font_size, GREEN)
            draw_text_centered(f"{selected.temp} °C", bottom_screen, font_size, GREEN)
        else:
            if rl.vector_3distance_sqr(player.pos, selected.pos) > (selected.radius + 250)**2:
                draw_text_centered("TOO FAR TO SCAN", bottom_screen, font_size, GREEN)
            else:
                if not selected.scanned:
                    # SCAN
                    self.scan_percent += 0.005

                    bottom_center = Vector2(bottom_screen.x + bottom_screen.width/2, bottom_screen.y + bottom_screen.height/2)
                    radius = min(bottom_screen.width/4, bottom_screen.height/4)

                    # scanning bar has a notch at the top 
                    # angles are in degrees
                    rl.draw_ring(bottom_center, radius-5, radius+5, -70, -70 + self.scan_percent*320, 24, Color(0x39, 0xa2, 0xd2, 0xff))
                    rl.draw_ring_lines(bottom_center, radius-5, radius+5, -70, 250, 24, WHITE)

                    if self.scan_percent >= 1.0:
                        self.scan_percent = 0.0
                        selected.scanned = True
