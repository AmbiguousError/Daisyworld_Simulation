import pygame
import random
import math

# --- Pygame Setup ---
pygame.init()
pygame.font.init()

# Screen dimensions
WIDTH, HEIGHT = 1200, 800
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Daisyworld Simulation")

# Colors
COLOR_BLACK = (0, 0, 0)
COLOR_WHITE = (255, 255, 255)
COLOR_GREY = (180, 180, 180)
COLOR_SKY_BLUE = (135, 206, 235)
COLOR_PANEL_BG = (20, 30, 40)
COLOR_DAISY_BLACK_PIXEL = (50, 50, 50) # Color for the daisy on the surface
COLOR_DAISY_WHITE_PIXEL = (240, 240, 240) # Color for the daisy on the surface
COLOR_GROUND = (150, 120, 90)
COLOR_TEXT_HIGHLIGHT = (255, 215, 0) # Gold for highlights
COLOR_BUTTON_BG = (80, 90, 100)
COLOR_BUTTON_TEXT = (255, 255, 255)

# --- Graph & Label Colors for visibility ---
COLOR_GRAPH_TEMP = (255, 80, 80) # Bright Red
COLOR_GRAPH_WHITE = (240, 240, 240) # Bright White
COLOR_GRAPH_BLACK = (160, 160, 160) # Medium Grey

# Fonts
FONT_TITLE = pygame.font.SysFont('sans', 30)
FONT_LARGE_TITLE = pygame.font.SysFont('sans', 50)
FONT_LABEL = pygame.font.SysFont('sans', 18)
FONT_VALUE = pygame.font.SysFont('monospace', 20)
FONT_FORMULA = pygame.font.SysFont('monospace', 16)
FONT_START_TEXT = pygame.font.SysFont('sans', 22)
FONT_START_HEADER = pygame.font.SysFont('sans', 28, bold=True)


# --- Daisyworld Model Parameters ---
class Daisyworld:
    def __init__(self):
        """Initializes the Daisyworld model with its default parameters."""
        self.reset()

    def reset(self):
        """Resets the simulation to its initial state."""
        self.albedo_white = 0.75
        self.albedo_black = 0.25
        self.albedo_ground = 0.5
        self.frac_white = 0.01
        self.frac_black = 0.01
        self.frac_ground = 1 - (self.frac_white + self.frac_black)
        self.solar_luminosity = 0.8
        self.max_luminosity = 1.6
        self.stefan_boltzmann = 5.67e-8
        self.planetary_temp = 0
        self.heating_effect_factor = 20
        self.death_rate = 0.3
        self.opt_temp = 22.5
        self.min_temp = 5.0
        self.max_temp = 40.0
        self.time_step = 0.1
        self.time = 0
        self.history = {'time': [], 'temp': [], 'white': [], 'black': [], 'luminosity': []}
        self.is_extinct = False # New flag for auto-stop

    def get_planetary_albedo(self):
        """Calculates the weighted average albedo of the planet."""
        return (self.frac_white * self.albedo_white +
                self.frac_black * self.albedo_black +
                self.frac_ground * self.albedo_ground)

    def get_planetary_temp(self, albedo):
        """Calculates the planet's effective temperature using the Stefan-Boltzmann law."""
        solar_flux = 917
        absorbed_flux = self.solar_luminosity * solar_flux * (1 - albedo)
        temp_kelvin = (absorbed_flux / self.stefan_boltzmann) ** 0.25
        return temp_kelvin - 273.15

    def get_local_temp(self, planetary_temp, planetary_albedo, daisy_albedo):
        """Calculates the local temperature of a daisy patch based on albedo difference."""
        return planetary_temp + self.heating_effect_factor * (planetary_albedo - daisy_albedo)

    def get_growth_rate(self, temp):
        """Calculates daisy growth rate based on a parabolic temperature function."""
        if self.min_temp < temp < self.max_temp:
            return 1.0 - 0.003265 * ((self.opt_temp - temp) ** 2)
        return 0

    def step(self):
        """Performs one step of the simulation."""
        if self.solar_luminosity < self.max_luminosity:
             self.solar_luminosity += 0.0005

        planetary_albedo = self.get_planetary_albedo()
        self.planetary_temp = self.get_planetary_temp(planetary_albedo)
        temp_white = self.get_local_temp(self.planetary_temp, planetary_albedo, self.albedo_white)
        temp_black = self.get_local_temp(self.planetary_temp, planetary_albedo, self.albedo_black)

        beta_white = self.get_growth_rate(temp_white)
        beta_black = self.get_growth_rate(temp_black)

        change_white = self.frac_white * (self.frac_ground * beta_white - self.death_rate)
        change_black = self.frac_black * (self.frac_ground * beta_black - self.death_rate)

        self.frac_white += change_white * self.time_step
        self.frac_black += change_black * self.time_step
        self.frac_white = max(0.0001, min(1, self.frac_white))
        self.frac_black = max(0.0001, min(1, self.frac_black))

        self.frac_ground = 1 - (self.frac_white + self.frac_black)
        if self.frac_ground < 0:
            self.frac_ground = 0
            total_daisies = self.frac_white + self.frac_black
            if total_daisies > 1:
                self.frac_white /= total_daisies
                self.frac_black /= total_daisies
        
        self.time += 1
        self.history['time'].append(self.time)
        self.history['temp'].append(self.planetary_temp)
        self.history['white'].append(self.frac_white * 100)
        self.history['black'].append(self.frac_black * 100)
        self.history['luminosity'].append(self.solar_luminosity)
        
        # --- Auto-stop condition ---
        # Check for extinction after an initial period has passed
        if self.time > 500 and (self.frac_white + self.frac_black) < 0.01:
            self.is_extinct = True


# --- Pygame Drawing Functions ---

def render_text_wrapped(surface, text, font, color, rect, line_spacing=1.2):
    """Renders text with word wrapping to fit inside a rect."""
    lines = []
    words = text.split(' ')
    current_line = ""
    for word in words:
        test_line = current_line + word + " "
        if font.size(test_line)[0] < rect.width:
            current_line = test_line
        else:
            lines.append(current_line)
            current_line = word + " "
    lines.append(current_line)

    y = rect.top
    for line in lines:
        text_surface = font.render(line, True, color)
        surface.blit(text_surface, (rect.left, y))
        y += font.get_linesize() * line_spacing
    return y

def draw_start_screen():
    """Draws the introductory screen."""
    screen.fill(COLOR_PANEL_BG)
    y_pos = 50
    title_surf = FONT_LARGE_TITLE.render("Welcome to Daisyworld", True, COLOR_WHITE)
    screen.blit(title_surf, (WIDTH // 2 - title_surf.get_width() // 2, y_pos))
    y_pos += 80
    col_width = (WIDTH - 150) // 2
    col1_rect = pygame.Rect(50, y_pos, col_width, HEIGHT - y_pos)
    col2_rect = pygame.Rect(WIDTH // 2 + 25, y_pos, col_width, HEIGHT - y_pos)
    header1_surf = FONT_START_HEADER.render("The Goal", True, COLOR_SKY_BLUE)
    screen.blit(header1_surf, (col1_rect.left, col1_rect.top))
    goal_text = "To demonstrate the Gaia Hypothesis: the idea that life can collectively self-regulate its environment to keep it habitable, without any conscious planning."
    text_rect = pygame.Rect(col1_rect.left, col1_rect.top + 40, col1_rect.width, 200)
    y_pos = render_text_wrapped(screen, goal_text, FONT_START_TEXT, COLOR_GREY, text_rect)
    header2_surf = FONT_START_HEADER.render("The Setup", True, COLOR_SKY_BLUE)
    screen.blit(header2_surf, (col1_rect.left, y_pos))
    y_pos += 40
    setup_text = [("Black Daisies:", "Absorb sunlight, warming the planet."), ("White Daisies:", "Reflect sunlight, cooling the planet."), ("The Sun:", "Its energy (Luminosity) will slowly increase.")]
    for header, desc in setup_text:
        header_surf = FONT_START_TEXT.render(header, True, COLOR_WHITE)
        screen.blit(header_surf, (col1_rect.left, y_pos))
        desc_surf = FONT_START_TEXT.render(desc, True, COLOR_GREY)
        screen.blit(desc_surf, (col1_rect.left + 160, y_pos))
        y_pos += 35
    header3_surf = FONT_START_HEADER.render("The Rules", True, COLOR_SKY_BLUE)
    screen.blit(header3_surf, (col2_rect.left, col2_rect.top))
    rules_text = "Daisies grow best at 22.5°C. Their growth rate is defined by a parabola, and they cannot survive if it gets too hot or too cold."
    text_rect = pygame.Rect(col2_rect.left, col2_rect.top + 40, col2_rect.width, 200)
    y_pos2 = render_text_wrapped(screen, rules_text, FONT_START_TEXT, COLOR_GREY, text_rect)
    header4_surf = FONT_START_HEADER.render("Controls", True, COLOR_SKY_BLUE)
    screen.blit(header4_surf, (col2_rect.left, y_pos2))
    y_pos2 += 40
    controls_text = [("Spacebar:", "Pause / Resume simulation."), ("R Key:", "Restart simulation.")]
    for key, action in controls_text:
        key_surf = FONT_START_TEXT.render(key, True, COLOR_WHITE)
        screen.blit(key_surf, (col2_rect.left, y_pos2))
        action_surf = FONT_START_TEXT.render(action, True, COLOR_GREY)
        screen.blit(action_surf, (col2_rect.left + 120, y_pos2))
        y_pos2 += 35
    start_instr = FONT_TITLE.render("Press ENTER to Begin Simulation", True, COLOR_TEXT_HIGHLIGHT)
    screen.blit(start_instr, (WIDTH // 2 - start_instr.get_width() // 2, HEIGHT - 100))

def draw_end_screen():
    """Draws the experiment conclusion screen."""
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((20, 30, 40, 230))
    screen.blit(overlay, (0, 0))

    y_pos = 100
    title_surf = FONT_LARGE_TITLE.render("Experiment Complete: Heat Death", True, COLOR_GRAPH_TEMP)
    screen.blit(title_surf, (WIDTH // 2 - title_surf.get_width() // 2, y_pos))
    y_pos += 100

    col_width = (WIDTH - 200)
    col_rect = pygame.Rect(100, y_pos, col_width, HEIGHT - y_pos)

    header_surf = FONT_START_HEADER.render("Summary of Results", True, COLOR_SKY_BLUE)
    screen.blit(header_surf, (col_rect.left, col_rect.top))
    
    results = [
        ("1. Warming Phase:", "The sun was cool, so heat-absorbing black daisies thrived, warming the planet to a habitable temperature."),
        ("2. Homeostasis (Regulation):", "As the sun grew hotter, reflective white daisies emerged. For a long time, the two populations balanced each other to keep the planet's temperature stable, despite the rising solar energy. This is the Gaia effect."),
        ("3. Extinction:", "Eventually, the sun became too hot for even the white daisies to handle. The temperature soared past their survival limit, causing a total collapse of all life.")
    ]
    
    y_pos = col_rect.top + 50
    for header, desc in results:
        # Draw header
        header_surf = FONT_START_TEXT.render(header, True, COLOR_WHITE)
        screen.blit(header_surf, (col_rect.left, y_pos))
        y_pos += header_surf.get_height() + 5 # Move y down for the description

        # Draw description text below the header
        text_rect = pygame.Rect(col_rect.left, y_pos, col_rect.width, 200)
        y_pos = render_text_wrapped(screen, desc, FONT_START_TEXT, COLOR_GREY, text_rect, 1.1)
        y_pos += 25 # Add extra space between items

    restart_instr = FONT_TITLE.render("Press 'R' to Restart the Experiment", True, COLOR_TEXT_HIGHLIGHT)
    screen.blit(restart_instr, (WIDTH // 2 - restart_instr.get_width() // 2, HEIGHT - 100))

def draw_daisyworld_surface(surface, world, rect):
    """Draws a visual representation of the planet surface."""
    num_pixels = int(rect.width * rect.height)
    num_white = int(num_pixels * world.frac_white)
    num_black = int(num_pixels * world.frac_black)
    pixel_colors = [COLOR_DAISY_WHITE_PIXEL] * num_white + [COLOR_DAISY_BLACK_PIXEL] * num_black + [COLOR_GROUND] * (num_pixels - num_white - num_black)
    random.shuffle(pixel_colors)
    pixel_index = 0
    for y in range(rect.height):
        for x in range(rect.width):
            if pixel_index < num_pixels:
                surface.set_at((x, y), pixel_colors[pixel_index])
                pixel_index += 1
    screen.blit(surface, rect.topleft)
    pygame.draw.rect(screen, COLOR_WHITE, rect, 2)

def draw_graph(world, rect):
    """Draws the graph of temperature and daisy populations over time."""
    pygame.draw.rect(screen, COLOR_PANEL_BG, rect)
    pygame.draw.rect(screen, COLOR_WHITE, rect, 2)
    history = world.history
    if len(history['time']) < 2: return
    def scale(val, val_min, val_max, rect_min, rect_max):
        if (val_max - val_min) == 0: return rect_min
        return rect_min + (rect_max - rect_min) * (val - val_min) / (val_max - val_min)
    max_time = max(1, max(history['time']))
    min_temp, max_temp = -10, 80
    min_pop, max_pop = 0, 100
    points_temp, points_white, points_black = [], [], []
    for i in range(len(history['time'])):
        x = scale(history['time'][i], 0, max_time, rect.left, rect.right)
        y_temp = scale(history['temp'][i], min_temp, max_temp, rect.bottom, rect.top)
        y_white = scale(history['white'][i], min_pop, max_pop, rect.bottom, rect.top)
        y_black = scale(history['black'][i], min_pop, max_pop, rect.bottom, rect.top)
        points_temp.append((x, y_temp))
        points_white.append((x, y_white))
        points_black.append((x, y_black))
    pygame.draw.lines(screen, COLOR_GRAPH_TEMP, False, points_temp, 2)
    pygame.draw.lines(screen, COLOR_GRAPH_WHITE, False, points_white, 2)
    pygame.draw.lines(screen, COLOR_GRAPH_BLACK, False, points_black, 2)
    legend_items = [("Temp", COLOR_GRAPH_TEMP), ("White Daisies", COLOR_GRAPH_WHITE), ("Black Daisies", COLOR_GRAPH_BLACK)]
    lx, ly = rect.right - 140, rect.top + 15
    for name, color in legend_items:
        pygame.draw.rect(screen, color, (lx, ly, 20, 10))
        label_surf = FONT_LABEL.render(name, True, COLOR_WHITE)
        screen.blit(label_surf, (lx + 25, ly - 3))
        ly += 20

def draw_info_panel(world, rect):
    """Draws the panel with current data and formulas."""
    pygame.draw.rect(screen, COLOR_PANEL_BG, rect)
    pygame.draw.rect(screen, COLOR_WHITE, rect, 2)
    y_pos = rect.top + 15
    def draw_line(label, value, unit, color=COLOR_WHITE):
        nonlocal y_pos
        label_surf = FONT_LABEL.render(label, True, COLOR_GREY)
        value_surf = FONT_VALUE.render(f"{value:>7.2f} {unit}", True, color)
        screen.blit(label_surf, (rect.left + 15, y_pos))
        screen.blit(value_surf, (rect.left + 200, y_pos))
        y_pos += 25
    title = FONT_TITLE.render("Daisyworld State", True, COLOR_WHITE)
    screen.blit(title, (rect.centerx - title.get_width() // 2, y_pos))
    y_pos += 45
    draw_line("Time...........:", world.time, "steps")
    draw_line("Solar Luminosity.:", world.solar_luminosity, " (factor)", COLOR_SKY_BLUE)
    draw_line("Planetary Albedo.:", world.get_planetary_albedo(), "")
    draw_line("Planetary Temp...:", world.planetary_temp, "C", COLOR_GRAPH_TEMP)
    y_pos += 10
    draw_line("White Daisy Pop..:", world.frac_white * 100, "%", COLOR_GRAPH_WHITE)
    draw_line("Black Daisy Pop..:", world.frac_black * 100, "%", COLOR_GRAPH_BLACK)
    draw_line("Bare Ground......:", world.frac_ground * 100, "%", COLOR_GROUND)
    y_pos += 40
    formula_title = FONT_TITLE.render("Core Formulas", True, COLOR_WHITE)
    screen.blit(formula_title, (rect.centerx - formula_title.get_width() // 2, y_pos))
    y_pos += 40
    formulas = ["Temp ~ (Luminosity * (1 - Albedo))^0.25", "Albedo = sum(Frac_i * Albedo_i)", "Growth = 1 - k * (T_optimal - T_local)^2", "d(Frac)/dt = Frac * (Growth - Death)"]
    for f in formulas:
        formula_surf = FONT_FORMULA.render(f, True, COLOR_GREY)
        screen.blit(formula_surf, (rect.left + 15, y_pos))
        y_pos += 20

def draw_buttons(rect, paused):
    """Draws the UI buttons."""
    restart_rect = pygame.Rect(rect.left + 20, rect.top, 120, 40)
    pause_rect = pygame.Rect(rect.left + 160, rect.top, 120, 40)
    pygame.draw.rect(screen, COLOR_BUTTON_BG, restart_rect, border_radius=5)
    restart_text = FONT_LABEL.render("Restart (R)", True, COLOR_BUTTON_TEXT)
    screen.blit(restart_text, (restart_rect.centerx - restart_text.get_width() // 2, restart_rect.centery - restart_text.get_height() // 2))
    pause_text_str = "Resume (Spc)" if paused else "Pause (Spc)"
    pygame.draw.rect(screen, COLOR_BUTTON_BG, pause_rect, border_radius=5)
    pause_text = FONT_LABEL.render(pause_text_str, True, COLOR_BUTTON_TEXT)
    screen.blit(pause_text, (pause_rect.centerx - pause_text.get_width() // 2, pause_rect.centery - pause_text.get_height() // 2))
    return restart_rect, pause_rect

# --- Main Game Loop ---
def main():
    clock = pygame.time.Clock()
    running = True
    paused = False
    game_state = 'start_screen'
    world = Daisyworld()
    world_rect = pygame.Rect(20, 20, 750, 400)
    graph_rect = pygame.Rect(20, 440, 750, 340)
    info_rect = pygame.Rect(790, 20, 390, 760)
    button_rect = pygame.Rect(info_rect.left, info_rect.bottom - 60, info_rect.width, 50)
    world_surface = pygame.Surface((world_rect.width, world_rect.height))

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if game_state == 'start_screen' and event.key == pygame.K_RETURN:
                    game_state = 'simulation'
                elif game_state == 'simulation':
                    if event.key == pygame.K_SPACE: paused = not paused
                    if event.key == pygame.K_r:
                        world.reset()
                        paused = False
                elif game_state == 'end_screen':
                    if event.key == pygame.K_r:
                        world.reset()
                        game_state = 'simulation'
            if event.type == pygame.MOUSEBUTTONDOWN and game_state == 'simulation':
                if event.button == 1:
                    restart_btn, pause_btn = draw_buttons(button_rect, paused)
                    if restart_btn.collidepoint(event.pos):
                        world.reset()
                        paused = False
                    if pause_btn.collidepoint(event.pos):
                        paused = not paused

        if game_state == 'start_screen':
            draw_start_screen()
        elif game_state == 'simulation':
            if not paused:
                world.step()
                if world.is_extinct:
                    game_state = 'end_screen'
            screen.fill(COLOR_BLACK)
            draw_daisyworld_surface(world_surface, world, world_surface.get_rect())
            draw_graph(world, graph_rect)
            draw_info_panel(world, info_rect)
            draw_buttons(button_rect, paused)
        elif game_state == 'end_screen':
            # Keep the final state drawn, then overlay the end screen
            draw_end_screen()

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

if __name__ == '__main__':
    main()
