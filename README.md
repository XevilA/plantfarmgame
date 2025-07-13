# 🌻 Farm Game - Complete Pygame Code

นี่คือสคริปต์เกมปลูกผักฉบับสมบูรณ์ที่เขียนด้วย **Pygame** โดยโค้ดนี้มีความพิเศษคือ **สามารถวาดกราฟิกทั้งหมดขึ้นมาเองได้** จึงไม่จำเป็นต้องใช้ไฟล์รูปภาพจากภายนอก ทำให้หมดปัญหาเรื่อง `FileNotFoundError`

## 📝 วิธีการใช้งาน

1.  **ติดตั้ง Pygame:**
    * เปิด Terminal (หรือ Command Prompt) แล้วรันคำสั่ง:
      ```bash
      pip install pygame
      ```
2.  **บันทึกโค้ด:**
    * คัดลอกโค้ดทั้งหมดด้านล่างนี้ไปวางในไฟล์ใหม่ แล้วบันทึกเป็นไฟล์ชื่อ `game.py`
3.  **รันเกม:**
    * เปิด Terminal ในตำแหน่งที่เก็บไฟล์ `game.py` แล้วรันคำสั่ง:
      ```bash
      python game.py
      ```

---

## 🐍 โค้ดเกมฉบับสมบูรณ์

```python
import pygame
import sys
import json
import os
from enum import Enum
from datetime import datetime
import math
import random

# Initialize Pygame and mixer
pygame.init()
pygame.mixer.init()

# Constants
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 800
FPS = 60
TILE_SIZE = 120
SAVE_FILE = "farm_save.json"

# Beautiful Colors
GRASS_GREEN = (126, 200, 80); LIGHT_GREEN = (144, 238, 144); DARK_GREEN = (0, 100, 0)
SOIL_BROWN = (139, 90, 43); LIGHT_BROWN = (205, 133, 63); BROWN = (101, 67, 33)
SKY_BLUE = (135, 206, 250); GOLDEN = (255, 215, 0); YELLOW = (255, 255, 0)
CREAM = (255, 253, 208); UI_BROWN = (222, 184, 135); UI_DARK = (139, 69, 19)
WHITE = (255, 255, 255); BLACK = (0, 0, 0); GRAY = (128, 128, 128)
PURPLE = (147, 112, 219); PINK = (255, 192, 203); ORANGE = (255, 165, 0)
RED = (220, 20, 60); GREEN = (0, 255, 0)

# Game Enums
class GameState(Enum):
    START_SCREEN = 0; MAIN = 1; SHOP = 2; INVENTORY = 3; PLANTING = 4; SETTINGS = 5

class Weather(Enum):
    SUNNY = 1; RAINY = 2; CLOUDY = 3

# Core Game Classes
class CropType:
    def __init__(self, name, growth_stages, sell_price, seed_price, growth_time):
        self.name = name; self.growth_stages = growth_stages; self.sell_price = sell_price
        self.seed_price = seed_price; self.growth_time = growth_time

class Crop:
    def __init__(self, crop_type):
        self.type = crop_type; self.planted_time = None; self.growth_stage = 0
        self.watered = False; self.fertilized = False

    def plant(self): self.planted_time = pygame.time.get_ticks()
    def update(self):
        if self.planted_time:
            elapsed = pygame.time.get_ticks() - self.planted_time
            growth_multiplier = 1.5 if self.fertilized else 1.0
            if self.watered: growth_multiplier *= 1.2
            stage_time = (self.type.growth_time / self.type.growth_stages) / growth_multiplier if growth_multiplier > 0 else float('inf')
            if stage_time > 0: self.growth_stage = min(int(elapsed / stage_time), self.type.growth_stages - 1)
    def is_ready(self): return self.growth_stage >= self.type.growth_stages - 1

class FarmPlot:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE); self.crop = None
        self.is_tilled = False; self.moisture = 0

    def till(self): self.is_tilled = True
    def water(self):
        self.moisture = 100
        if self.crop: self.crop.watered = True
    def fertilize(self):
        if self.crop: self.crop.fertilized = True
    def plant(self, crop):
        if self.is_tilled and not self.crop:
            self.crop = crop; self.crop.plant(); return True
        return False
    def harvest(self):
        if self.crop and self.crop.is_ready():
            harvested = self.crop; self.crop = None; return harvested
        return None
    def update(self):
        if self.moisture > 0: self.moisture = max(0, self.moisture - 0.05)
        if self.crop: self.crop.update()

class Particle:
    def __init__(self, x, y, color, velocity, life=30, size=3):
        self.x, self.y = x, y; self.vx, self.vy = velocity; self.color = color
        self.size, self.life, self.max_life = size, life, life
    def update(self):
        self.x += self.vx; self.y += self.vy; self.vy += 0.3; self.life -= 1
    def draw(self, screen):
        if self.life > 0:
            alpha = self.life / self.max_life
            pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), int(self.size * alpha))

class ImageLoader:
    def __init__(self):
        self.images = {}; self.create_assets()
    def get(self, name, size=None):
        img = self.images.get(name, self.create_placeholder())
        return pygame.transform.scale(img, size) if size else img
    def create_placeholder(self):
        surface = pygame.Surface((64, 64), pygame.SRCALPHA)
        pygame.draw.rect(surface, PINK, (0, 0, 64, 64), border_radius=10)
        return surface
    def create_assets(self):
        self.images['cat'] = self.create_cat_mascot()
        self.images['coin'] = self.create_coin()
        self.images['market'] = self.create_market_stall()
        self.images['bag'] = self.create_bag()
        self.images['plot'] = self.create_plot()
        self.images['seedling'] = self.create_seedling()
        self.images['durian'] = self.create_durian()
        self.images['mangosteen'] = self.create_mangosteen()
        self.images['durian_seed'] = self.create_seed_packet('durian')
        self.images['mangosteen_seed'] = self.create_seed_packet('mangosteen')
        self.images['water_can'] = self.create_water_can()
        self.images['fertilizer'] = self.create_fertilizer()
    def create_cat_mascot(self):
        s = pygame.Surface((200, 200), pygame.SRCALPHA)
        pygame.draw.ellipse(s, WHITE, (50, 100, 100, 80)); pygame.draw.ellipse(s, BLACK, (50, 100, 100, 80), 3)
        pygame.draw.circle(s, WHITE, (100, 80), 50); pygame.draw.circle(s, BLACK, (100, 80), 50, 3)
        pygame.draw.polygon(s, WHITE, [(60, 50), (50, 20), (80, 40)]); pygame.draw.polygon(s, BLACK, [(60, 50), (50, 20), (80, 40)], 3)
        pygame.draw.polygon(s, WHITE, [(120, 40), (150, 20), (140, 50)]); pygame.draw.polygon(s, BLACK, [(120, 40), (150, 20), (140, 50)], 3)
        pygame.draw.circle(s, BLACK, (80, 75), 8); pygame.draw.circle(s, BLACK, (120, 75), 8)
        pygame.draw.circle(s, WHITE, (82, 73), 3); pygame.draw.circle(s, WHITE, (122, 73), 3)
        pygame.draw.polygon(s, PINK, [(100, 85), (95, 95), (105, 95)])
        pygame.draw.arc(s, BLACK, (85, 85, 15, 15), 0, math.pi, 2); pygame.draw.arc(s, BLACK, (100, 85, 15, 15), 0, math.pi, 2)
        pygame.draw.arc(s, WHITE, (140, 120, 60, 60), -math.pi/4, math.pi/2, 20); pygame.draw.arc(s, BLACK, (140, 120, 60, 60), -math.pi/4, math.pi/2, 3)
        return s
    def create_coin(self):
        s = pygame.Surface((64, 64), pygame.SRCALPHA)
        pygame.draw.circle(s, GOLDEN, (32, 32), 30); pygame.draw.circle(s, (218, 165, 32), (32, 32), 30, 3)
        pygame.draw.circle(s, (218, 165, 32), (32, 32), 24, 2)
        star = [(32 + (15 if i%2==0 else 8) * math.cos(i*math.pi/5-math.pi/2), 32 + (15 if i%2==0 else 8) * math.sin(i*math.pi/5-math.pi/2)) for i in range(10)]
        pygame.draw.polygon(s, (218, 165, 32), star)
        return s
    def create_market_stall(self):
        s = pygame.Surface((200, 200), pygame.SRCALPHA)
        pygame.draw.rect(s, BROWN, (30, 60, 20, 120)); pygame.draw.rect(s, BROWN, (150, 60, 20, 120))
        pygame.draw.rect(s, BLACK, (30, 60, 20, 120), 2); pygame.draw.rect(s, BLACK, (150, 60, 20, 120), 2)
        pygame.draw.rect(s, UI_BROWN, (20, 120, 160, 60)); pygame.draw.rect(s, BLACK, (20, 120, 160, 60), 3)
        for i in range(4):
            color = YELLOW if i % 2 == 0 else WHITE
            pygame.draw.arc(s, color, (20 + i * 40, 20, 40, 80), 0, math.pi, 30)
            pygame.draw.arc(s, BLACK, (20 + i * 40, 20, 40, 80), 0, math.pi, 3)
        pygame.draw.rect(s, UI_BROWN, (60, 30, 80, 40)); pygame.draw.rect(s, BLACK, (60, 30, 80, 40), 2)
        return s
    def create_bag(self):
        s = pygame.Surface((80, 80), pygame.SRCALPHA)
        pygame.draw.ellipse(s, BROWN, (10, 30, 60, 45)); pygame.draw.ellipse(s, (139, 69, 19), (10, 30, 60, 45), 3)
        pygame.draw.arc(s, BROWN, (20, 15, 40, 30), 0, math.pi, 8); pygame.draw.arc(s, (139, 69, 19), (20, 15, 40, 30), 0, math.pi, 3)
        pygame.draw.arc(s, (160, 82, 45), (10, 25, 60, 30), 0, math.pi, 20); pygame.draw.arc(s, (139, 69, 19), (10, 25, 60, 30), 0, math.pi, 3)
        pygame.draw.rect(s, GOLDEN, (35, 35, 10, 8)); pygame.draw.rect(s, BLACK, (35, 35, 10, 8), 1)
        return s
    def create_plot(self):
        s = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA); fence_color = (160, 82, 45)
        for i in range(5):
            x = i * (TILE_SIZE // 4); pygame.draw.rect(s, fence_color, (x, 0, 8, 20)); pygame.draw.rect(s, fence_color, (x, TILE_SIZE - 20, 8, 20))
            pygame.draw.rect(s, fence_color, (0, x, 20, 8)); pygame.draw.rect(s, fence_color, (TILE_SIZE - 20, x, 20, 8))
        pygame.draw.rect(s, SOIL_BROWN, (20, 20, TILE_SIZE - 40, TILE_SIZE - 40))
        for i in range(3):
            for j in range(3): pygame.draw.circle(s, LIGHT_BROWN, (30 + i * 25, 30 + j * 25), 3)
        return s
    def create_seedling(self):
        s = pygame.Surface((60, 60), pygame.SRCALPHA); pygame.draw.rect(s, DARK_GREEN, (28, 30, 4, 20))
        pygame.draw.ellipse(s, LIGHT_GREEN, (15, 15, 20, 25)); pygame.draw.ellipse(s, LIGHT_GREEN, (25, 15, 20, 25))
        pygame.draw.ellipse(s, DARK_GREEN, (15, 15, 20, 25), 2); pygame.draw.ellipse(s, DARK_GREEN, (25, 15, 20, 25), 2)
        pygame.draw.ellipse(s, SOIL_BROWN, (10, 45, 40, 15))
        return s
    def create_durian(self):
        s = pygame.Surface((80, 80), pygame.SRCALPHA)
        pygame.draw.ellipse(s, (126, 200, 80), (10, 15, 60, 55))
        for i in range(8):
            for j in range(6):
                if (i + j) % 2 == 0: pygame.draw.polygon(s, DARK_GREEN, [(15+i*8, 20+j*8), (12+i*8, 25+j*8), (18+i*8, 25+j*8)])
        pygame.draw.rect(s, BROWN, (38, 10, 4, 10)); pygame.draw.ellipse(s, BLACK, (10, 15, 60, 55), 2)
        return s
    def create_mangosteen(self):
        s = pygame.Surface((70, 70), pygame.SRCALPHA)
        pygame.draw.circle(s, PURPLE, (35, 40), 28); pygame.draw.circle(s, (128, 0, 128), (35, 40), 28, 3)
        pygame.draw.circle(s, DARK_GREEN, (35, 15), 12)
        for i in range(6):
            angle = i * math.pi/3; x = 35 + 10 * math.cos(angle); y = 15 + 10 * math.sin(angle)
            pygame.draw.circle(s, LIGHT_GREEN, (int(x), int(y)), 5)
        pygame.draw.ellipse(s, (200, 150, 255, 100), (25, 25, 15, 20))
        return s
    def create_seed_packet(self, crop_type):
        s = pygame.Surface((60, 80), pygame.SRCALPHA)
        pygame.draw.rect(s, CREAM, (5, 5, 50, 70)); pygame.draw.rect(s, UI_DARK, (5, 5, 50, 70), 2)
        if crop_type == 'durian':
            img = self.images.get('durian', self.create_placeholder())
            s.blit(pygame.transform.scale(img, (30,30)), (15, 25))
        else:
            img = self.images.get('mangosteen', self.create_placeholder())
            s.blit(pygame.transform.scale(img, (30,30)), (15, 25))
        for i in range(3): pygame.draw.ellipse(s, BROWN, (15 + i*10, 60, 6, 8))
        return s
    def create_water_can(self):
        s = pygame.Surface((80, 80), pygame.SRCALPHA)
        pygame.draw.rect(s, SKY_BLUE, (20, 30, 40, 35)); pygame.draw.rect(s, (0, 100, 200), (20, 30, 40, 35), 3)
        pygame.draw.polygon(s, SKY_BLUE, [(60, 35), (70, 25), (75, 30), (60, 45)]); pygame.draw.polygon(s, (0, 100, 200), [(60, 35), (70, 25), (75, 30), (60, 45)], 2)
        pygame.draw.arc(s, SKY_BLUE, (5, 20, 30, 40), math.pi/2, 3*math.pi/2, 5); pygame.draw.arc(s, (0, 100, 200), (5, 20, 30, 40), math.pi/2, 3*math.pi/2, 2)
        return s
    def create_fertilizer(self):
        s = pygame.Surface((60, 70), pygame.SRCALPHA); pygame.draw.rect(s, BROWN, (10, 15, 40, 50)); pygame.draw.rect(s, (101, 67, 33), (10, 15, 40, 50), 2)
        pygame.draw.rect(s, GREEN, (28, 32, 4, 8)); pygame.draw.circle(s, GREEN, (25, 30), 5); pygame.draw.circle(s, GREEN, (35, 30), 5)
        return s

class SoundManager:
    def play(self, sound_name): pass

class FarmGame:
    def __init__(self):
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("🌻 Happy Farm - Vegetables Day 🌻")
        self.clock = pygame.time.Clock(); self.running = True; self.state = GameState.START_SCREEN
        self.images = ImageLoader(); self.sounds = SoundManager()
        self.font_huge = pygame.font.Font(None, 96); self.font_large = pygame.font.Font(None, 72)
        self.font_medium = pygame.font.Font(None, 48); self.font_small = pygame.font.Font(None, 32)
        self.reset_game(); self.create_ui_elements(); self.load_game()

    def create_ui_elements(self):
        self.new_game_button = pygame.Rect(WINDOW_WIDTH//2-200, 450, 400, 80)
        self.continue_button = pygame.Rect(WINDOW_WIDTH//2-200, 550, 400, 80)
        self.back_button = pygame.Rect(50, 700, 150, 60)
        self.shop_button = pygame.Rect(50, 50, 180, 70)
        self.inventory_button = pygame.Rect(50, 130, 180, 70)
        self.save_button = pygame.Rect(1050, 50, 150, 60)

    def load_game(self):
        if not os.path.exists(SAVE_FILE): return
        try:
            with open(SAVE_FILE, 'r') as f:
                data = json.load(f)
                self.coins = data.get('coins', 500)
                self.inventory = data.get('inventory', self.inventory)
                plot_data = data.get('plots', [])
                for i, p_info in enumerate(plot_data):
                    if i < len(self.plots):
                        self.plots[i].is_tilled = p_info.get('tilled', False)
                        if p_info.get('has_crop'):
                            c_type_name = p_info.get('crop_type')
                            c_type = self.crop_types.get(c_type_name)
                            if c_type: self.plots[i].crop = Crop(c_type)
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Save file corrupted or invalid, starting new game. Error: {e}")
            if os.path.exists(SAVE_FILE): os.remove(SAVE_FILE)
            self.reset_game()

    def save_game(self):
        plot_data = []
        for p in self.plots:
            p_info = {'tilled': p.is_tilled, 'has_crop': p.crop is not None}
            if p.crop: p_info['crop_type'] = p.crop.type.name.lower()
            plot_data.append(p_info)
        save_data = {'coins': self.coins, 'inventory': self.inventory, 'plots': plot_data}
        with open(SAVE_FILE, 'w') as f: json.dump(save_data, f, indent=2)
        print("Game Saved!")

    def reset_game(self):
        self.coins = 500
        self.inventory = {"durian_seeds": 10, "mangosteen_seeds": 10, "durian": 0, "mangosteen": 0}
        self.plots = [FarmPlot(320+j*(TILE_SIZE+15), 200+i*(TILE_SIZE+15)) for i in range(3) for j in range(5)]
        self.crop_types = {"durian": CropType("Durian", 3, 100, 30, 10000), "mangosteen": CropType("Mangosteen", 3, 60, 20, 7000)}
        self.selected_plot = None

    def draw_background(self):
        self.screen.fill(SKY_BLUE)
        pygame.draw.rect(self.screen, GRASS_GREEN, (0, WINDOW_HEIGHT//2, WINDOW_WIDTH, WINDOW_HEIGHT//2))

    def draw_text(self, text, font, color, center):
        surf = font.render(text, True, color)
        rect = surf.get_rect(center=center); self.screen.blit(surf, rect)

    def draw_button(self, rect, text, base_color, hover_color, font):
        mouse_pos = pygame.mouse.get_pos()
        color = hover_color if rect.collidepoint(mouse_pos) else base_color
        pygame.draw.rect(self.screen, color, rect, border_radius=15)
        pygame.draw.rect(self.screen, BLACK, rect, 3, border_radius=15)
        self.draw_text(text, font, WHITE, rect.center)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT: self.running = False; self.save_game()
            if event.type == pygame.MOUSEBUTTONDOWN:
                pos = event.pos
                if self.state == GameState.START_SCREEN:
                    if self.new_game_button.collidepoint(pos): self.reset_game(); self.state = GameState.MAIN
                    if self.continue_button.collidepoint(pos) and os.path.exists(SAVE_FILE): self.load_game(); self.state = GameState.MAIN
                elif self.state == GameState.MAIN:
                    if self.shop_button.collidepoint(pos): self.state = GameState.SHOP
                    if self.inventory_button.collidepoint(pos): self.state = GameState.INVENTORY
                    if self.save_button.collidepoint(pos): self.save_game()
                    for plot in self.plots:
                        if plot.rect.collidepoint(pos): self.handle_plot_click(plot)
                elif self.state in [GameState.SHOP, GameState.INVENTORY, GameState.PLANTING]:
                    if self.back_button.collidepoint(pos): self.state = GameState.MAIN
                    # Add shop/inventory click logic here

    def handle_plot_click(self, plot):
        if not plot.is_tilled: plot.till()
        elif plot.crop and plot.crop.is_ready():
            harvested = plot.harvest()
            self.inventory[harvested.type.name.lower()] += 1
            self.coins += harvested.type.sell_price
        elif not plot.crop: self.state = GameState.PLANTING; self.selected_plot = plot

    def update(self):
        for plot in self.plots: plot.update()

    def draw(self):
        self.draw_background()
        if self.state == GameState.START_SCREEN:
            self.draw_text("VEGETABLES DAY", self.font_huge, GOLDEN, (WINDOW_WIDTH//2, 150))
            self.screen.blit(self.images.get('cat', (200, 200)), (WINDOW_WIDTH//2-100, 250))
            self.draw_button(self.new_game_button, "🌱 New Game", LIGHT_GREEN, DARK_GREEN, self.font_medium)
            if os.path.exists(SAVE_FILE): self.draw_button(self.continue_button, "📂 Continue", ORANGE, UI_DARK, self.font_medium)
        elif self.state == GameState.MAIN:
            for plot in self.plots:
                if plot.is_tilled:
                    self.screen.blit(self.images.get('plot', (TILE_SIZE, TILE_SIZE)), plot.rect)
                    if plot.crop:
                        img_name = 'seedling' if not plot.crop.is_ready() else plot.crop.type.name.lower()
                        img = self.images.get(img_name)
                        size = 40 + plot.crop.growth_stage * 15
                        self.screen.blit(pygame.transform.scale(img, (size, size)), (plot.rect.centerx-size//2, plot.rect.centery-size//2))
                else: pygame.draw.rect(self.screen, DARK_GREEN, plot.rect, 5, 10)
            self.draw_button(self.shop_button, "🛒 Shop", ORANGE, UI_DARK, self.font_small)
            self.draw_button(self.inventory_button, "🎒 Inventory", PURPLE, (128,0,128), self.font_small)
            self.draw_button(self.save_button, "💾 Save", LIGHT_GREEN, DARK_GREEN, self.font_small)
            self.draw_text(f"🪙 {self.coins}", self.font_large, GOLDEN, (WINDOW_WIDTH//2, 50))
        elif self.state == GameState.SHOP:
            self.draw_text("SHOP", self.font_large, BLACK, (WINDOW_WIDTH//2, 100))
            self.draw_button(self.back_button, "← Back", RED, (139,0,0), self.font_small)
        elif self.state == GameState.INVENTORY:
            self.draw_text("INVENTORY", self.font_large, BLACK, (WINDOW_WIDTH//2, 100))
            y = 200
            for item, count in self.inventory.items():
                if count > 0: self.draw_text(f"{item.replace('_',' ').title()}: {count}", self.font_medium, BLACK, (WINDOW_WIDTH//2, y)); y += 50
            self.draw_button(self.back_button, "← Back", RED, (139,0,0), self.font_small)
        elif self.state == GameState.PLANTING:
            self.draw_text("Choose a Seed", self.font_large, BLACK, (WINDOW_WIDTH//2, 100))
            # Seed selection UI would go here
            self.draw_button(self.back_button, "← Back", RED, (139,0,0), self.font_small)
        pygame.display.flip()

    def run(self):
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = FarmGame()
    game.run()

```
