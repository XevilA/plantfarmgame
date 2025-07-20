import os
import json
import random
import sys
import pygame
import math
import time
from State import GameState
from Weather import Weather
from particle import Particle
from crop import Crop
from CPT import CropType
from music import SoundManager
from datetime import datetime
from enum import Enum
from Plot import FarmPlot
from config import TILE_SIZE
from image_loader import ImageLoader


pygame.init()
pygame.mixer.init()



WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 800
FPS = 60

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
LIGHT_GRAY = (200, 200, 200)
DARK_GRAY = (100, 100, 100)



###################################################################################################


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

        # Enhanced inventory with categories
        self.inventory = {
            "crops": {
                "durian": 0,
                "mangosteen": 0
            },
            "seeds": {
                "durian_seeds": 10,
                "mangosteen_seeds": 10
            },
            "tools": {
                "fertilizer": 10,
                "water_can": 10
            }
        }

        # Inventory UI state
        self.inventory_tab = "crops"  # crops, seeds, tools
        self.selected_item = None
        self.item_hover = None
        
        # Inventory selling
        self.sell_mode = False
        self.sell_quantity = 1

        # Crop types
        self.crop_types = {
            "durian": CropType("Durian", 3, 100, 30, 10000),
            "mangosteen": CropType("Mangosteen", 3, 60, 20, 7000)
            #(ชื่อพืช, ระยะการเติบโต, ราคาซื้อ, XP ที่ได้, ราคาขาย)
        }

        # Create farm plots (4x4 grid)
        self.plots = []
        start_x = 320#ตำแหน่งบนจอของ มุมซ้ายบนของแปลงแรก
        start_y = 200
        spacing = TILE_SIZE + 30#ระยะห่างระหว่างแต่ละแปลง  = ขนาดแปลง (TILE_SIZE) + ช่องว่าง 30 px
        for i in range(4):#loopแปลง
            for j in range(4):
                x = start_x + j * spacing
                y = start_y + i * spacing
                self.plots.append(FarmPlot(x, y))

        self.sounds.play("click")

        # Particlesist ว่าง เพื่อเก็บวัตถุ Particle ทั้งหมดในเกม ณ ขณะนั้น
        self.particles = []

        # Selected plot for planting
        self.selected_plot = None

        # Decorative elements เมฆสุดเท่ที่ฉาก
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

        # Settings screen elements วาดหน้าตั้งค่าตรงเพลง
        self.music_slider_rect = pygame.Rect(570, 250, 230, 20)
        self.sfx_slider_rect = pygame.Rect(570, 350, 230, 20)
        self.music_slider_pos = self.music_slider_rect.x + int(self.sounds.music_volume * 300)
        self.sfx_slider_pos = self.sfx_slider_rect.x + int(self.sounds.sfx_volume * 300)
        self.dragging_music = False
        self.dragging_sfx = False
        self.music_toggle_rect = pygame.Rect(890, 240, 100, 40)
        self.sfx_toggle_rect = pygame.Rect(890, 340, 100, 40)

        # UI Elementsปุ่ม
        self.create_ui_elements()

        # Tool modesปุ๋ยน้ำ ถ้ากดใช้จะทรู
        self.watering_mode = False
        self.fertilizing_mode = False

        # Load saved game and settings
        self.load_settings()
        self.load_game()

    def create_ui_elements(self):
        """Create all UI buttons and elements"""
        # Main screen buttons
        self.shop_button = pygame.Rect(50, 250, 180, 70)
        self.inventory_button = pygame.Rect(50, 340, 180, 70)
        self.save_button = pygame.Rect(1050, 50, 150, 60)
        self.settings_button = pygame.Rect(1050, 120, 150, 60)

        # Tool buttons
        self.water_button = pygame.Rect(50, 430, 180, 60)
        self.fertilize_button = pygame.Rect(50, 510, 180, 60)

        # Back button (universal)
        self.back_button = pygame.Rect(50, 700, 150, 60)

        # Start screen buttons
        self.new_game_button = pygame.Rect(WINDOW_WIDTH//2 - 200, 450, 400, 80)
        self.continue_button = pygame.Rect(WINDOW_WIDTH//2 - 200, 550, 400, 80)#กลางจอ

        # Shop items with better layoutร้านค้า
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

    def get_item_from_inventory(self, key):
        """Get item count from nested inventory structure"""
        for category in self.inventory.values():
            if key in category:
                return category[key]
        return 0
    
    def set_item_in_inventory(self, key, value):
        """Set item count in nested inventory structure"""
        for category in self.inventory.values():
            if key in category:
                category[key] = value
                return
    
    def add_item_to_inventory(self, key, amount):
        """Add item to nested inventory structure"""
        for category in self.inventory.values():
            if key in category:
                category[key] += amount
                return

    def load_game(self):
        """Load saved game data"""
        try:
            if os.path.exists(SAVE_FILE):#ตรวจสอบว่ามีไฟล์เซฟอยู่หรือไม่
                with open(SAVE_FILE, 'r') as f:
                    data = json.load(f)#เก็บข้อมูลjson
                    self.coins = data.get('coins', 500)
                    self.level = data.get('level', 1)
                    self.xp = data.get('xp', 0)
                    self.day = data.get('day', 1)
                    
                    # Convert old inventory format to new format if needed
                    saved_inventory = data.get('inventory', {})
                    if 'crops' in saved_inventory:
                        self.inventory = saved_inventory
                    else:
                        # Old format - convert to new
                        self.inventory = {
                            "crops": {
                                "durian": saved_inventory.get("durian", 0),
                                "mangosteen": saved_inventory.get("mangosteen", 0)
                            },
                            "seeds": {
                                "durian_seeds": saved_inventory.get("durian_seeds", 10),
                                "mangosteen_seeds": saved_inventory.get("mangosteen_seeds", 10)
                            },
                            "tools": {
                                "fertilizer": saved_inventory.get("fertilizer", 10),
                                "water_can": saved_inventory.get("water_can", 10)
                            }
                        }

                    # Load plots
                    plot_data = data.get('plots', [])
                    for i, plot_info in enumerate(plot_data):#loop list
                        if i < len(self.plots):    # ตรวจสอบว่า index ไม่เกินจำนวนแปลงที่มีอยู่ใน self.plots
                            self.plots[i].is_tilled = plot_info.get('tilled', False)#เช็คไถ
                            self.plots[i].moisture = plot_info.get('moisture', 0)#เช็คชื้น

                            if plot_info.get('has_crop'):#เก็บผัก
                                crop_type = plot_info.get('crop_type')#เรียกชื่อผัก
                                if crop_type in self.crop_types:
                                    crop = Crop(self.crop_types[crop_type])
                                    crop.growth_stage = plot_info.get('growth_stage', 0)  # โหลดสถานะการเติบโตของพืชจากเซฟ เช่น โตถึงขั้นไหนแล้ว (stage 0 - 3)
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
            'timestamp':datetime .now().isoformat()
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
        for i in range(WINDOW_HEIGHT // 2):#loopครึ่งจอ
            ratio = i / (WINDOW_HEIGHT // 2)#ไล่สี
            r = int(135 + (255 - 135) * ratio)
            g = int(206 + (255 - 206) * ratio)
            b = int(250 + (255 - 250) * ratio)#ไล่สี
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
            f"Level: {self.level}",
            f"XP: {self.xp}/100",
            f"Day: {self.day}",
            f"{self.weather.name.title()}"
        ]

        y_offset = 70
        for stat in stats:# ข้อความหลายบรรทัดแนวตั้ง 
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
            # Glowing effectบิกเก็บผักได้ 
            glow_size = 15 + math.sin(self.animation_timer * 0.01) * 5
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
            (self.shop_button, " Shop", ORANGE),
            (self.inventory_button, " Inventory", PURPLE),
            (self.save_button, " Save", LIGHT_GREEN),
            (self.settings_button, " Settings", UI_BROWN),
            (self.water_button, " Water", SKY_BLUE),
            (self.fertilize_button, " Fertilize", DARK_GREEN)
        ]

        for button, text, color in buttons:
            # Button shadow เงาปุ่มสวยๆ
            shadow = button.copy()
            shadow.x += 3
            shadow.y += 3
            pygame.draw.rect(self.screen, (0, 0, 0, 100), shadow, border_radius=15)

            # Highlight if tool is active กรอบเหลืองปุ่มที่ใช้
            if (text == " Water" and self.watering_mode) or \
               (text == " Fertilize" and self.fertilizing_mode):
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

        # Draw particlesสร้ามสำเนา ob ตอบลบจะได้ไม่รวน
        for particle in self.particles[:]:
            particle.update()
            particle.draw(self.screen)
            if particle.life <= 0:
                self.particles.remove(particle)

        # Draw active tool cursor ตอนกดปุ๋ยกับน้ำ
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
        """Enhanced inventory screen with tabs and selling"""
        self.draw_background()

        # Inventory window
        inv_bg = pygame.Rect(150, 50, 980, 650)
        pygame.draw.rect(self.screen, UI_BROWN, inv_bg, border_radius=30)
        pygame.draw.rect(self.screen, BLACK, inv_bg, 5, border_radius=30)

        # Title bar
        title_bg = pygame.Rect(170, 70, 940, 80)
        pygame.draw.rect(self.screen, DARK_GREEN, title_bg, border_radius=20)

        # Title
        title = self.font_large.render("INVENTORY", True, WHITE)
        self.screen.blit(title, (WINDOW_WIDTH//2 - title.get_width()//2, 85))

        # Tab buttons
        tabs = [
            ("🌾 Crops", "crops"),
            ("🌱 Seeds", "seeds"),
            ("🛠️ Tools", "tools")
        ]

        tab_x = 200
        for tab_text, tab_key in tabs:
            tab_rect = pygame.Rect(tab_x, 160, 200, 50)
            is_active = self.inventory_tab == tab_key
            tab_color = LIGHT_GREEN if is_active else CREAM
            
            # Shadow for active tab
            if is_active:
                shadow = tab_rect.copy()
                shadow.y += 2
                pygame.draw.rect(self.screen, (0, 0, 0, 50), shadow, border_radius=15)
            
            pygame.draw.rect(self.screen, tab_color, tab_rect, border_radius=15)
            pygame.draw.rect(self.screen, BLACK, tab_rect, 2, border_radius=15)

            text = self.font_small.render(tab_text, True, BLACK)
            self.screen.blit(text, (tab_rect.centerx - text.get_width()//2,
                                   tab_rect.centery - text.get_height()//2))
            tab_x += 220

        # Sell mode toggle
        sell_toggle_rect = pygame.Rect(850, 160, 120, 50)
        sell_color = RED if self.sell_mode else GRAY
        pygame.draw.rect(self.screen, sell_color, sell_toggle_rect, border_radius=15)
        pygame.draw.rect(self.screen, BLACK, sell_toggle_rect, 2, border_radius=15)
        sell_text = self.font_small.render("💰 Sell", True, WHITE)
        self.screen.blit(sell_text, (sell_toggle_rect.centerx - sell_text.get_width()//2,
                                     sell_toggle_rect.centery - sell_text.get_height()//2))

        # Items grid
        self.draw_inventory_items()

        # Selected item details
        if self.selected_item:
            self.draw_item_details()

        # Back button
        self.draw_back_button()

    def draw_inventory_items(self):
        """Draw items in grid layout"""
        # Get current tab items
        current_items = self.inventory.get(self.inventory_tab, {})
        
        # Grid settings
        grid_x = 200
        grid_y = 230
        item_size = 100
        padding = 20
        cols = 8
        
        # Item backgrounds
        item_index = 0
        for item_key, count in current_items.items():
            if count > 0:  # Only show items we have
                row = item_index // cols
                col = item_index % cols
                
                x = grid_x + col * (item_size + padding)
                y = grid_y + row * (item_size + padding)
                
                item_rect = pygame.Rect(x, y, item_size, item_size)
                
                # Hover effect
                mouse_pos = pygame.mouse.get_pos()
                is_hovered = item_rect.collidepoint(mouse_pos)
                
                # Selected highlight
                is_selected = self.selected_item == item_key
                
                # Draw item slot
                if is_selected:
                    pygame.draw.rect(self.screen, GOLDEN, item_rect.inflate(6, 6), border_radius=15)
                elif is_hovered:
                    pygame.draw.rect(self.screen, LIGHT_GRAY, item_rect.inflate(4, 4), border_radius=15)
                
                pygame.draw.rect(self.screen, WHITE, item_rect, border_radius=15)
                pygame.draw.rect(self.screen, BLACK, item_rect, 2, border_radius=15)
                
                # Draw item icon
                icon_name = item_key.replace('_seeds', '_seed').replace('water_can', 'water_can')
                if icon_name.endswith('_seed'):
                    icon_name = icon_name
                else:
                    icon_name = item_key
                    
                icon = self.images.get(icon_name, (60, 60))
                icon_rect = icon.get_rect(center=item_rect.center)
                icon_rect.y -= 10
                self.screen.blit(icon, icon_rect)
                
                # Draw count
                count_bg = pygame.Rect(x + item_size - 35, y + item_size - 30, 30, 25)
                pygame.draw.ellipse(self.screen, BLACK, count_bg)
                pygame.draw.ellipse(self.screen, GOLDEN, count_bg.inflate(-4, -4))
                
                count_text = self.font_tiny.render(str(count), True, BLACK)
                count_rect = count_text.get_rect(center=count_bg.center)
                self.screen.blit(count_text, count_rect)
                
                # Store rect for click detection
                if not hasattr(self, 'item_rects'):
                    self.item_rects = {}
                self.item_rects[item_key] = item_rect
                
                item_index += 1

    def draw_item_details(self):
        """Draw detailed info for selected item"""
        if not self.selected_item:
            return
            
        # Detail panel
        detail_rect = pygame.Rect(200, 480, 760, 180)
        pygame.draw.rect(self.screen, CREAM, detail_rect, border_radius=20)
        pygame.draw.rect(self.screen, BLACK, detail_rect, 3, border_radius=20)
        
        # Item icon
        icon_name = self.selected_item.replace('_seeds', '_seed')
        icon = self.images.get(icon_name, (80, 80))
        self.screen.blit(icon, (220, 500))
        
        # Item name
        item_display_name = self.selected_item.replace('_', ' ').title()
        name_text = self.font_medium.render(item_display_name, True, BLACK)
        self.screen.blit(name_text, (320, 510))
        
        # Get item info
        count = self.get_item_from_inventory(self.selected_item)
        
        # Description based on item type
        if self.inventory_tab == "crops":
            if self.selected_item == "durian":
                desc = "A spiky tropical fruit. Sells for $100"
                sell_price = 100
            else:
                desc = "A sweet purple fruit. Sells for $60"
                sell_price = 60
                
            desc_text = self.font_small.render(desc, True, DARK_GRAY)
            self.screen.blit(desc_text, (320, 550))
            
            # Quantity and sell controls
            if self.sell_mode:
                # Quantity selector
                qty_rect = pygame.Rect(320, 590, 200, 40)
                pygame.draw.rect(self.screen, WHITE, qty_rect, border_radius=10)
                pygame.draw.rect(self.screen, BLACK, qty_rect, 2, border_radius=10)
                
                # - button
                minus_btn = pygame.Rect(330, 595, 30, 30)
                pygame.draw.rect(self.screen, RED, minus_btn, border_radius=5)
                minus_text = self.font_medium.render("-", True, WHITE)
                self.screen.blit(minus_text, (minus_btn.centerx - minus_text.get_width()//2,
                                             minus_btn.centery - minus_text.get_height()//2 - 3))
                
                # Quantity display
                qty_text = self.font_small.render(str(self.sell_quantity), True, BLACK)
                self.screen.blit(qty_text, (qty_rect.centerx - qty_text.get_width()//2,
                                           qty_rect.centery - qty_text.get_height()//2))
                
                # + button
                plus_btn = pygame.Rect(480, 595, 30, 30)
                pygame.draw.rect(self.screen, GREEN, plus_btn, border_radius=5)
                plus_text = self.font_medium.render("+", True, WHITE)
                self.screen.blit(plus_text, (plus_btn.centerx - plus_text.get_width()//2,
                                           plus_btn.centery - plus_text.get_height()//2 - 3))
                
                # Sell button
                sell_btn = pygame.Rect(550, 590, 150, 40)
                sell_value = sell_price * self.sell_quantity
                pygame.draw.rect(self.screen, GOLDEN, sell_btn, border_radius=10)
                pygame.draw.rect(self.screen, BLACK, sell_btn, 2, border_radius=10)
                sell_btn_text = self.font_small.render(f"Sell for ${sell_value}", True, BLACK)
                self.screen.blit(sell_btn_text, (sell_btn.centerx - sell_btn_text.get_width()//2,
                                                sell_btn.centery - sell_btn_text.get_height()//2))
                
                # Store button rects
                self.minus_btn = minus_btn
                self.plus_btn = plus_btn
                self.sell_btn = sell_btn
                
        elif self.inventory_tab == "seeds":
            desc = f"Plant these to grow {self.selected_item.replace('_seeds', '')}!"
            desc_text = self.font_small.render(desc, True, DARK_GRAY)
            self.screen.blit(desc_text, (320, 550))
            
            stock_text = self.font_small.render(f"In stock: {count}", True, BLACK)
            self.screen.blit(stock_text, (320, 590))
            
        elif self.inventory_tab == "tools":
            if self.selected_item == "fertilizer":
                desc = "Makes crops grow 50% faster!"
            else:
                desc = "Essential for watering your crops"
                
            desc_text = self.font_small.render(desc, True, DARK_GRAY)
            self.screen.blit(desc_text, (320, 550))
            
            stock_text = self.font_small.render(f"Remaining: {count}", True, BLACK)
            self.screen.blit(stock_text, (320, 590))

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
            count = self.get_item_from_inventory(key)

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
            " Drag sliders to adjust volume",
            " Click ON/OFF to toggle sounds",
            " Settings are saved automatically"
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
        """Handle all game eventsไว้จัดการทุกสถานการ"""
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
                    self.handle_inventory_click(mouse_pos)

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
            self.selected_item = None
            self.sell_mode = False
            self.sell_quantity = 1
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
                    if plot.crop and self.get_item_from_inventory("fertilizer") > 0:
                        plot.fertilize()
                        self.add_item_to_inventory("fertilizer", -1)
                        self.create_particles(plot.rect.centerx, plot.rect.centery, "fertilize")
                        self.sounds.play('plant')

                elif not plot.is_tilled:
                    plot.till()
                    self.sounds.play('plant')

                elif plot.crop and plot.crop.is_ready():
                    harvested = plot.harvest()
                    if harvested:
                        self.add_item_to_inventory(harvested.type.name.lower(), 1)
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
                self.add_item_to_inventory(item['key'], 1)
                self.create_particles(mouse_pos[0], mouse_pos[1], "coin")
                self.sounds.play('coin')

    def handle_inventory_click(self, mouse_pos):
        """Handle inventory screen interactions"""
        if self.back_button.collidepoint(mouse_pos):
            self.state = GameState.MAIN
            return
        
        # Check tab clicks
        tab_x = 200
        for tab_text, tab_key in [("🌾 Crops", "crops"), ("🌱 Seeds", "seeds"), ("🛠️ Tools", "tools")]:
            tab_rect = pygame.Rect(tab_x, 160, 200, 50)
            if tab_rect.collidepoint(mouse_pos):
                self.inventory_tab = tab_key
                self.selected_item = None
                self.sell_quantity = 1
                return
            tab_x += 220
        
        # Check sell mode toggle
        sell_toggle_rect = pygame.Rect(850, 160, 120, 50)
        if sell_toggle_rect.collidepoint(mouse_pos):
            self.sell_mode = not self.sell_mode
            if not self.sell_mode:
                self.sell_quantity = 1
            return
        
        # Check item clicks
        if hasattr(self, 'item_rects'):
            for item_key, item_rect in self.item_rects.items():
                if item_rect.collidepoint(mouse_pos):
                    self.selected_item = item_key
                    self.sell_quantity = 1
                    return
        
        # Check sell controls
        if self.selected_item and self.sell_mode and self.inventory_tab == "crops":
            if hasattr(self, 'minus_btn') and self.minus_btn.collidepoint(mouse_pos):
                self.sell_quantity = max(1, self.sell_quantity - 1)
            elif hasattr(self, 'plus_btn') and self.plus_btn.collidepoint(mouse_pos):
                max_qty = self.get_item_from_inventory(self.selected_item)
                self.sell_quantity = min(max_qty, self.sell_quantity + 1)
            elif hasattr(self, 'sell_btn') and self.sell_btn.collidepoint(mouse_pos):
                # Sell items
                count = self.get_item_from_inventory(self.selected_item)
                if count >= self.sell_quantity:
                    if self.selected_item == "durian":
                        sell_price = 100
                    else:
                        sell_price = 60
                    
                    total_value = sell_price * self.sell_quantity
                    self.add_item_to_inventory(self.selected_item, -self.sell_quantity)
                    self.coins += total_value
                    self.create_particles(mouse_pos[0], mouse_pos[1], "coin")
                    self.sounds.play('coin')
                    
                    # Reset if sold all
                    if self.get_item_from_inventory(self.selected_item) == 0:
                        self.selected_item = None
                        self.sell_quantity = 1

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
            if rect.collidepoint(mouse_pos) and self.get_item_from_inventory(seed_key) > 0:
                crop = Crop(self.crop_types[crop_type])
                if self.selected_plot.plant(crop):
                    self.add_item_to_inventory(seed_key, -1)
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
            "crops": {
                "durian": 0,
                "mangosteen": 0
            },
            "seeds": {
                "durian_seeds": 10,
                "mangosteen_seeds": 10
            },
            "tools": {
                "fertilizer": 10,
                "water_can": 10
            }
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
    game = FarmGame()
    game.run()
