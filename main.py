

import pygame
import sys
import json
import os
from enum import Enum
from datetime import datetime
import math
import random


pygame.init()
pygame.mixer.init()


WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 800
FPS = 60
TILE_SIZE = 120
SAVE_FILE = "farm_save.json"


GRASS_GREEN = (126, 200, 80)
LIGHT_GREEN = (144, 238, 144)
DARK_GREEN = (0, 100, 0)
SOIL_BROWN = (139, 90, 43)
LIGHT_BROWN = (205, 133, 63)
SKY_BLUE = (135, 206, 250)
GOLDEN = (255, 215, 0)
CREAM = (255, 253, 208)
UI_BROWN = (222, 184, 135)
UI_DARK = (139, 69, 19)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
PURPLE = (147, 112, 219)
PINK = (255, 192, 203)
ORANGE = (255, 165, 0)
RED = (220, 20, 60)
GRAY = (128, 128, 128)
BROWN = (101, 67, 33)
YELLOW = (255, 255, 0)
GREEN = (0, 255, 0)

class GameState(Enum):
    START_SCREEN = 0
    MAIN = 1
    SHOP = 2
    INVENTORY = 3
    PLANTING = 4
    SETTINGS = 5

class Weather(Enum):
    SUNNY = 1
    RAINY = 2
    CLOUDY = 3

class CropType:
    def __init__(self, name, growth_stages, sell_price, seed_price, growth_time):
        self.name = name
        self.growth_stages = growth_stages
        self.sell_price = sell_price
        self.seed_price = seed_price
        self.growth_time = growth_time

class Crop:
    def __init__(self, crop_type):
        self.type = crop_type
        self.planted_time = None
        self.growth_stage = 0
        self.watered = False
        self.fertilized = False

    def plant(self):
        self.planted_time = pygame.time.get_ticks()

    def update(self):
        if self.planted_time:
            elapsed = pygame.time.get_ticks() - self.planted_time
            growth_multiplier = 1.5 if self.fertilized else 1.0
            if self.watered:
                growth_multiplier *= 1.2

            stage_time = (self.type.growth_time / self.type.growth_stages) / growth_multiplier
            self.growth_stage = min(int(elapsed / stage_time), self.type.growth_stages - 1)

    def is_ready(self):
        return self.growth_stage >= self.type.growth_stages - 1

class FarmPlot:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)
        self.crop = None
        self.is_tilled = False
        self.moisture = 0
        self.has_fence = False

    def till(self):
        self.is_tilled = True

    def water(self):
        self.moisture = 100
        if self.crop:
            self.crop.watered = True

    def fertilize(self):
        if self.crop:
            self.crop.fertilized = True

    def plant(self, crop):
        if self.is_tilled and not self.crop:
            self.crop = crop
            self.crop.plant()
            return True
        return False

    def harvest(self):
        if self.crop and self.crop.is_ready():
            harvested = self.crop
            self.crop = None
            return harvested
        return None

    def update(self):
        if self.moisture > 0:
            self.moisture = max(0, self.moisture - 0.05)
        if self.crop:
            self.crop.update()

class Particle:
    def __init__(self, x, y, color, velocity, life=30, size=3):
        self.x = x
        self.y = y
        self.vx = velocity[0]
        self.vy = velocity[1]
        self.color = color
        self.size = size
        self.life = life
        self.max_life = life

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.3  # Gravity
        self.life -= 1

    def draw(self, screen):
        if self.life > 0:
            alpha = self.life / self.max_life
            pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)),
                             int(self.size * alpha))

class ImageLoader:
    """Load and create game graphics"""
    def __init__(self):
        self.images = {}
        self.create_assets()

    def create_assets(self):
        """Create all game assets programmatically"""
        # Cat mascot
        self.images['cat'] = self.create_cat_mascot()

        # Coins
        self.images['coin'] = self.create_coin()

        # Shop
        self.images['shop'] = self.create_shop_icon()
        self.images['market'] = self.create_market_stall()

        # Bag
        self.images['bag'] = self.create_bag()

        # Farm elements
        self.images['plot'] = self.create_plot()
        self.images['seedling'] = self.create_seedling()

        # Fruits
        self.images['durian'] = self.create_durian()
        self.images['mangosteen'] = self.create_mangosteen()

        # Seeds
        self.images['durian_seed'] = self.create_seed_packet('durian')
        self.images['mangosteen_seed'] = self.create_seed_packet('mangosteen')

        # Tools
        self.images['water_can'] = self.create_water_can()
        self.images['fertilizer'] = self.create_fertilizer()

    def create_cat_mascot(self):
        """Create a cute cat mascot"""
        size = (200, 200)
        surface = pygame.Surface(size, pygame.SRCALPHA)

        # Body
        pygame.draw.ellipse(surface, WHITE, (50, 100, 100, 80))
        pygame.draw.ellipse(surface, BLACK, (50, 100, 100, 80), 3)

        # Head
        pygame.draw.circle(surface, WHITE, (100, 80), 50)
        pygame.draw.circle(surface, BLACK, (100, 80), 50, 3)

        # Ears
        pygame.draw.polygon(surface, WHITE, [(60, 50), (50, 20), (80, 40)])
        pygame.draw.polygon(surface, BLACK, [(60, 50), (50, 20), (80, 40)], 3)
        pygame.draw.polygon(surface, WHITE, [(120, 40), (150, 20), (140, 50)])
        pygame.draw.polygon(surface, BLACK, [(120, 40), (150, 20), (140, 50)], 3)

        # Eyes
        pygame.draw.circle(surface, BLACK, (80, 75), 8)
        pygame.draw.circle(surface, BLACK, (120, 75), 8)
        pygame.draw.circle(surface, WHITE, (82, 73), 3)
        pygame.draw.circle(surface, WHITE, (122, 73), 3)

        # Nose
        pygame.draw.polygon(surface, PINK, [(100, 85), (95, 95), (105, 95)])

        # Mouth
        pygame.draw.arc(surface, BLACK, (85, 85, 15, 15), 0, math.pi, 2)
        pygame.draw.arc(surface, BLACK, (100, 85, 15, 15), 0, math.pi, 2)

        # Tail
        pygame.draw.arc(surface, WHITE, (140, 120, 60, 60), -math.pi/4, math.pi/2, 20)
        pygame.draw.arc(surface, BLACK, (140, 120, 60, 60), -math.pi/4, math.pi/2, 3)

        return surface

    def create_coin(self):
        """Create a golden coin"""
        size = (64, 64)
        surface = pygame.Surface(size, pygame.SRCALPHA)

        # Outer circle
        pygame.draw.circle(surface, GOLDEN, (32, 32), 30)
        pygame.draw.circle(surface, (218, 165, 32), (32, 32), 30, 3)

        # Inner circle
        pygame.draw.circle(surface, (218, 165, 32), (32, 32), 24, 2)

        # Star
        star_points = []
        for i in range(10):
            angle = i * math.pi / 5
            if i % 2 == 0:
                r = 15
            else:
                r = 8
            x = 32 + r * math.cos(angle - math.pi/2)
            y = 32 + r * math.sin(angle - math.pi/2)
            star_points.append((x, y))
        pygame.draw.polygon(surface, (218, 165, 32), star_points)

        return surface

    def create_shop_icon(self):
        """Create shop icon"""
        size = (64, 64)
        surface = pygame.Surface(size, pygame.SRCALPHA)

        # Shop building
        pygame.draw.rect(surface, ORANGE, (10, 20, 44, 40))
        pygame.draw.rect(surface, BLACK, (10, 20, 44, 40), 2)

        # Roof
        pygame.draw.polygon(surface, RED, [(5, 20), (32, 5), (59, 20)])
        pygame.draw.polygon(surface, BLACK, [(5, 20), (32, 5), (59, 20)], 2)

        # Door
        pygame.draw.rect(surface, BROWN, (24, 40, 16, 20))
        pygame.draw.rect(surface, BLACK, (24, 40, 16, 20), 2)

        # Window
        pygame.draw.rect(surface, SKY_BLUE, (15, 28, 12, 10))
        pygame.draw.rect(surface, BLACK, (15, 28, 12, 10), 2)
        pygame.draw.rect(surface, SKY_BLUE, (37, 28, 12, 10))
        pygame.draw.rect(surface, BLACK, (37, 28, 12, 10), 2)

        return surface

    def create_market_stall(self):
        """Create market stall like in the image"""
        size = (200, 200)
        surface = pygame.Surface(size, pygame.SRCALPHA)

        # Wooden posts
        pygame.draw.rect(surface, BROWN, (30, 60, 20, 120))
        pygame.draw.rect(surface, BROWN, (150, 60, 20, 120))
        pygame.draw.rect(surface, BLACK, (30, 60, 20, 120), 2)
        pygame.draw.rect(surface, BLACK, (150, 60, 20, 120), 2)

        # Counter
        pygame.draw.rect(surface, UI_BROWN, (20, 120, 160, 60))
        pygame.draw.rect(surface, BLACK, (20, 120, 160, 60), 3)

        # Awning
        for i in range(4):
            x = 20 + i * 40
            color = YELLOW if i % 2 == 0 else WHITE
            pygame.draw.arc(surface, color, (x, 20, 40, 80), 0, math.pi, 30)
            pygame.draw.arc(surface, BLACK, (x, 20, 40, 80), 0, math.pi, 3)

        # Sign
        pygame.draw.rect(surface, UI_BROWN, (60, 30, 80, 40))
        pygame.draw.rect(surface, BLACK, (60, 30, 80, 40), 2)

        return surface

    def create_bag(self):
        """Create bag icon like in the image"""
        size = (80, 80)
        surface = pygame.Surface(size, pygame.SRCALPHA)

        # Bag body
        pygame.draw.ellipse(surface, BROWN, (10, 30, 60, 45))
        pygame.draw.ellipse(surface, (139, 69, 19), (10, 30, 60, 45), 3)

        # Handle
        pygame.draw.arc(surface, BROWN, (20, 15, 40, 30), 0, math.pi, 8)
        pygame.draw.arc(surface, (139, 69, 19), (20, 15, 40, 30), 0, math.pi, 3)

        # Flap
        pygame.draw.arc(surface, (160, 82, 45), (10, 25, 60, 30), 0, math.pi, 0)
        pygame.draw.arc(surface, (160, 82, 45), (10, 25, 60, 30), 0, math.pi, 20)
        pygame.draw.arc(surface, (139, 69, 19), (10, 25, 60, 30), 0, math.pi, 3)

        # Buckle
        pygame.draw.rect(surface, GOLDEN, (35, 35, 10, 8))
        pygame.draw.rect(surface, BLACK, (35, 35, 10, 8), 1)

        return surface

    def create_plot(self):
        """Create farm plot"""
        size = (TILE_SIZE, TILE_SIZE)
        surface = pygame.Surface(size, pygame.SRCALPHA)

        # Wooden fence border
        fence_color = (160, 82, 45)
        # Posts
        for i in range(5):
            x = i * 30
            pygame.draw.rect(surface, fence_color, (x, 0, 8, 20))
            pygame.draw.rect(surface, fence_color, (x, 100, 8, 20))
            pygame.draw.rect(surface, fence_color, (0, x, 20, 8))
            pygame.draw.rect(surface, fence_color, (100, x, 20, 8))

        # Soil
        pygame.draw.rect(surface, SOIL_BROWN, (20, 20, 80, 80))

        # Soil texture
        for i in range(3):
            for j in range(3):
                x = 30 + i * 25
                y = 30 + j * 25
                pygame.draw.circle(surface, LIGHT_BROWN, (x, y), 3)

        return surface

    def create_seedling(self):
        """Create seedling sprite"""
        size = (60, 60)
        surface = pygame.Surface(size, pygame.SRCALPHA)

        # Stem
        pygame.draw.rect(surface, DARK_GREEN, (28, 30, 4, 20))

        # Leaves
        pygame.draw.ellipse(surface, LIGHT_GREEN, (15, 15, 20, 25))
        pygame.draw.ellipse(surface, LIGHT_GREEN, (25, 15, 20, 25))
        pygame.draw.ellipse(surface, DARK_GREEN, (15, 15, 20, 25), 2)
        pygame.draw.ellipse(surface, DARK_GREEN, (25, 15, 20, 25), 2)

        # Soil mound
        pygame.draw.ellipse(surface, SOIL_BROWN, (10, 45, 40, 15))

        return surface

    def create_durian(self):
        """Create durian sprite"""
        size = (80, 80)
        surface = pygame.Surface(size, pygame.SRCALPHA)

        # Main body
        pygame.draw.ellipse(surface, (126, 200, 80), (10, 15, 60, 55))

        # Spikes
        for i in range(8):
            for j in range(6):
                x = 15 + i * 8
                y = 20 + j * 8
                if (i + j) % 2 == 0:
                    pygame.draw.polygon(surface, DARK_GREEN,
                                      [(x, y), (x-3, y+5), (x+3, y+5)])

        # Stem
        pygame.draw.rect(surface, BROWN, (38, 10, 4, 10))

        # Outline
        pygame.draw.ellipse(surface, BLACK, (10, 15, 60, 55), 2)

        return surface

    def create_mangosteen(self):
        """Create mangosteen sprite"""
        size = (70, 70)
        surface = pygame.Surface(size, pygame.SRCALPHA)

        # Main body
        pygame.draw.circle(surface, PURPLE, (35, 40), 28)
        pygame.draw.circle(surface, (128, 0, 128), (35, 40), 28, 3)

        # Top crown
        pygame.draw.circle(surface, DARK_GREEN, (35, 15), 12)
        for i in range(6):
            angle = i * math.pi / 3
            x = 35 + 10 * math.cos(angle)
            y = 15 + 10 * math.sin(angle)
            pygame.draw.circle(surface, LIGHT_GREEN, (int(x), int(y)), 5)

        # Highlight
        pygame.draw.ellipse(surface, (200, 150, 255), (25, 25, 15, 20))

        return surface

    def create_seed_packet(self, crop_type):
        """Create seed packet"""
        size = (60, 80)
        surface = pygame.Surface(size, pygame.SRCALPHA)

        # Packet
        pygame.draw.rect(surface, CREAM, (5, 5, 50, 70))
        pygame.draw.rect(surface, UI_DARK, (5, 5, 50, 70), 2)

        # Top tear line
        for i in range(5):
            pygame.draw.line(surface, BLACK, (10 + i*10, 10), (15 + i*10, 10), 1)

        # Label
        pygame.draw.rect(surface, WHITE, (10, 20, 40, 30))
        pygame.draw.rect(surface, BLACK, (10, 20, 40, 30), 1)

        # Crop image
        if crop_type == 'durian':
            pygame.draw.circle(surface, GREEN, (30, 35), 12)
            # Mini spikes
            for angle in range(0, 360, 60):
                x = 30 + 10 * math.cos(math.radians(angle))
                y = 35 + 10 * math.sin(math.radians(angle))
                pygame.draw.circle(surface, DARK_GREEN, (int(x), int(y)), 2)
        else:
            pygame.draw.circle(surface, PURPLE, (30, 35), 10)
            pygame.draw.circle(surface, DARK_GREEN, (30, 25), 5)

        # Seeds at bottom
        for i in range(3):
            pygame.draw.ellipse(surface, BROWN, (15 + i*10, 60, 6, 8))

        return surface

    def create_water_can(self):
        """Create watering can"""
        size = (80, 80)
        surface = pygame.Surface(size, pygame.SRCALPHA)

        # Can body
        pygame.draw.rect(surface, SKY_BLUE, (20, 30, 40, 35))
        pygame.draw.rect(surface, (0, 100, 200), (20, 30, 40, 35), 3)

        # Spout
        pygame.draw.polygon(surface, SKY_BLUE,
                          [(60, 35), (70, 25), (75, 30), (60, 45)])
        pygame.draw.polygon(surface, (0, 100, 200),
                          [(60, 35), (70, 25), (75, 30), (60, 45)], 2)

        # Handle
        pygame.draw.arc(surface, SKY_BLUE, (30, 20, 20, 30), math.pi/2, 3*math.pi/2, 5)
        pygame.draw.arc(surface, (0, 100, 200), (30, 20, 20, 30), math.pi/2, 3*math.pi/2, 2)

        # Water drops
        for i in range(3):
            pygame.draw.circle(surface, (173, 216, 230), (70 + i*3, 35 + i*5), 2)

        return surface

    def create_fertilizer(self):
        """Create fertilizer bag"""
        size = (60, 70)
        surface = pygame.Surface(size, pygame.SRCALPHA)

        # Bag
        pygame.draw.rect(surface, BROWN, (10, 15, 40, 50))
        pygame.draw.rect(surface, (101, 67, 33), (10, 15, 40, 50), 2)

        # Label
        pygame.draw.rect(surface, WHITE, (15, 25, 30, 20))
        pygame.draw.rect(surface, BLACK, (15, 25, 30, 20), 1)

        # Plant symbol
        pygame.draw.rect(surface, GREEN, (28, 32, 4, 8))
        pygame.draw.circle(surface, GREEN, (25, 30), 5)
        pygame.draw.circle(surface, GREEN, (35, 30), 5)

        # Top opening
        pygame.draw.polygon(surface, CREAM, [(10, 15), (20, 5), (40, 5), (50, 15)])
        pygame.draw.polygon(surface, (101, 67, 33), [(10, 15), (20, 5), (40, 5), (50, 15)], 2)

        return surface

    def get(self, name, size=None):
        img = self.images.get(name, self.create_placeholder(name))
        if size:
            return pygame.transform.scale(img, size)
        return img

    def create_placeholder(self, name):
        """Create placeholder if image missing"""
        size = (64, 64)
        surface = pygame.Surface(size, pygame.SRCALPHA)
        pygame.draw.rect(surface, PINK, (0, 0, size[0], size[1]), border_radius=10)
        pygame.draw.rect(surface, BLACK, (0, 0, size[0], size[1]), 2, border_radius=10)
        return surface

class SoundManager:
    """Manage game sounds"""
    def __init__(self):
        self.sounds = {}
        self.music_volume = 0.5
        self.sfx_volume = 0.7
        self.sfx_enabled = True
        self.create_sounds()

    def create_sounds(self):
        """Create simple sound effects"""
        # Since we can't load actual files, we'll use pygame's sound generation
        # In a real game, you would load actual sound files here
        pass

    def set_music_volume(self, volume):
        """Set background music volume (0.0 to 1.0)"""
        self.music_volume = max(0.0, min(1.0, volume))
        pygame.mixer.music.set_volume(self.music_volume)

    def set_sfx_volume(self, volume):
        """Set sound effects volume (0.0 to 1.0)"""
        self.sfx_volume = max(0.0, min(1.0, volume))

    def toggle_music(self):
        """Toggle music on/off"""
        if pygame.mixer.music.get_busy():
            pygame.mixer.music.pause()
        else:
            pygame.mixer.music.unpause()

    def play(self, sound_name):
        """Play a sound effect"""
        # In a real implementation, this would play the actual sound
        pass

class FarmGame:
    def __init__(self):
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("🌻 Happy Farm - Vegetables Day 🌻")
        self.clock = pygame.time.Clock()
        self.running = True
        self.state = GameState.START_SCREEN

        # Load assets
        self.images = ImageLoader()
        self.sounds = SoundManager()

        # Fonts
        self.font_huge = pygame.font.Font(None, 96)
        self.font_large = pygame.font.Font(None, 72)
        self.font_medium = pygame.font.Font(None, 48)
        self.font_small = pygame.font.Font(None, 32)
        self.font_tiny = pygame.font.Font(None, 24)

        # Game data
        self.coins = 500
        self.level = 1
        self.xp = 0
        self.day = 1
        self.weather = Weather.SUNNY

        # Enhanced inventory
        self.inventory = {
            "durian": 0,
            "mangosteen": 0,
            "durian_seeds": 10,
            "mangosteen_seeds": 10,
            "fertilizer": 5,
            "water_can": 1
        }

        # Crop types
        self.crop_types = {
            "durian": CropType("Durian", 3, 100, 30, 10000),
            "mangosteen": CropType("Mangosteen", 3, 60, 20, 7000)
        }

        # Create farm plots (4x4 grid)
        self.plots = []
        start_x = 320
        start_y = 200
        spacing = TILE_SIZE + 30
        for i in range(4):
            for j in range(4):
                x = start_x + j * spacing
                y = start_y + i * spacing
                self.plots.append(FarmPlot(x, y))

        # Particles
        self.particles = []

        # Selected plot for planting
        self.selected_plot = None

        # Decorative elements
        self.clouds = []
        for i in range(5):
            self.clouds.append({
                'x': random.randint(0, WINDOW_WIDTH),
                'y': random.randint(50, 150),
                'speed': random.uniform(0.3, 1.0),
                'size': random.randint(40, 80)
            })

        # Animation timers
        self.animation_timer = 0

        # Sound settings
        self.music_enabled = True
        self.sfx_enabled = True

        # Settings screen elements
        self.music_slider_rect = pygame.Rect(500, 250, 300, 20)
        self.sfx_slider_rect = pygame.Rect(500, 350, 300, 20)
        self.music_slider_pos = self.music_slider_rect.x + int(self.sounds.music_volume * 300)
        self.sfx_slider_pos = self.sfx_slider_rect.x + int(self.sounds.sfx_volume * 300)
        self.dragging_music = False
        self.dragging_sfx = False
        self.music_toggle_rect = pygame.Rect(850, 240, 100, 40)
        self.sfx_toggle_rect = pygame.Rect(850, 340, 100, 40)

        # UI Elements
        self.create_ui_elements()

        # Tool modes
        self.watering_mode = False
        self.fertilizing_mode = False

        # Load saved game and settings
        self.load_settings()
        self.load_game()

    def create_ui_elements(self):
        """Create all UI buttons and elements"""
        # Main screen buttons
        self.shop_button = pygame.Rect(50, 50, 180, 70)
        self.inventory_button = pygame.Rect(50, 130, 180, 70)
        self.save_button = pygame.Rect(1050, 50, 150, 60)
        self.settings_button = pygame.Rect(1050, 120, 150, 60)

        # Tool buttons
        self.water_button = pygame.Rect(50, 250, 180, 60)
        self.fertilize_button = pygame.Rect(50, 320, 180, 60)

        # Back button (universal)
        self.back_button = pygame.Rect(50, 700, 150, 60)

        # Start screen buttons
        self.new_game_button = pygame.Rect(WINDOW_WIDTH//2 - 200, 450, 400, 80)
        self.continue_button = pygame.Rect(WINDOW_WIDTH//2 - 200, 550, 400, 80)

        # Shop items with better layout
        self.shop_items = []
        shop_x = 350
        shop_y = 250
        items = [
            ("Durian Seeds", "durian_seeds", 30, 'durian_seed'),
            ("Mangosteen Seeds", "mangosteen_seeds", 20, 'mangosteen_seed'),
            ("Fertilizer", "fertilizer", 15, 'fertilizer'),
            ("Premium Water Can", "water_can", 50, 'water_can')
        ]

        for i, (name, key, price, icon) in enumerate(items):
            self.shop_items.append({
                'name': name,
                'key': key,
                'price': price,
                'icon': icon,
                'rect': pygame.Rect(shop_x + (i % 2) * 300, shop_y + (i // 2) * 150, 280, 120)
            })

    def load_game(self):
        """Load saved game data"""
        try:
            if os.path.exists(SAVE_FILE):
                with open(SAVE_FILE, 'r') as f:
                    data = json.load(f)
                    self.coins = data.get('coins', 500)
                    self.level = data.get('level', 1)
                    self.xp = data.get('xp', 0)
                    self.day = data.get('day', 1)
                    self.inventory = data.get('inventory', self.inventory)

                    # Load plots
                    plot_data = data.get('plots', [])
                    for i, plot_info in enumerate(plot_data):
                        if i < len(self.plots):
                            self.plots[i].is_tilled = plot_info.get('tilled', False)
                            self.plots[i].moisture = plot_info.get('moisture', 0)

                            if plot_info.get('has_crop'):
                                crop_type = plot_info.get('crop_type')
                                if crop_type in self.crop_types:
                                    crop = Crop(self.crop_types[crop_type])
                                    crop.growth_stage = plot_info.get('growth_stage', 0)
                                    crop.watered = plot_info.get('watered', False)
                                    crop.fertilized = plot_info.get('fertilized', False)
                                    self.plots[i].crop = crop
        except Exception as e:
            print(f"Error loading save: {e}")

    def save_game(self):
        """Save game data"""
        plot_data = []
        for plot in self.plots:
            plot_info = {
                'tilled': plot.is_tilled,
                'moisture': plot.moisture,
                'has_crop': plot.crop is not None
            }
            if plot.crop:
                plot_info['crop_type'] = plot.crop.type.name.lower()
                plot_info['growth_stage'] = plot.crop.growth_stage
                plot_info['watered'] = plot.crop.watered
                plot_info['fertilized'] = plot.crop.fertilized
            plot_data.append(plot_info)

        save_data = {
            'coins': self.coins,
            'level': self.level,
            'xp': self.xp,
            'day': self.day,
            'inventory': self.inventory,
            'plots': plot_data,
            'timestamp': datetime.now().isoformat()
        }

        try:
            with open(SAVE_FILE, 'w') as f:
                json.dump(save_data, f, indent=2)
            print("Game saved successfully!")
            return True
        except Exception as e:
            print(f"Error saving game: {e}")
            return False

    def draw_background(self):
        """Draw beautiful background with gradient sky"""
        # Gradient sky
        for i in range(WINDOW_HEIGHT // 2):
            ratio = i / (WINDOW_HEIGHT // 2)
            r = int(135 + (255 - 135) * ratio)
            g = int(206 + (255 - 206) * ratio)
            b = int(250 + (255 - 250) * ratio)
            pygame.draw.line(self.screen, (r, g, b), (0, i), (WINDOW_WIDTH, i))

        # Ground
        pygame.draw.rect(self.screen, GRASS_GREEN, (0, WINDOW_HEIGHT // 2, WINDOW_WIDTH, WINDOW_HEIGHT // 2))

        # Draw animated clouds
        for cloud in self.clouds:
            self.draw_cloud(cloud['x'], cloud['y'], cloud['size'])
            cloud['x'] += cloud['speed']
            if cloud['x'] > WINDOW_WIDTH + 100:
                cloud['x'] = -100

        # Decorative flowers
        for i in range(15):
            x = 100 + i * 80
            y = WINDOW_HEIGHT - 100 + random.randint(-20, 20)
            self.draw_flower(x, y)

    def draw_cloud(self, x, y, size):
        """Draw fluffy cloud"""
        for i in range(3):
            for j in range(2):
                offset_x = i * size//3 - size//3
                offset_y = j * size//4 - size//8
                circle_size = size//2 + random.randint(-5, 5)
                pygame.draw.circle(self.screen, WHITE,
                                 (int(x + offset_x), int(y + offset_y)), circle_size)

    def draw_flower(self, x, y):
        """Draw decorative flower"""
        colors = [PINK, RED, YELLOW, PURPLE]
        color = random.choice(colors)
        # Stem
        pygame.draw.line(self.screen, DARK_GREEN, (x, y), (x, y - 20), 3)
        # Petals
        for angle in range(0, 360, 60):
            px = x + 10 * math.cos(math.radians(angle))
            py = y - 20 + 10 * math.sin(math.radians(angle))
            pygame.draw.circle(self.screen, color, (int(px), int(py)), 6)
        # Center
        pygame.draw.circle(self.screen, YELLOW, (x, y - 20), 4)

    def draw_start_screen(self):
        """Draw start screen with cat mascot"""
        self.draw_background()

        # Title with shadow effect
        title_text = "VEGETABLES DAY"
        for i in range(3):
            shadow = self.font_huge.render(title_text, True, BLACK)
            self.screen.blit(shadow, (WINDOW_WIDTH//2 - shadow.get_width()//2 + 3-i, 103-i))
        title = self.font_huge.render(title_text, True, GOLDEN)
        self.screen.blit(title, (WINDOW_WIDTH//2 - title.get_width()//2, 100))

        # Draw cat mascot
        cat_img = self.images.get('cat', (200, 200))
        cat_rect = cat_img.get_rect(center=(WINDOW_WIDTH//2, 300))
        self.screen.blit(cat_img, cat_rect)

        # Animated welcome text
        wave = math.sin(self.animation_timer * 0.05) * 10
        welcome = self.font_medium.render("Welcome to your farm adventure!", True, WHITE)
        self.screen.blit(welcome, (WINDOW_WIDTH//2 - welcome.get_width()//2, 420 + wave))

        # Beautiful buttons
        # New Game
        pygame.draw.rect(self.screen, LIGHT_GREEN, self.new_game_button, border_radius=20)
        pygame.draw.rect(self.screen, DARK_GREEN, self.new_game_button, 4, border_radius=20)
        new_text = self.font_medium.render("🌱 New Game", True, WHITE)
        self.screen.blit(new_text, (self.new_game_button.centerx - new_text.get_width()//2,
                                    self.new_game_button.centery - new_text.get_height()//2))

        # Continue (if save exists)
        if os.path.exists(SAVE_FILE):
            pygame.draw.rect(self.screen, ORANGE, self.continue_button, border_radius=20)
            pygame.draw.rect(self.screen, UI_DARK, self.continue_button, 4, border_radius=20)
            cont_text = self.font_medium.render("📂 Continue", True, WHITE)
            self.screen.blit(cont_text, (self.continue_button.centerx - cont_text.get_width()//2,
                                        self.continue_button.centery - cont_text.get_height()//2))

    def draw_ui_panel(self):
        """Draw main UI panel with stats"""
        # Main panel
        panel = pygame.Rect(10, 10, 280, 220)
        pygame.draw.rect(self.screen, CREAM, panel, border_radius=20)
        pygame.draw.rect(self.screen, UI_DARK, panel, 4, border_radius=20)

        # Draw coin with icon
        coin_img = self.images.get('coin', (32, 32))
        self.screen.blit(coin_img, (25, 25))
        coin_text = self.font_small.render(f": ${self.coins}", True, BLACK)
        self.screen.blit(coin_text, (65, 30))

        # Stats
        stats = [
            f"⭐ Level: {self.level}",
            f"✨ XP: {self.xp}/100",
            f"📅 Day: {self.day}",
            f"🌤️ {self.weather.name.title()}"
        ]

        y_offset = 70
        for stat in stats:
            text = self.font_small.render(stat, True, BLACK)
            self.screen.blit(text, (25, y_offset))
            y_offset += 35

    def draw_farm_plot(self, plot):
        """Draw individual farm plot with effects"""
        # Shadow
        shadow_rect = plot.rect.copy()
        shadow_rect.x += 5
        shadow_rect.y += 5
        pygame.draw.rect(self.screen, (0, 0, 0, 50), shadow_rect, border_radius=10)

        # Plot background
        if plot.is_tilled:
            # Draw plot image
            plot_img = self.images.get('plot', (TILE_SIZE, TILE_SIZE))
            self.screen.blit(plot_img, plot.rect)
        else:
            # Untilled ground
            pygame.draw.rect(self.screen, GRASS_GREEN, plot.rect, border_radius=10)
            pygame.draw.rect(self.screen, DARK_GREEN, plot.rect, 3, border_radius=10)

        # Moisture effect
        if plot.moisture > 0 and plot.is_tilled:
            # Create darker wet soil effect
            moisture_surf = pygame.Surface((plot.rect.width, plot.rect.height), pygame.SRCALPHA)
            alpha = int(plot.moisture * 0.5)  # Max 50% opacity
            moisture_surf.fill((*SKY_BLUE, alpha))
            self.screen.blit(moisture_surf, plot.rect)

        # Draw crop
        if plot.crop:
            self.draw_crop(plot)

    def draw_crop(self, plot):
        """Draw crop with growth animation"""
        crop = plot.crop
        center_x = plot.rect.centerx
        center_y = plot.rect.centery

        # Growth animation
        bounce = math.sin(self.animation_timer * 0.1) * 2

        if crop.type.name == "Durian":
            if crop.growth_stage == 0:
                # Seedling
                img = self.images.get('seedling', (40, 40))
                self.screen.blit(img, (center_x - 20, center_y - 20 + bounce))
            elif crop.growth_stage == 1:
                # Growing - smaller durian
                img = self.images.get('durian', (60, 60))
                self.screen.blit(img, (center_x - 30, center_y - 30 + bounce))
            else:
                # Mature - full size durian
                img = self.images.get('durian', (80, 80))
                self.screen.blit(img, (center_x - 40, center_y - 40 + bounce))

        elif crop.type.name == "Mangosteen":
            if crop.growth_stage == 0:
                # Seedling
                img = self.images.get('seedling', (40, 40))
                self.screen.blit(img, (center_x - 20, center_y - 20 + bounce))
            elif crop.growth_stage == 1:
                # Growing - smaller mangosteen
                img = self.images.get('mangosteen', (50, 50))
                self.screen.blit(img, (center_x - 25, center_y - 25 + bounce))
            else:
                # Mature - full size mangosteen
                img = self.images.get('mangosteen', (70, 70))
                self.screen.blit(img, (center_x - 35, center_y - 35 + bounce))

        # Ready indicator
        if crop.is_ready():
            # Glowing effect
            glow_size = 15 + math.sin(self.animation_timer * 0.1) * 5
            pygame.draw.circle(self.screen, GOLDEN, (center_x + 40, center_y - 40), int(glow_size))
            pygame.draw.circle(self.screen, YELLOW, (center_x + 40, center_y - 40), 12)
            ready_text = self.font_tiny.render("!", True, BLACK)
            self.screen.blit(ready_text, (center_x + 36, center_y - 48))

    def draw_main_game(self):
        """Draw main game screen"""
        self.draw_background()

        # Draw UI panel
        self.draw_ui_panel()

        # Draw buttons with icons
        buttons = [
            (self.shop_button, "🛒 Shop", ORANGE),
            (self.inventory_button, "🎒 Inventory", PURPLE),
            (self.save_button, "💾 Save", LIGHT_GREEN),
            (self.settings_button, "⚙️ Settings", UI_BROWN),
            (self.water_button, "💧 Water", SKY_BLUE),
            (self.fertilize_button, "🌱 Fertilize", DARK_GREEN)
        ]

        for button, text, color in buttons:
            # Button shadow
            shadow = button.copy()
            shadow.x += 3
            shadow.y += 3
            pygame.draw.rect(self.screen, (0, 0, 0, 100), shadow, border_radius=15)

            # Highlight if tool is active
            if (text == "💧 Water" and self.watering_mode) or \
               (text == "🌱 Fertilize" and self.fertilizing_mode):
                pygame.draw.rect(self.screen, YELLOW, button.inflate(6, 6), border_radius=15)

            # Button
            pygame.draw.rect(self.screen, color, button, border_radius=15)
            pygame.draw.rect(self.screen, BLACK, button, 3, border_radius=15)

            # Text
            btn_text = self.font_small.render(text, True, WHITE)
            self.screen.blit(btn_text, (button.centerx - btn_text.get_width()//2,
                                       button.centery - btn_text.get_height()//2))

        # Draw farm plots
        for plot in self.plots:
            self.draw_farm_plot(plot)

        # Draw particles
        for particle in self.particles[:]:
            particle.update()
            particle.draw(self.screen)
            if particle.life <= 0:
                self.particles.remove(particle)

        # Draw active tool cursor
        if self.watering_mode or self.fertilizing_mode:
            mouse_x, mouse_y = pygame.mouse.get_pos()
            if self.watering_mode:
                cursor_img = self.images.get('water_can', (40, 40))
            else:
                cursor_img = self.images.get('fertilizer', (40, 40))
            self.screen.blit(cursor_img, (mouse_x - 20, mouse_y - 20))

    def draw_shop(self):
        """Draw shop screen"""
        self.draw_background()

        # Shop building background
        shop_bg = pygame.Rect(200, 50, 880, 650)
        pygame.draw.rect(self.screen, CREAM, shop_bg, border_radius=30)
        pygame.draw.rect(self.screen, UI_DARK, shop_bg, 5, border_radius=30)

        # Shop building with shop image
        shop_img = self.images.get('market', (100, 100))
        self.screen.blit(shop_img, (340, 60))

        # Title background
        sign_rect = pygame.Rect(440, 70, 400, 100)
        pygame.draw.rect(self.screen, ORANGE, sign_rect, border_radius=20)
        pygame.draw.rect(self.screen, UI_DARK, sign_rect, 4, border_radius=20)

        # Title
        title = self.font_large.render("FARM SHOP", True, WHITE)
        self.screen.blit(title, (WINDOW_WIDTH//2 - title.get_width()//2, 100))

        # Coins display
        coin_bg = pygame.Rect(850, 180, 200, 60)
        pygame.draw.rect(self.screen, GOLDEN, coin_bg, border_radius=15)
        pygame.draw.rect(self.screen, BLACK, coin_bg, 3, border_radius=15)
        coin_img = self.images.get('coin', (40, 40))
        self.screen.blit(coin_img, (870, 190))
        coin_text = self.font_medium.render(f"${self.coins}", True, BLACK)
        self.screen.blit(coin_text, (920, 195))

        # Shop items
        for item in self.shop_items:
            # Item card
            pygame.draw.rect(self.screen, WHITE, item['rect'], border_radius=20)
            pygame.draw.rect(self.screen, BLACK, item['rect'], 3, border_radius=20)

            # Item icon
            icon = self.images.get(item['icon'], (60, 60))
            self.screen.blit(icon, (item['rect'].x + 10, item['rect'].centery - 30))

            # Item name and price
            name_text = self.font_small.render(item['name'], True, BLACK)
            price_text = self.font_medium.render(f"${item['price']}", True, DARK_GREEN)

            self.screen.blit(name_text, (item['rect'].x + 80, item['rect'].y + 20))
            self.screen.blit(price_text, (item['rect'].x + 80, item['rect'].y + 55))

            # Buy button
            buy_btn = pygame.Rect(item['rect'].right - 80, item['rect'].centery - 20, 60, 40)
            btn_color = LIGHT_GREEN if self.coins >= item['price'] else GRAY
            pygame.draw.rect(self.screen, btn_color, buy_btn, border_radius=10)
            pygame.draw.rect(self.screen, BLACK, buy_btn, 2, border_radius=10)
            buy_text = self.font_tiny.render("BUY", True, WHITE)
            self.screen.blit(buy_text, (buy_btn.centerx - buy_text.get_width()//2,
                                       buy_btn.centery - buy_text.get_height()//2))

        # Back button
        self.draw_back_button()

    def draw_inventory(self):
        """Draw inventory screen matching the design"""
        self.draw_background()

        # Inventory window
        inv_bg = pygame.Rect(200, 50, 880, 650)
        pygame.draw.rect(self.screen, UI_BROWN, inv_bg, border_radius=30)
        pygame.draw.rect(self.screen, BLACK, inv_bg, 5, border_radius=30)

        # Title bar
        title_bg = pygame.Rect(220, 70, 840, 100)
        pygame.draw.rect(self.screen, DARK_GREEN, title_bg, border_radius=20)

        # Title
        title = self.font_large.render("Farm Marketplace", True, WHITE)
        self.screen.blit(title, (WINDOW_WIDTH//2 - title.get_width()//2, 90))

        # Tabs
        tabs = [
            ("🌿 Crops", True),
            ("🔨 Upgrade Materials", False),
            ("⭐ Special Items", False)
        ]

        tab_x = 250
        for tab_text, active in tabs:
            tab_rect = pygame.Rect(tab_x, 190, 250, 50)
            tab_color = LIGHT_GREEN if active else CREAM
            pygame.draw.rect(self.screen, tab_color, tab_rect, border_radius=15)
            pygame.draw.rect(self.screen, BLACK, tab_rect, 2, border_radius=15)

            text = self.font_small.render(tab_text, True, BLACK)
            self.screen.blit(text, (tab_rect.centerx - text.get_width()//2,
                                   tab_rect.centery - text.get_height()//2))
            tab_x += 270

        # Inventory items display
        item_y = 270
        items = [
            ("Durian", self.inventory.get("durian", 0), 'durian', GREEN),
            ("Mangosteen", self.inventory.get("mangosteen", 0), 'mangosteen', PURPLE)
        ]

        for name, count, icon, color in items:
            # Item row background
            item_bg = pygame.Rect(250, item_y, 780, 80)
            pygame.draw.rect(self.screen, CREAM, item_bg, border_radius=15)
            pygame.draw.rect(self.screen, BLACK, item_bg, 2, border_radius=15)

            # Item icon
            icon_img = self.images.get(icon, (60, 60))
            self.screen.blit(icon_img, (270, item_y + 10))

            # Item name
            name_text = self.font_medium.render(name, True, BLACK)
            self.screen.blit(name_text, (350, item_y + 25))

            # Stock count
            stock_text = self.font_small.render(f"In stock: {count}", True, color)
            self.screen.blit(stock_text, (350, item_y + 55))

            item_y += 100

        # Back button
        self.draw_back_button()

    def draw_planting_menu(self):
        """Draw seed selection menu"""
        self.draw_background()

        # Menu background
        menu_bg = pygame.Rect(300, 200, 680, 400)
        pygame.draw.rect(self.screen, CREAM, menu_bg, border_radius=30)
        pygame.draw.rect(self.screen, UI_DARK, menu_bg, 5, border_radius=30)

        # Title
        title = self.font_medium.render("Select Seed to Plant", True, BLACK)
        self.screen.blit(title, (WINDOW_WIDTH//2 - title.get_width()//2, 230))

        # Seed options
        seeds = [
            ("Durian", "durian_seeds", 400, 350, DARK_GREEN, 'durian_seed'),
            ("Mangosteen", "mangosteen_seeds", 600, 350, PURPLE, 'mangosteen_seed')
        ]

        for name, key, x, y, color, icon in seeds:
            count = self.inventory.get(key, 0)

            # Seed card
            card = pygame.Rect(x - 80, y - 80, 160, 160)
            card_color = color if count > 0 else GRAY
            pygame.draw.rect(self.screen, card_color, card, border_radius=20)
            pygame.draw.rect(self.screen, BLACK, card, 3, border_radius=20)

            # Seed icon
            seed_img = self.images.get(icon, (80, 80))
            self.screen.blit(seed_img, (x - 40, y - 60))

            # Text
            name_text = self.font_small.render(name, True, WHITE)
            count_text = self.font_small.render(f"x{count}", True, WHITE)

            self.screen.blit(name_text, (x - name_text.get_width()//2, y + 30))
            self.screen.blit(count_text, (x - count_text.get_width()//2, y + 60))

        self.draw_back_button()

    def draw_settings(self):
        """Draw settings screen"""
        self.draw_background()

        # Settings panel
        panel = pygame.Rect(240, 100, 800, 600)
        pygame.draw.rect(self.screen, CREAM, panel, border_radius=30)
        pygame.draw.rect(self.screen, UI_DARK, panel, 5, border_radius=30)

        # Title
        title = self.font_large.render("⚙️ SETTINGS", True, BLACK)
        self.screen.blit(title, (WINDOW_WIDTH//2 - title.get_width()//2, 130))

        # Music Volume
        music_text = self.font_medium.render("🎵 Music Volume", True, BLACK)
        self.screen.blit(music_text, (300, 240))

        # Music slider background
        pygame.draw.rect(self.screen, GRAY, self.music_slider_rect, border_radius=10)
        pygame.draw.rect(self.screen, BLACK, self.music_slider_rect, 2, border_radius=10)

        # Music slider fill
        fill_width = int((self.sounds.music_volume) * self.music_slider_rect.width)
        fill_rect = pygame.Rect(self.music_slider_rect.x, self.music_slider_rect.y,
                               fill_width, self.music_slider_rect.height)
        pygame.draw.rect(self.screen, GOLDEN, fill_rect, border_radius=10)

        # Music slider handle
        handle_x = self.music_slider_rect.x + int(self.sounds.music_volume * self.music_slider_rect.width)
        pygame.draw.circle(self.screen, WHITE, (handle_x, self.music_slider_rect.centery), 15)
        pygame.draw.circle(self.screen, BLACK, (handle_x, self.music_slider_rect.centery), 15, 2)

        # Music percentage
        music_percent = self.font_small.render(f"{int(self.sounds.music_volume * 100)}%", True, BLACK)
        self.screen.blit(music_percent, (self.music_slider_rect.right + 20, self.music_slider_rect.centery - 10))

        # Music toggle button
        toggle_color = LIGHT_GREEN if self.music_enabled else RED
        pygame.draw.rect(self.screen, toggle_color, self.music_toggle_rect, border_radius=20)
        pygame.draw.rect(self.screen, BLACK, self.music_toggle_rect, 3, border_radius=20)
        toggle_text = self.font_small.render("ON" if self.music_enabled else "OFF", True, WHITE)
        self.screen.blit(toggle_text, (self.music_toggle_rect.centerx - toggle_text.get_width()//2,
                                       self.music_toggle_rect.centery - toggle_text.get_height()//2))

        # Sound Effects Volume
        sfx_text = self.font_medium.render("🔊 Sound Effects", True, BLACK)
        self.screen.blit(sfx_text, (300, 340))

        # SFX slider background
        pygame.draw.rect(self.screen, GRAY, self.sfx_slider_rect, border_radius=10)
        pygame.draw.rect(self.screen, BLACK, self.sfx_slider_rect, 2, border_radius=10)

        # SFX slider fill
        sfx_fill_width = int((self.sounds.sfx_volume) * self.sfx_slider_rect.width)
        sfx_fill_rect = pygame.Rect(self.sfx_slider_rect.x, self.sfx_slider_rect.y,
                                   sfx_fill_width, self.sfx_slider_rect.height)
        pygame.draw.rect(self.screen, SKY_BLUE, sfx_fill_rect, border_radius=10)

        # SFX slider handle
        sfx_handle_x = self.sfx_slider_rect.x + int(self.sounds.sfx_volume * self.sfx_slider_rect.width)
        pygame.draw.circle(self.screen, WHITE, (sfx_handle_x, self.sfx_slider_rect.centery), 15)
        pygame.draw.circle(self.screen, BLACK, (sfx_handle_x, self.sfx_slider_rect.centery), 15, 2)

        # SFX percentage
        sfx_percent = self.font_small.render(f"{int(self.sounds.sfx_volume * 100)}%", True, BLACK)
        self.screen.blit(sfx_percent, (self.sfx_slider_rect.right + 20, self.sfx_slider_rect.centery - 10))

        # SFX toggle button
        sfx_toggle_color = LIGHT_GREEN if self.sfx_enabled else RED
        pygame.draw.rect(self.screen, sfx_toggle_color, self.sfx_toggle_rect, border_radius=20)
        pygame.draw.rect(self.screen, BLACK, self.sfx_toggle_rect, 3, border_radius=20)
        sfx_toggle_text = self.font_small.render("ON" if self.sfx_enabled else "OFF", True, WHITE)
        self.screen.blit(sfx_toggle_text, (self.sfx_toggle_rect.centerx - sfx_toggle_text.get_width()//2,
                                           self.sfx_toggle_rect.centery - sfx_toggle_text.get_height()//2))

        # Instructions
        inst_y = 450
        instructions = [
            "🎵 Drag sliders to adjust volume",
            "🔇 Click ON/OFF to toggle sounds",
            "💾 Settings are saved automatically"
        ]
        for instruction in instructions:
            inst_text = self.font_small.render(instruction, True, BLACK)
            self.screen.blit(inst_text, (WINDOW_WIDTH//2 - inst_text.get_width()//2, inst_y))
            inst_y += 40

        # Back button
        self.draw_back_button()

    def draw_back_button(self):
        """Draw universal back button"""
        pygame.draw.rect(self.screen, RED, self.back_button, border_radius=15)
        pygame.draw.rect(self.screen, BLACK, self.back_button, 3, border_radius=15)
        back_text = self.font_small.render("← Back", True, WHITE)
        self.screen.blit(back_text, (self.back_button.centerx - back_text.get_width()//2,
                                     self.back_button.centery - back_text.get_height()//2))

    def create_particles(self, x, y, particle_type):
        """Create particle effects"""
        if particle_type == "water":
            for _ in range(15):
                vx = random.uniform(-3, 3)
                vy = random.uniform(-5, -2)
                self.particles.append(Particle(x, y, SKY_BLUE, (vx, vy), 40, 4))

        elif particle_type == "harvest":
            colors = [GOLDEN, YELLOW, ORANGE]
            for _ in range(20):
                vx = random.uniform(-4, 4)
                vy = random.uniform(-6, -2)
                color = random.choice(colors)
                self.particles.append(Particle(x, y, color, (vx, vy), 50, 5))

        elif particle_type == "plant":
            for _ in range(10):
                vx = random.uniform(-2, 2)
                vy = random.uniform(-3, -1)
                self.particles.append(Particle(x, y, LIGHT_GREEN, (vx, vy), 30, 3))

        elif particle_type == "fertilize":
            for _ in range(12):
                vx = random.uniform(-3, 3)
                vy = random.uniform(-4, -2)
                self.particles.append(Particle(x, y, BROWN, (vx, vy), 35, 4))

        elif particle_type == "coin":
            for _ in range(8):
                vx = random.uniform(-2, 2)
                vy = random.uniform(-5, -3)
                self.particles.append(Particle(x, y, GOLDEN, (vx, vy), 40, 6))

    def handle_events(self):
        """Handle all game events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.save_game()
                self.save_settings()
                self.running = False

            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                self.sounds.play('click')

                if self.state == GameState.START_SCREEN:
                    if self.new_game_button.collidepoint(mouse_pos):
                        self.reset_game()
                        self.state = GameState.MAIN
                    elif self.continue_button.collidepoint(mouse_pos) and os.path.exists(SAVE_FILE):
                        self.state = GameState.MAIN

                elif self.state == GameState.MAIN:
                    self.handle_main_click(mouse_pos)

                elif self.state == GameState.SHOP:
                    self.handle_shop_click(mouse_pos)

                elif self.state == GameState.INVENTORY:
                    if self.back_button.collidepoint(mouse_pos):
                        self.state = GameState.MAIN

                elif self.state == GameState.PLANTING:
                    self.handle_planting_click(mouse_pos)

                elif self.state == GameState.SETTINGS:
                    self.handle_settings_click(mouse_pos)

            elif event.type == pygame.MOUSEBUTTONUP:
                self.dragging_music = False
                self.dragging_sfx = False

            elif event.type == pygame.MOUSEMOTION:
                if self.state == GameState.SETTINGS:
                    mouse_x = event.pos[0]
                    if self.dragging_music:
                        # Update music volume based on mouse position
                        relative_x = mouse_x - self.music_slider_rect.x
                        volume = max(0, min(1, relative_x / self.music_slider_rect.width))
                        self.sounds.set_music_volume(volume)
                    elif self.dragging_sfx:
                        # Update SFX volume based on mouse position
                        relative_x = mouse_x - self.sfx_slider_rect.x
                        volume = max(0, min(1, relative_x / self.sfx_slider_rect.width))
                        self.sounds.set_sfx_volume(volume)

    def handle_main_click(self, mouse_pos):
        """Handle clicks on main game screen"""
        # UI Buttons
        if self.shop_button.collidepoint(mouse_pos):
            self.state = GameState.SHOP
            self.watering_mode = False
            self.fertilizing_mode = False
        elif self.inventory_button.collidepoint(mouse_pos):
            self.state = GameState.INVENTORY
            self.watering_mode = False
            self.fertilizing_mode = False
        elif self.save_button.collidepoint(mouse_pos):
            if self.save_game():
                self.create_particles(mouse_pos[0], mouse_pos[1], "coin")
        elif self.settings_button.collidepoint(mouse_pos):
            self.state = GameState.SETTINGS
            self.watering_mode = False
            self.fertilizing_mode = False
        elif self.water_button.collidepoint(mouse_pos):
            self.watering_mode = not self.watering_mode
            self.fertilizing_mode = False
            return
        elif self.fertilize_button.collidepoint(mouse_pos):
            self.fertilizing_mode = not self.fertilizing_mode
            self.watering_mode = False
            return

        # Farm plots
        for plot in self.plots:
            if plot.rect.collidepoint(mouse_pos):
                if self.watering_mode:
                    plot.water()
                    self.create_particles(plot.rect.centerx, plot.rect.centery, "water")
                    self.sounds.play('water')

                elif self.fertilizing_mode:
                    if plot.crop and self.inventory.get("fertilizer", 0) > 0:
                        plot.fertilize()
                        self.inventory["fertilizer"] -= 1
                        self.create_particles(plot.rect.centerx, plot.rect.centery, "fertilize")
                        self.sounds.play('plant')

                elif not plot.is_tilled:
                    plot.till()
                    self.sounds.play('plant')

                elif plot.crop and plot.crop.is_ready():
                    harvested = plot.harvest()
                    if harvested:
                        self.inventory[harvested.type.name.lower()] += 1
                        self.coins += harvested.type.sell_price
                        self.xp += 10
                        self.check_level_up()
                        self.create_particles(plot.rect.centerx, plot.rect.centery, "harvest")
                        self.sounds.play('harvest')

                elif not plot.crop:
                    self.selected_plot = plot
                    self.state = GameState.PLANTING
                    self.watering_mode = False
                    self.fertilizing_mode = False

    def handle_shop_click(self, mouse_pos):
        """Handle shop interactions"""
        if self.back_button.collidepoint(mouse_pos):
            self.state = GameState.MAIN
            return

        # Check shop items
        for item in self.shop_items:
            buy_btn = pygame.Rect(item['rect'].right - 80, item['rect'].centery - 20, 60, 40)
            if buy_btn.collidepoint(mouse_pos) and self.coins >= item['price']:
                self.coins -= item['price']
                self.inventory[item['key']] += 1
                self.create_particles(mouse_pos[0], mouse_pos[1], "coin")
                self.sounds.play('coin')

    def handle_planting_click(self, mouse_pos):
        """Handle seed selection"""
        if self.back_button.collidepoint(mouse_pos):
            self.state = GameState.MAIN
            return

        seeds = [
            ("durian", "durian_seeds", pygame.Rect(320, 270, 160, 160)),
            ("mangosteen", "mangosteen_seeds", pygame.Rect(520, 270, 160, 160))
        ]

        for crop_type, seed_key, rect in seeds:
            if rect.collidepoint(mouse_pos) and self.inventory.get(seed_key, 0) > 0:
                crop = Crop(self.crop_types[crop_type])
                if self.selected_plot.plant(crop):
                    self.inventory[seed_key] -= 1
                    self.create_particles(self.selected_plot.rect.centerx,
                                        self.selected_plot.rect.centery, "plant")
                    self.sounds.play('plant')
                self.state = GameState.MAIN

    def handle_settings_click(self, mouse_pos):
        """Handle settings screen interactions"""
        if self.back_button.collidepoint(mouse_pos):
            self.state = GameState.MAIN
            self.save_settings()
            return

        # Check music toggle
        if self.music_toggle_rect.collidepoint(mouse_pos):
            self.music_enabled = not self.music_enabled
            if self.music_enabled:
                pygame.mixer.music.unpause()
            else:
                pygame.mixer.music.pause()

        # Check SFX toggle
        elif self.sfx_toggle_rect.collidepoint(mouse_pos):
            self.sfx_enabled = not self.sfx_enabled
            self.sounds.sfx_enabled = self.sfx_enabled

        # Check sliders
        else:
            # Music slider handle
            music_handle_rect = pygame.Rect(
                self.music_slider_rect.x + int(self.sounds.music_volume * self.music_slider_rect.width) - 15,
                self.music_slider_rect.centery - 15, 30, 30
            )
            if music_handle_rect.collidepoint(mouse_pos):
                self.dragging_music = True

            # SFX slider handle
            sfx_handle_rect = pygame.Rect(
                self.sfx_slider_rect.x + int(self.sounds.sfx_volume * self.sfx_slider_rect.width) - 15,
                self.sfx_slider_rect.centery - 15, 30, 30
            )
            if sfx_handle_rect.collidepoint(mouse_pos):
                self.dragging_sfx = True

    def save_settings(self):
        """Save sound settings to file"""
        settings = {
            'music_volume': self.sounds.music_volume,
            'sfx_volume': self.sounds.sfx_volume,
            'music_enabled': self.music_enabled,
            'sfx_enabled': self.sfx_enabled
        }
        try:
            with open('settings.json', 'w') as f:
                json.dump(settings, f)
        except:
            pass

    def load_settings(self):
        """Load sound settings from file"""
        try:
            if os.path.exists('settings.json'):
                with open('settings.json', 'r') as f:
                    settings = json.load(f)
                    self.sounds.set_music_volume(settings.get('music_volume', 0.5))
                    self.sounds.set_sfx_volume(settings.get('sfx_volume', 0.7))
                    self.music_enabled = settings.get('music_enabled', True)
                    self.sfx_enabled = settings.get('sfx_enabled', True)
                    self.sounds.sfx_enabled = self.sfx_enabled

                    if not self.music_enabled:
                        pygame.mixer.music.pause()
        except:
            pass

    def check_level_up(self):
        """Check and handle level up"""
        if self.xp >= 100:
            self.level += 1
            self.xp -= 100
            self.coins += 50 * self.level
            # Could add more rewards here

    def reset_game(self):
        """Reset game to initial state"""
        self.coins = 500
        self.level = 1
        self.xp = 0
        self.day = 1
        self.inventory = {
            "durian": 0,
            "mangosteen": 0,
            "durian_seeds": 10,
            "mangosteen_seeds": 10,
            "fertilizer": 5,
            "water_can": 1
        }
        for plot in self.plots:
            plot.is_tilled = False
            plot.crop = None
            plot.moisture = 0

    def update(self):
        """Update game state"""
        self.animation_timer += 1

        # Update plots
        for plot in self.plots:
            plot.update()

        # Day cycle (optional)
        if self.animation_timer % 3600 == 0:  # New day every minute
            self.day += 1
            self.weather = random.choice(list(Weather))

    def run(self):
        """Main game loop"""
        while self.running:
            self.handle_events()
            self.update()

            # Draw based on current state
            if self.state == GameState.START_SCREEN:
                self.draw_start_screen()
            elif self.state == GameState.MAIN:
                self.draw_main_game()
            elif self.state == GameState.SHOP:
                self.draw_shop()
            elif self.state == GameState.INVENTORY:
                self.draw_inventory()
            elif self.state == GameState.PLANTING:
                self.draw_planting_menu()
            elif self.state == GameState.SETTINGS:
                self.draw_settings()

            pygame.display.flip()
            self.clock.tick(FPS)

        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    print("""
    ===================================
    🌻 Happy Farm - Vegetables Day 🌻
    ===================================

    FULLY FIXED VERSION with all graphics created programmatically!

    🎮 Features:
    - Complete game with all assets drawn in code
    - Beautiful UI matching your design mockups
    - Farm management with durian and mangosteen crops
    - Shop system with seed purchasing
    - Inventory system matching your marketplace design
    - Settings menu with volume controls
    - Save/Load system
    - Particle effects for all actions
    - Tool modes (Water & Fertilize) with visual feedback

    🎨 Design Elements:
    - Cat mascot on start screen
    - Market stall design for shop
    - Beautiful farm plots with fence borders
    - Animated crops with growth stages
    - Gradient sky and animated clouds
    - Decorative flowers
    - All UI elements match your mockups

    🕹️ How to Play:
    1. Click on plots to till them
    2. Click tilled plots to plant seeds
    3. Use Water and Fertilize tools to help crops grow
    4. Harvest when crops show golden indicator
    5. Sell crops to earn coins
    6. Buy more seeds from the shop

    Enjoy your farming adventure!
    ===================================
    """)

    game = FarmGame()
    game.run()
