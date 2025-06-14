import pygame
import random
import math
import copy
import asyncio # Essential for web hosting

# --- PyScript & Gemini API Integration ---
try:
    from pyscript import display
    import pyodide.http
    # Make a request to the Gemini API
    async def call_gemini_api(prompt):
        api_key = "" # Leave blank when using the built-in proxy
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
        
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        
        try:
            response = await pyodide.http.pyfetch(
                url,
                method='POST',
                headers={'Content-Type': 'application/json'},
                body=str(payload).replace("'", '"') # Convert payload to JSON string
            )
            data = await response.json()
            if data and 'candidates' in data and data['candidates']:
                return data['candidates'][0]['content']['parts'][0]['text']
            else:
                return "Error: Could not parse response from Gemini API."
        except Exception as e:
            return f"An error occurred: {e}"
except ImportError:
    # Define dummy functions for desktop use
    def display(value, target=None, append=True):
        pass
    async def call_gemini_api(prompt):
        print("Gemini API call (mocked for desktop):", prompt)
        await asyncio.sleep(2)
        return "This is a mocked response for desktop testing. The AI analysis feature only works when run in the browser."
# --- End Integration ---


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
COLOR_DAISY_BLACK_PIXEL = (50, 50, 50)
COLOR_DAISY_WHITE_PIXEL = (240, 240, 240)
COLOR_GROUND = (150, 120, 90)
COLOR_TEXT_HIGHLIGHT = (255, 215, 0)
COLOR_BUTTON_BG = (80, 90, 100)
COLOR_BUTTON_TEXT = (255, 255, 255)

# --- Graph & Label Colors for visibility ---
COLOR_GRAPH_TEMP = (255, 80, 80)
COLOR_GRAPH_WHITE = (240, 240, 240)
COLOR_GRAPH_BLACK = (160, 160, 160)

# Fonts
FONT_TITLE = pygame.font.SysFont('sans', 30)
FONT_LARGE_TITLE = pygame.font.SysFont('sans', 50)
FONT_LABEL = pygame.font.SysFont('sans', 18)
FONT_VALUE = pygame.font.SysFont('monospace', 20)
FONT_FORMULA = pygame.font.SysFont('monospace', 16)
FONT_SETTINGS_TEXT = pygame.font.SysFont('sans', 22)
FONT_SETTINGS_HEADER = pygame.font.SysFont('sans', 28, bold=True)
FONT_SETTINGS_DESC = pygame.font.SysFont('sans', 16)


# --- Default Settings ---
DEFAULT_SETTINGS = {
    'albedo_white':      {'value': 0.75, 'min': 0.5, 'max': 1.0, 'step': 0.05, 'format': '{:.2f}', 'desc': "Reflectivity of white daisies (higher is more reflective)."},
    'albedo_black':      {'value': 0.25, 'min': 0.0, 'max': 0.5, 'step': 0.05, 'format': '{:.2f}', 'desc': "Reflectivity of black daisies (lower is more absorbent)."},
    'albedo_ground':     {'value': 0.50, 'min': 0.0, 'max': 1.0, 'step': 0.05, 'format': '{:.2f}', 'desc': "Reflectivity of the bare ground."},
    'death_rate':        {'value': 0.30, 'min': 0.1, 'max': 1.0, 'step': 0.05, 'format': '{:.2f}', 'desc': "Natural death rate of daisies. Higher is less stable."},
    'start_luminosity':  {'value': 0.80, 'min': 0.4, 'max': 1.4, 'step': 0.05, 'format': '{:.2f}', 'desc': "The initial energy output of the sun."},
    'luminosity_change': {'value': 0.0005, 'min': 0.0, 'max': 0.002, 'step': 0.0001, 'format': '{:.4f}', 'desc': "Rate of solar warming. Set to 0 for a constant sun."},
    'heating_effect':    {'value': 20,   'min': 0,   'max': 50,  'step': 2,    'format': '{:d}', 'desc': "How much a daisy's color affects its local temperature."},
    'stability_turns':   {'value': 5,  'min': 5,  'max': 500,'step': 5,   'format': '{:d}', 'desc': "Turns of no change before ending due to stability."},
}
current_settings = copy.deepcopy(DEFAULT_SETTINGS)

# --- Daisyworld Model Parameters ---
class Daisyworld:
    def __init__(self):
        self.history = {}
        self.time = 0
        self.reset(current_settings)

    def reset(self, settings):
        self.albedo_white = settings['albedo_white']['value']
        self.albedo_black = settings['albedo_black']['value']
        self.albedo_ground = settings['albedo_ground']['value']
        self.death_rate = settings['death_rate']['value']
        self.solar_luminosity = settings['start_luminosity']['value']
        self.luminosity_change_rate = settings['luminosity_change']['value']
        self.heating_effect_factor = settings['heating_effect']['value']
        self.stability_check_turns = settings['stability_turns']['value']
        self.frac_white = 0.01
        self.frac_black = 0.01
        self.frac_ground = 1 - (self.frac_white + self.frac_black)
        self.max_luminosity = 1.8
        self.stefan_boltzmann = 5.67e-8
        self.planetary_temp = 0
        self.opt_temp = 22.5
        self.min_temp = 5.0
        self.max_temp = 40.0
        self.time_step = 0.1
        self.time = 0
        self.history = {'time': [], 'temp': [], 'white': [], 'black': []}
        self.end_reason = None
        self.white_pop_history = []
        self.black_pop_history = []

    def get_planetary_albedo(self):
        return (self.frac_white * self.albedo_white + self.frac_black * self.albedo_black + self.frac_ground * self.albedo_ground)

    def get_planetary_temp(self, albedo):
        solar_flux = 917
        absorbed_flux = self.solar_luminosity * solar_flux * (1 - albedo)
        temp_kelvin = (absorbed_flux / self.stefan_boltzmann) ** 0.25
        return temp_kelvin - 273.15

    def get_local_temp(self, planetary_temp, planetary_albedo, daisy_albedo):
        return planetary_temp + self.heating_effect_factor * (planetary_albedo - daisy_albedo)

    def get_growth_rate(self, temp):
        if self.min_temp < temp < self.max_temp:
            return 1.0 - 0.003265 * ((self.opt_temp - temp) ** 2)
        return 0

    def step(self):
        if self.solar_luminosity < self.max_luminosity:
            self.solar_luminosity += self.luminosity_change_rate
        planetary_albedo = self.get_planetary_albedo()
        self.planetary_temp = self.get_planetary_temp(planetary_albedo)
        temp_white = self.get_local_temp(self.planetary_temp, planetary_albedo, self.albedo_white)
        temp_black = self.get_local_temp(self.planetary_temp, planetary_albedo, self.albedo_black)
        beta_white = self.get_growth_rate(temp_white)
        beta_black = self.get_growth_rate(temp_black)
        change_white = self.frac_white * (self.frac_ground * beta_white - self.death_rate)
        change_black = self.frac_black * (self.frac_ground * beta_black - self.death_rate)
        self.frac_white = max(0.0001, min(1, self.frac_white + change_white * self.time_step))
        self.frac_black = max(0.0001, min(1, self.frac_black + change_black * self.time_step))
        self.frac_ground = max(0, 1 - (self.frac_white + self.frac_black))
        if self.frac_ground == 0:
            total_daisies = self.frac_white + self.frac_black
            if total_daisies > 1:
                self.frac_white /= total_daisies
                self.frac_black /= total_daisies
        self.time += 1
        self.history['time'].append(self.time)
        self.history['temp'].append(self.planetary_temp)
        self.history['white'].append(self.frac_white * 100)
        self.history['black'].append(self.frac_black * 100)
        
        if self.time > 500 and (self.frac_white + self.frac_black) < 0.01:
            self.end_reason = 'extinct'
        
        self.white_pop_history.append(self.frac_white)
        self.black_pop_history.append(self.frac_black)
        if len(self.white_pop_history) > self.stability_check_turns:
            self.white_pop_history.pop(0)
            self.black_pop_history.pop(0)

        if len(self.white_pop_history) == self.stability_check_turns:
            white_delta = max(self.white_pop_history) - min(self.white_pop_history)
            black_delta = max(self.black_pop_history) - min(self.black_pop_history)
            stability_threshold = 0.0001
            if white_delta < stability_threshold and black_delta < stability_threshold and (self.frac_white + self.frac_black) > 0.01:
                 self.end_reason = 'stable'

# --- UI & Drawing Functions ---
def render_text_wrapped(surface, text, font, color, rect, line_spacing=1.2):
    lines = []
    words = text.split(' ')
    current_line = ""
    for word in words:
        test_line = f"{current_line}{word} "
        if font.size(test_line)[0] < rect.width:
            current_line = test_line
        else:
            lines.append(current_line)
            current_line = f"{word} "
    lines.append(current_line)
    y = rect.top
    for line in lines:
        text_surface = font.render(line, True, color)
        surface.blit(text_surface, (rect.left, y))
        y += font.get_linesize() * line_spacing
    return y

def draw_settings_screen(settings):
    screen.fill(COLOR_PANEL_BG)
    y_pos = 20
    title_surf = FONT_LARGE_TITLE.render("Daisyworld Simulation", True, COLOR_WHITE)
    screen.blit(title_surf, (WIDTH // 2 - title_surf.get_width() // 2, y_pos)); y_pos += 70
    buttons = {}
    left_col_rect = pygame.Rect(50, y_pos, WIDTH // 2 - 75, HEIGHT - y_pos)
    right_col_rect = pygame.Rect(WIDTH // 2 - 25, y_pos, WIDTH // 2 - 25, HEIGHT - y_pos)
    y_pos_left = left_col_rect.top
    header1_surf = FONT_SETTINGS_HEADER.render("The Experiment", True, COLOR_SKY_BLUE)
    screen.blit(header1_surf, (left_col_rect.left, y_pos_left)); y_pos_left += 40
    goal_text = "Daisyworld demonstrates the Gaia Hypothesis: the idea that life can collectively self-regulate its environment to keep it habitable, without any conscious planning."
    text_rect = pygame.Rect(left_col_rect.left, y_pos_left, left_col_rect.width, 200)
    y_pos_left = render_text_wrapped(screen, goal_text, FONT_SETTINGS_TEXT, COLOR_GREY, text_rect); y_pos_left += 20
    header2_surf = FONT_SETTINGS_HEADER.render("Core Formulas", True, COLOR_SKY_BLUE)
    screen.blit(header2_surf, (left_col_rect.left, y_pos_left)); y_pos_left += 40
    formulas = ["Temp ~ (Luminosity * (1-Albedo))^0.25", "Albedo = sum(Frac_i * Albedo_i)", "Growth = 1-k*(T_opt-T_local)^2", "d(Frac)/dt = Frac*(Growth-Death)"]
    for f in formulas:
        formula_surf = FONT_FORMULA.render(f, True, COLOR_GREY)
        screen.blit(formula_surf, (left_col_rect.left + 20, y_pos_left)); y_pos_left += 25
    y_pos_right = right_col_rect.top
    header3_surf = FONT_SETTINGS_HEADER.render("Settings", True, COLOR_SKY_BLUE)
    screen.blit(header3_surf, (right_col_rect.left, y_pos_right)); y_pos_right += 40
    for i, (key, params) in enumerate(settings.items()):
        name = key.replace('_', ' ').title()
        label_surf = FONT_SETTINGS_TEXT.render(name, True, COLOR_WHITE)
        screen.blit(label_surf, (right_col_rect.left, y_pos_right))
        desc_surf = FONT_SETTINGS_DESC.render(params['desc'], True, COLOR_GREY)
        screen.blit(desc_surf, (right_col_rect.left, y_pos_right + 25))
        value_str = params['format'].format(params['value'])
        value_surf = FONT_SETTINGS_TEXT.render(value_str, True, COLOR_WHITE)
        screen.blit(value_surf, (right_col_rect.right - 180, y_pos_right))
        minus_btn_rect = pygame.Rect(right_col_rect.right - 90, y_pos_right, 40, 30); plus_btn_rect = pygame.Rect(right_col_rect.right - 45, y_pos_right, 40, 30)
        pygame.draw.rect(screen, COLOR_BUTTON_BG, minus_btn_rect, border_radius=5); pygame.draw.rect(screen, COLOR_BUTTON_BG, plus_btn_rect, border_radius=5)
        minus_text = FONT_TITLE.render("-", True, COLOR_WHITE); plus_text = FONT_TITLE.render("+", True, COLOR_WHITE)
        screen.blit(minus_text, (minus_btn_rect.centerx - minus_text.get_width()//2, minus_btn_rect.centery - minus_text.get_height()//2 - 2))
        screen.blit(plus_text, (plus_btn_rect.centerx - plus_text.get_width()//2, plus_btn_rect.centery - plus_text.get_height()//2 - 2))
        buttons[f'{key}_minus'] = minus_btn_rect; buttons[f'{key}_plus'] = plus_btn_rect
        y_pos_right += 60
    y_pos = y_pos_right + 20
    default_btn_rect = pygame.Rect(WIDTH//2 - 100, y_pos, 250, 50); start_btn_rect = pygame.Rect(WIDTH//2 + 170, y_pos, 250, 50)
    pygame.draw.rect(screen, COLOR_BUTTON_BG, default_btn_rect, border_radius=5)
    default_text = FONT_TITLE.render("Load Defaults", True, COLOR_WHITE)
    screen.blit(default_text, (default_btn_rect.centerx - default_text.get_width()//2, default_btn_rect.centery - default_text.get_height()//2))
    pygame.draw.rect(screen, COLOR_SKY_BLUE, start_btn_rect, border_radius=5)
    start_text = FONT_TITLE.render("Start Simulation", True, COLOR_BLACK)
    screen.blit(start_text, (start_btn_rect.centerx - start_text.get_width()//2, start_btn_rect.centery - start_text.get_height()//2))
    buttons['defaults'] = default_btn_rect; buttons['start'] = start_btn_rect
    return buttons

def draw_end_screen(world):
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA); overlay.fill((20, 30, 40, 240)); screen.blit(overlay, (0, 0))
    final_temp = world.history['temp'][-1]
    max_white_pop = max(world.history['white']) if world.history['white'] else 0
    max_black_pop = max(world.history['black']) if world.history['black'] else 0
    title_text, summary_text, color = "Experiment Complete", COLOR_WHITE, []
    if world.end_reason == 'stable':
        title_text = "Stable Equilibrium Reached"; color = (100, 255, 100)
        summary_text = [("Observation:", "The simulation ended because the daisy populations and temperature remained constant for the specified number of turns."),("Analysis:", "The conditions you set allowed the daisy populations to find a balance. They successfully regulated the planet's temperature, keeping it within a habitable range and demonstrating a robust Gaian system.")]
    elif max_white_pop < 2 and max_black_pop < 2:
        title_text = "Extinction: Failure to Launch"; color = COLOR_GREY
        summary_text = [("Initial Conditions:", "The parameters you set were too harsh for either daisy species to establish a foothold."),("Result:", "With no life to regulate the environment, the planet's temperature was solely determined by physical factors, resulting in a barren world.")]
    elif final_temp > world.max_temp:
        title_text = "Extinction: Heat Death"; color = COLOR_GRAPH_TEMP
        summary_text = [("Warming Phase:", "Initially, black daisies may have warmed the planet."),("Homeostasis:", "For a period, the daisies likely regulated the temperature. However, external pressure or internal factors made this unsustainable."),("Final Result:", "The environment eventually overwhelmed the daisies' regulatory capacity, causing the temperature to soar past their survival limit and leading to a total collapse of life.")]
    elif final_temp < world.min_temp:
        title_text = "Extinction: Freeze Death"; color = COLOR_SKY_BLUE
        summary_text = [("Warming attempt:", "Black daisies attempted to warm the planet, but the sun's luminosity was too low or their heating effect was too weak to overcome the cold."),("Result:", "The planet never reached the optimal temperature for sustained growth. The populations dwindled and life froze.")]
    y_pos = 50
    title_surf = FONT_LARGE_TITLE.render(title_text, True, color)
    screen.blit(title_surf, (WIDTH // 2 - title_surf.get_width() // 2, y_pos)); y_pos += 80
    left_col_rect = pygame.Rect(50, y_pos, WIDTH // 2 - 75, HEIGHT - y_pos - 100); right_col_rect = pygame.Rect(WIDTH // 2 + 25, y_pos, WIDTH // 2 - 75, HEIGHT - y_pos - 100)
    y_pos_left = left_col_rect.top
    header1_surf = FONT_SETTINGS_HEADER.render("Summary of Results", True, COLOR_SKY_BLUE)
    screen.blit(header1_surf, (left_col_rect.left, y_pos_left)); y_pos_left += 50
    for header, desc in summary_text:
        header_surf_sm = FONT_SETTINGS_TEXT.render(header, True, COLOR_WHITE)
        screen.blit(header_surf_sm, (left_col_rect.left, y_pos_left)); y_pos_left += header_surf_sm.get_height() + 5
        text_rect = pygame.Rect(left_col_rect.left + 20, y_pos_left, left_col_rect.width - 20, 200)
        y_pos_left = render_text_wrapped(screen, desc, FONT_SETTINGS_TEXT, COLOR_GREY, text_rect, 1.1); y_pos_left += 30
    y_pos_right = right_col_rect.top
    header2_surf = FONT_SETTINGS_HEADER.render("Final State", True, COLOR_SKY_BLUE)
    screen.blit(header2_surf, (right_col_rect.left, y_pos_right)); y_pos_right += 50
    def draw_final_line(label, value, unit, color=COLOR_WHITE):
        nonlocal y_pos_right
        label_surf = FONT_LABEL.render(label, True, COLOR_GREY); value_surf = FONT_VALUE.render(f"{value:>7.2f} {unit}", True, color)
        screen.blit(label_surf, (right_col_rect.left, y_pos_right)); screen.blit(value_surf, (right_col_rect.left + 250, y_pos_right)); y_pos_right += 35
    final_white_pop = world.history['white'][-1]; final_black_pop = world.history['black'][-1]; final_albedo = world.get_planetary_albedo()
    draw_final_line("Final Temperature:", final_temp, "C", COLOR_GRAPH_TEMP); draw_final_line("Final White Pop:", final_white_pop, "%", COLOR_GRAPH_WHITE); draw_final_line("Final Black Pop:", final_black_pop, "%", COLOR_GRAPH_BLACK); draw_final_line("Final Albedo:", final_albedo, ""); draw_final_line("Final Luminosity:", world.solar_luminosity, ""); draw_final_line("Total Time:", world.time, "steps")
    restart_instr = FONT_TITLE.render("Press 'R' to Return to Settings", True, COLOR_TEXT_HIGHLIGHT)
    screen.blit(restart_instr, (WIDTH // 2 - restart_instr.get_width() // 2, HEIGHT - 100))
    gemini_button_rect = pygame.Rect(WIDTH // 2 - 150, HEIGHT - 160, 300, 50)
    pygame.draw.rect(screen, COLOR_SKY_BLUE, gemini_button_rect, border_radius=5)
    gemini_text = FONT_TITLE.render("✨ Analyze with AI", True, COLOR_BLACK)
    screen.blit(gemini_text, (gemini_button_rect.centerx - gemini_text.get_width() // 2, gemini_button_rect.centery - gemini_text.get_height() // 2))
    return gemini_button_rect

def draw_analysis_modal(text):
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA); overlay.fill((10, 10, 15, 245)); screen.blit(overlay, (0, 0))
    modal_rect = pygame.Rect(100, 100, WIDTH - 200, HEIGHT - 200)
    pygame.draw.rect(screen, COLOR_PANEL_BG, modal_rect, border_radius=10); pygame.draw.rect(screen, COLOR_SKY_BLUE, modal_rect, 2, border_radius=10)
    y_pos = modal_rect.top + 30
    title_surf = FONT_SETTINGS_HEADER.render("AI Field Report", True, COLOR_SKY_BLUE)
    screen.blit(title_surf, (modal_rect.centerx - title_surf.get_width()//2, y_pos)); y_pos += 60
    text_area = pygame.Rect(modal_rect.left + 40, y_pos, modal_rect.width - 80, modal_rect.height - 150)
    render_text_wrapped(screen, text, FONT_SETTINGS_TEXT, COLOR_GREY, text_area)
    close_btn_rect = pygame.Rect(modal_rect.centerx - 75, modal_rect.bottom - 70, 150, 40)
    pygame.draw.rect(screen, COLOR_BUTTON_BG, close_btn_rect, border_radius=5)
    close_text = FONT_LABEL.render("Close", True, COLOR_BUTTON_TEXT)
    screen.blit(close_text, (close_btn_rect.centerx - close_text.get_width()//2, close_btn_rect.centery - close_text.get_height()//2))
    return close_btn_rect

def draw_daisyworld_surface(surface, world, rect):
    num_pixels = int(rect.width * rect.height); num_white = int(num_pixels * world.frac_white); num_black = int(num_pixels * world.frac_black)
    pixel_colors = [COLOR_DAISY_WHITE_PIXEL] * num_white + [COLOR_DAISY_BLACK_PIXEL] * num_black + [COLOR_GROUND] * (num_pixels - num_white - num_black)
    random.shuffle(pixel_colors)
    pixel_index = 0
    for y in range(rect.height):
        for x in range(rect.width):
            if pixel_index < num_pixels:
                surface.set_at((x, y), pixel_colors[pixel_index]); pixel_index += 1
    screen.blit(surface, rect.topleft); pygame.draw.rect(screen, COLOR_WHITE, rect, 2)

def draw_graph(world, rect):
    pygame.draw.rect(screen, COLOR_PANEL_BG, rect); pygame.draw.rect(screen, COLOR_WHITE, rect, 2)
    history = world.history
    if len(history['time']) < 2: return
    def scale(val, val_min, val_max, rect_min, rect_max):
        if (val_max - val_min) == 0: return rect_min
        return rect_min + (rect_max - rect_min) * (val - val_min) / (val_max - val_min)
    max_time = max(1, len(history['time']))
    points_temp, points_white, points_black = [], [], []
    for i in range(len(history['time'])):
        x = scale(i, 0, max_time -1, rect.left, rect.right)
        points_temp.append((x, scale(history['temp'][i], -10, 80, rect.bottom, rect.top)))
        points_white.append((x, scale(history['white'][i], 0, 100, rect.bottom, rect.top)))
        points_black.append((x, scale(history['black'][i], 0, 100, rect.bottom, rect.top)))
    pygame.draw.lines(screen, COLOR_GRAPH_TEMP, False, points_temp, 2); pygame.draw.lines(screen, COLOR_GRAPH_WHITE, False, points_white, 2); pygame.draw.lines(screen, COLOR_GRAPH_BLACK, False, points_black, 2)
    legend_items = [("Temp", COLOR_GRAPH_TEMP), ("White Daisies", COLOR_GRAPH_WHITE), ("Black Daisies", COLOR_GRAPH_BLACK)]
    lx, ly = rect.right - 140, rect.top + 15
    for name, color in legend_items:
        pygame.draw.rect(screen, color, (lx, ly, 20, 10)); label_surf = FONT_LABEL.render(name, True, COLOR_WHITE)
        screen.blit(label_surf, (lx + 25, ly - 3)); ly += 20

def draw_info_panel(world, rect):
    pygame.draw.rect(screen, COLOR_PANEL_BG, rect); pygame.draw.rect(screen, COLOR_WHITE, rect, 2)
    y_pos = rect.top + 15
    def draw_line(label, value, unit, color=COLOR_WHITE):
        nonlocal y_pos
        label_surf = FONT_LABEL.render(label, True, COLOR_GREY); value_surf = FONT_VALUE.render(f"{value:>7.2f} {unit}", True, color)
        screen.blit(label_surf, (rect.left + 15, y_pos)); screen.blit(value_surf, (rect.left + 200, y_pos)); y_pos += 25
    title = FONT_TITLE.render("Daisyworld State", True, COLOR_WHITE)
    screen.blit(title, (rect.centerx - title.get_width() // 2, y_pos)); y_pos += 45
    draw_line("Time...........:", world.time, "steps"); draw_line("Solar Luminosity.:", world.solar_luminosity, "", COLOR_SKY_BLUE); draw_line("Planetary Albedo.:", world.get_planetary_albedo(), ""); draw_line("Planetary Temp...:", world.planetary_temp, "C", COLOR_GRAPH_TEMP); y_pos += 10
    draw_line("White Daisy Pop..:", world.frac_white * 100, "%", COLOR_GRAPH_WHITE); draw_line("Black Daisy Pop..:", world.frac_black * 100, "%", COLOR_GRAPH_BLACK); draw_line("Bare Ground......:", world.frac_ground * 100, "%", COLOR_GROUND); y_pos += 40
    formula_title = FONT_TITLE.render("Core Formulas", True, COLOR_WHITE)
    screen.blit(formula_title, (rect.centerx - formula_title.get_width() // 2, y_pos)); y_pos += 40
    formulas = ["Temp ~ (Luminosity * (1-Albedo))^0.25", "Albedo = sum(Frac_i * Albedo_i)", "Growth = 1-k*(T_opt-T_local)^2", "d(Frac)/dt = Frac*(Growth-Death)"]
    for f in formulas:
        formula_surf = FONT_FORMULA.render(f, True, COLOR_GREY)
        screen.blit(formula_surf, (rect.left + 15, y_pos)); y_pos += 20

def draw_buttons(rect):
    back_btn_rect = pygame.Rect(rect.left + 20, rect.top, 150, 40)
    pygame.draw.rect(screen, COLOR_BUTTON_BG, back_btn_rect, border_radius=5)
    text = FONT_LABEL.render("Back to Settings", True, COLOR_BUTTON_TEXT)
    screen.blit(text, (back_btn_rect.centerx - text.get_width()//2, back_btn_rect.centery - text.get_height()//2))
    return back_btn_rect

# --- Main Game Loop ---
async def main():
    global current_settings
    running = True
    game_state = 'settings_screen'
    world = Daisyworld()
    world_rect = pygame.Rect(20, 20, 750, 400); graph_rect = pygame.Rect(20, 440, 750, 340); info_rect = pygame.Rect(790, 20, 390, 760); button_rect = pygame.Rect(info_rect.left, info_rect.bottom - 60, info_rect.width, 50)
    world_surface = pygame.Surface((world_rect.width, world_rect.height))
    settings_buttons = {}
    show_analysis_modal = False; analysis_text = "Loading AI analysis..."; gemini_button_rect, close_analysis_button_rect = None, None

    # Crucial change for web deployment
    display(screen, target="pygame-container", append=False)

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if game_state == 'settings_screen':
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    for key, rect in settings_buttons.items():
                        if rect.collidepoint(event.pos):
                            if key == 'start':
                                game_state = 'simulation'; world.reset(current_settings)
                            elif key == 'defaults':
                                current_settings = copy.deepcopy(DEFAULT_SETTINGS)
                            else:
                                var, op = key.rsplit('_', 1); params = current_settings[var]
                                if op == 'plus':
                                    params['value'] = min(params['max'], round(params['value'] + params['step'], 4))
                                elif op == 'minus':
                                    params['value'] = max(params['min'], round(params['value'] - params['step'], 4))
            elif game_state == 'simulation':
                if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                    game_state = 'settings_screen'
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if draw_buttons(button_rect).collidepoint(event.pos):
                        game_state = 'settings_screen'
            elif game_state == 'end_screen':
                 if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                    game_state = 'settings_screen'; show_analysis_modal = False
                 if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if gemini_button_rect and gemini_button_rect.collidepoint(event.pos) and not show_analysis_modal:
                        show_analysis_modal = True; analysis_text = "Loading AI analysis..."
                        prompt = f"You are a planetary scientist observing a simulation of Daisyworld. The experiment just ended. The final temperature was {world.planetary_temp:.2f}C, the white daisy population was {world.frac_white*100:.2f}%, and the black daisy population was {world.frac_black*100:.2f}%. The outcome was '{world.end_reason}'. Write a creative, narrative-style field report log entry explaining what you observed and the likely story of this planet's fate."
                        async def update_analysis():
                            nonlocal analysis_text; analysis_text = await call_gemini_api(prompt)
                        asyncio.create_task(update_analysis())
                    if close_analysis_button_rect and close_analysis_button_rect.collidepoint(event.pos):
                        show_analysis_modal = False

        if game_state == 'settings_screen':
            settings_buttons = draw_settings_screen(current_settings)
        elif game_state == 'simulation':
            world.step()
            if world.end_reason:
                game_state = 'end_screen'
            screen.fill(COLOR_BLACK); draw_daisyworld_surface(world_surface, world, world_surface.get_rect()); draw_graph(world, graph_rect); draw_info_panel(world, info_rect); draw_buttons(button_rect)
        elif game_state == 'end_screen':
            screen.fill(COLOR_BLACK); draw_daisyworld_surface(world_surface, world, world_surface.get_rect()); draw_graph(world, graph_rect); draw_info_panel(world, info_rect); draw_buttons(button_rect)
            gemini_button_rect = draw_end_screen(world)
            if show_analysis_modal:
                close_analysis_button_rect = draw_analysis_modal(analysis_text)

        pygame.display.flip()
        await asyncio.sleep(0)

    pygame.quit()

if __name__ == '__main__':
    asyncio.run(main())
