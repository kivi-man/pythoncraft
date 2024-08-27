from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
import noise
import random
import psutil
import time

app = Ursina()

grass_texture = load_texture("Assets/Textures/Grass_Block.png")
stone_texture = load_texture("Assets/Textures/Stone_Block.png")
brick_texture = load_texture("Assets/Textures/Brick_Block.png")
dirt_texture = load_texture("Assets/Textures/Dirt_Block.png")
wood_texture = load_texture("Assets/Textures/Wood_Block.png")
sky_texture = load_texture("Assets/Textures/Skybox.png")
arm_texture = load_texture("Assets/Textures/Arm_Texture.png")
punch_sound = Audio("Assets/SFX/Punch_Sound.wav", loop=False, autoplay=False)
window.exit_button.visible = False
block_pick = 1
game_paused = False
is_running = False
chunk_size = 1
chunk_height = 1
loaded_chunks = {}
chunk_distance = 7
show_debug_info = False
last_debug_update = 0
debug_update_interval = 1

def update():
    global block_pick, is_running, last_debug_update

    if not game_paused:
        if held_keys["1"]: block_pick = 1
        if held_keys["2"]: block_pick = 2
        if held_keys["3"]: block_pick = 3
        if held_keys["4"]: block_pick = 4
        if held_keys["5"]: block_pick = 5

        is_running = held_keys['left control']
        player.speed = 10 if is_running else 3

        manage_chunks()

        if show_debug_info and time.time() - last_debug_update >= debug_update_interval:
            last_debug_update = time.time()
            update_debug_info()

        update_hand()

def input(key):
    global block_pick, show_debug_info
    if key == 'escape':
        toggle_pause()
    if key == 'f3':
        show_debug_info = not show_debug_info
        if show_debug_info:
            update_debug_info()
    if key == 'scroll up':
        block_pick += 1
        if block_pick > 5:
            block_pick = 1
    elif key == 'scroll down':
        block_pick -= 1
        if block_pick < 1:
            block_pick = 5

    print(f"Seçilen blok ID'si: {block_pick}")

class Voxel(Button):
    def __init__(self, position=(0, 0, 0), texture=grass_texture):
        super().__init__(
            parent=scene,
            position=position,
            model="Assets/Models/Block",
            origin_y=0.5,
            texture=texture,
            color=color.color(0, 0, random.uniform(0.9, 1)),
            highlight_color=color.light_gray,
            scale=0.5
        )
    
    def input(self, key):
        if self.hovered and not game_paused:
            if key == "left mouse down":
                punch_sound.play()
                destroy(self)
            elif key == "right mouse down":
                punch_sound.play()
                if block_pick == 1: voxel = Voxel(position=self.position + mouse.normal, texture=grass_texture)
                if block_pick == 2: voxel = Voxel(position=self.position + mouse.normal, texture=stone_texture)
                if block_pick == 3: voxel = Voxel(position=self.position + mouse.normal, texture=brick_texture)
                if block_pick == 4: voxel = Voxel(position=self.position + mouse.normal, texture=dirt_texture)
                if block_pick == 5: voxel = Voxel(position=self.position + mouse.normal, texture=wood_texture)

class Sky(Entity):
    def __init__(self):
        super().__init__(
            parent=scene,
            model="Sphere",
            texture=sky_texture,
            scale=150,
            double_sided=True
        )

class Hand(Entity):
    def __init__(self):
        super().__init__(
            parent=camera.ui,
            model="Assets/Models/Arm",
            texture=arm_texture,
            scale=0.2,
            rotation=Vec3(150, -10, 0),
            position=Vec2(0.4, -0.6)
        )
    
    def update_texture(self, texture=None):
        if texture:
            self.model = "Assets/Models/Block"
            self.texture = texture
        else:
            self.model = "Assets/Models/Arm"
            self.texture = arm_texture

def generate_chunk(x_chunk, z_chunk):
    chunk = []
    for x in range(x_chunk * chunk_size, (x_chunk + 1) * chunk_size):
        for z in range(z_chunk * chunk_size, (z_chunk + 1) * chunk_size):
            height = int(noise.pnoise2(x * 0.1, z * 0.1, octaves=6) * 5) + 5
            for y in range(height):
                texture = grass_texture if y == height - 1 else (stone_texture if y < height - 4 else dirt_texture)
                voxel = Voxel(position=(x, y, z), texture=texture)
                chunk.append(voxel)
    return chunk

def manage_chunks():
    global loaded_chunks

    player_chunk_x = int(player.x // chunk_size)
    player_chunk_z = int(player.z // chunk_size)

    new_loaded_chunks = set()
    for x in range(player_chunk_x - chunk_distance, player_chunk_x + chunk_distance + 1):
        for z in range(player_chunk_z - chunk_distance, player_chunk_z + chunk_distance + 1):
            chunk_key = (x, z)
            if chunk_key not in loaded_chunks:
                loaded_chunks[chunk_key] = generate_chunk(x, z)
            else:
                for voxel in loaded_chunks[chunk_key]:
                    voxel.visible = True
            new_loaded_chunks.add(chunk_key)

    for chunk_key in list(loaded_chunks.keys()):
        if chunk_key not in new_loaded_chunks:
            for voxel in loaded_chunks[chunk_key]:
                voxel.visible = False

def toggle_pause():
    global game_paused
    game_paused = not game_paused
    menu.enabled = game_paused
    mouse.locked = not game_paused
    player.enabled = not game_paused

def resume_game():
    toggle_pause()

def open_settings():
    print("Ayarlar menüsü açıldı.")

def quit_game():
    application.quit()

for x in range(-chunk_distance, chunk_distance + 1):
    for z in range(-chunk_distance, chunk_distance + 1):
        loaded_chunks[(x, z)] = generate_chunk(x, z)

player = FirstPersonController()
sky = Sky()
hand = Hand()

menu = Entity(parent=camera.ui, enabled=False)
background = Entity(parent=menu, model='quad', texture='white_cube', scale=(0.6, 0.7), color=color.dark_gray, position=(0, 0))

button_height = 0.1
button_spacing = 0.02

resume_button = Button(parent=menu, text='Back to Game', scale=(0.5, button_height), position=(0, 0.2), on_click=resume_game)
options_button = Button(parent=menu, text='Options...', scale=(0.5, button_height), position=(0, 0.2 - (button_height + button_spacing)), on_click=open_settings)
quit_button = Button(parent=menu, text='Save and Quit to Title', scale=(0.5, button_height), position=(0, 0.2 - 2 * (button_height + button_spacing)), on_click=quit_game)

fps_text = Text(parent=camera.ui, color=color.white, scale=1, position=(-0.5, 0.3))
position_text = Text(parent=camera.ui, color=color.white, scale=1, position=(-0.5, 0.1))

def update_debug_info():
    fps_text.text = f'FPS: {int(1 / time.dt)}'
    ram_usage = psutil.virtual_memory().used / (1024 * 1024)
    ram_total = psutil.virtual_memory().total / (1024 * 1024)
    fps_text.text += f'\nRAM Usage: {ram_usage:.2f} MB\nTotal RAM: {ram_total:.2f} MB'
    position_text.text = f'Position: X: {player.x:.2f} Y: {player.y:.2f} Z: {player.z:.2f}'

def update_hand():
    if block_pick:
        textures = [grass_texture, stone_texture, brick_texture, dirt_texture, wood_texture]
        hand.update_texture(texture=textures[block_pick - 1])
    else:
        hand.update_texture(None)

app.run()
