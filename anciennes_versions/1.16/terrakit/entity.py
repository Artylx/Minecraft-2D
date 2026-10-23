from ctypes.wintypes import HENHMETAFILE

import pygame
from terrakit import game_property, inventory, game_type
import math
import random
import uuid
from terrakit.texture_manager import TextureType
from terrakit import context
from terrakit.annimator import Anim, AnimationClip, Animator, AnimationSet

def rotate_around_pivot(image, angle, pivot, offset):
    rotated_image = pygame.transform.rotate(image, angle)
    rotated_offset = offset.rotate(-angle)
    rect = rotated_image.get_rect(center=pivot + rotated_offset)
    return rotated_image, rect

def tint_surface(surface, color):
    tinted = surface.copy()
    tinted.fill(color, special_flags=pygame.BLEND_RGB_MULT)
    return tinted

def apply_brightness(surface, brightness):
    result = surface.copy()
    dark = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    dark.fill((0, 0, 0, int((1 - brightness) * 255)))
    result.blit(dark, (0, 0))
    return result

def create_outline_surface(surface, thickness=3):

    mask = pygame.mask.from_surface(surface)

    size = (
        surface.get_width() + thickness * 2,
        surface.get_height() + thickness * 2
    )

    outline = pygame.Surface(
        size,
        pygame.SRCALPHA
    )

    # Décalage pour recentrer
    offset = pygame.Vector2(thickness, thickness)

    for x, y in mask.outline():

        for dx in range(-thickness, thickness + 1):
            for dy in range(-thickness, thickness + 1):

                if dx * dx + dy * dy <= thickness * thickness:

                    outline.set_at(
                        (
                            int(x + offset.x + dx),
                            int(y + offset.y + dy)
                        ),
                        (255,255,255,255)
                    )

    return outline

ATTACK_RANGE = 30

# class Entity:
#     texture_manager = None

#     def __init__(self, rect, world=None, name="Unamed entity", texture=None, dif_pos_render=None, 
#                  displayed_name="", display_name=False, gravity=game_property.GRAVITY, 
#                  collidable=True, live_time=None, speed=game_property.ENTITY_SPEED):
#         self.uuid = uuid.uuid4()
#         self.rect = rect
#         self.texture = texture
#         self.display_name = display_name
#         self.name = name
#         self.world = world
#         self.spawn_time = pygame.time.get_ticks()
#         self.font = pygame.font.SysFont("Arial", 14)
#         self.gravity = gravity
#         self.collidable = collidable
#         self.is_alive = True
#         self.live_time = live_time
#         self.in_liquid = False
#         if dif_pos_render is None:
#             dif_pos_render = [0, 0]
#         self.dif_pos_render = dif_pos_render

#         self.on_ground = False
#         self.auto_jump = False

#         self.velocity = pygame.Vector2(0, 0)

#         self.speed = speed

#         self.set_displayed_name(str(displayed_name))

#         self.temp_rect = None
#         self.attached_entities = []
#         self.attached_to = None

#         self.alpha_texture = 255
#         self.removing = False
#         self.remove_speed = 100

#     def set_displayed_name(self, name: str):
#         self.displayed_name = name
#         self.update_vars()

#     def is_valid(self): 
#         if self.world:
#             if self.world.contains_entity(self):
#                 return True
#         return False

#     def attach_self(self, entity):
#         self.attached_to = entity
#         entity.add_attached_entity(self)

#     def add_attached_entity(self, entity):
#         self.attached_entities.append(entity)

#     def update_vars(self):
#         self.display_name_text_surface = self.font.render(self.displayed_name, True, (255, 255, 255))

#         self.display_name_margin_x = 8
#         self.display_name_margin_y = 4

#         self.display_name_surface_width = self.display_name_text_surface.get_width() + self.display_name_margin_x * 2
#         self.display_name_surface_height = self.display_name_text_surface.get_height() + self.display_name_margin_y * 2

#         self.display_name_surface = pygame.Surface((self.display_name_surface_width, self.display_name_surface_height), pygame.SRCALPHA)
    
#     def get_uuid(self):
#         return self.uuid
    
#     def kill(self):
#         self.is_alive = False
#         for entity in self.attached_entities:
#             entity.kill()
    
#     def is_touching_liquid(self):
#         points = [
#             (self.rect.left // game_property.TILE_SIZE, self.rect.top // game_property.TILE_SIZE),
#             (self.rect.right // game_property.TILE_SIZE, self.rect.top // game_property.TILE_SIZE),
#             (self.rect.left // game_property.TILE_SIZE, self.rect.bottom // game_property.TILE_SIZE),
#             (self.rect.right // game_property.TILE_SIZE, self.rect.bottom // game_property.TILE_SIZE),

#             # Milieux des côtés
#             (self.rect.centerx // game_property.TILE_SIZE, self.rect.top // game_property.TILE_SIZE),
#             (self.rect.centerx // game_property.TILE_SIZE, self.rect.bottom // game_property.TILE_SIZE),
#             (self.rect.left // game_property.TILE_SIZE, self.rect.centery // game_property.TILE_SIZE),
#             (self.rect.right // game_property.TILE_SIZE, self.rect.centery // game_property.TILE_SIZE),
#         ]

#         for x, y in points:
#             block = self.world.get_block(int(x), int(y))

#             if block is not None and block.block_property.liquid:
#                 return True

#         return False

#     def render(self, screen, cam_rect, color=(255, 255, 255)):
#         draw_x, draw_y = game_property.world_to_screen(
#             self.rect.x, self.rect.y, self.rect.height, cam_rect
#         )

#         draw_x += self.dif_pos_render[0]
#         draw_y -= self.dif_pos_render[1]

#         light = self.world.get_entity_light(self)

#         # normaliser (0–15 → 0.2–1.0)
#         brightness = max(0.2, light / 15)

#         if self.texture:
#             tex = self.texture.copy()

#             brightness = max(0.2, light / 15)

#             # surface de modulation
#             shade = pygame.Surface(tex.get_size(), pygame.SRCALPHA)
#             shade.fill((
#                 int(255 * brightness),
#                 int(255 * brightness),
#                 int(255 * brightness),
#                 255
#             ))

#             tex.blit(shade, (0, 0), special_flags=pygame.BLEND_RGB_MULT)

#             tex.set_alpha(int(self.alpha_texture))

#             screen.blit(tex, (draw_x, draw_y))
#         else:
#             if color:
#                 c = (
#                     int(color[0] * brightness),
#                     int(color[1] * brightness),
#                     int(color[2] * brightness)
#                 )
#                 surface = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)

#                 surface.fill((*c, int(self.alpha_texture)))

#                 screen.blit(surface, (draw_x, draw_y))

#     def get_nearest_player(self, distance: int):
#         """
#         Return (TUPLE):
#             -   Player
#             -   Distance
#         """
#         nearest = None

#         if not distance:
#             return nearest
#         nearest_distance = distance

#         for player in self.world.get_entities(Player):
#             dx = player.rect.centerx - self.rect.centerx
#             dy = player.rect.centery - self.rect.centery

#             distance = math.hypot(dx, dy)

#             if distance < nearest_distance:
#                 nearest_distance = distance
#                 nearest = (player, distance)
#         return nearest

#     def render_display_name(self, screen, cam_rect, x_offset=0, y_offset=0):        
#         draw_x, draw_y = game_property.world_to_screen(
#             self.rect.x, self.rect.y, self.rect.height, cam_rect
#         )

#         draw_x += self.dif_pos_render[0]
#         draw_y -= self.dif_pos_render[1]

#         # Surface fond semi-transparent
#         chat_surface = pygame.Surface((self.display_name_surface_width, self.display_name_surface_height), pygame.SRCALPHA)
#         chat_surface.fill((0, 0, 0, 150))

#         # Ajouter texte dans la surface
#         chat_surface.blit(self.display_name_text_surface, (self.display_name_margin_x, self.display_name_margin_y))

#         # Centrer au-dessus du joueur
#         name_x = draw_x + self.rect.width / 2 - self.display_name_surface_width / 2 + x_offset
#         name_y = draw_y - self.display_name_surface_height - 5 + y_offset

#         screen.blit(chat_surface, (name_x, name_y))

#     def render_hit_box(self, screen, cam_rect, color=(255, 255, 255), width=1):
#         self.render_hit_box_with_rect(screen, cam_rect, color=(255, 255, 255), width=1, rect=self.rect)

#     def render_hit_box_with_rect(self, screen, cam_rect, rect=None, color=(255, 255, 255), width=1):
#         draw_x, draw_y = game_property.world_to_screen(rect.x, rect.y, rect.height, cam_rect)
#         pygame.draw.rect(screen, color, (draw_x, draw_y, rect.width, rect.height), width)

#     def render_highlight(self, screen, cam_rect, color=(255, 255, 255)):
#         self.render_hit_box(screen, cam_rect, color, width=2)

#     def tp(self, x, y):
#         self.rect.x = x
#         self.rect.y = y

#     def tp_tile(self, x, y):
#         self.rect.x = x * game_property.TILE_SIZE
#         self.rect.y = y * game_property.TILE_SIZE

#     def update_live_time(self, dt):
#         if self.live_time is not None:
#             self.live_time -= dt
        
#             if self.live_time <= 0:
#                 self.removing = True

#         if self.removing:
#             self.alpha_texture -= self.remove_speed * dt

#             if self.alpha_texture <= 0:
#                 self.alpha_texture = 0

#                 self.kill()

#                 return

#     def update(self, dt, update_live=True):
#         self.in_liquid = self.is_touching_liquid()

#         if update_live:
#             self.update_live_time(dt)

#         max_steps = 100
#         steps = 0
        
#         try:
#             self.apply_gravity(dt)
            
#             if self.in_liquid:
#                 self.velocity.x *= 0.84
#                 self.velocity.y *= 0.84
#             else:
#                 self.velocity.x *= 0.9

#             new_x = self.rect.x + self.velocity.x * dt
#             new_y = self.rect.y + self.velocity.y * dt


#             # ----- HORIZONTAL -----
#             self.temp_rect = self.rect.copy()
#             self.temp_rect.x = new_x

#             if not self.world.is_collide_at(self.temp_rect):
#                 self.move(new_x - self.rect.x, 0)
#             else:
#                 if self.velocity.x != 0:
#                     step = 1 if self.velocity.x > 0 else -1

#                     while not self.world.is_collide_at(self.rect.move(step, 0)):
#                         self.move(step, 0)
#                         steps += 1

#                         if steps > max_steps:
#                             break

#                     self.velocity.x = 0


#             # ----- VERTICAL -----
#             self.temp_rect = self.rect.copy()
#             self.temp_rect.y = new_y

#             if not self.world.is_collide_at(self.temp_rect):
#                 self.move(0, new_y - self.rect.y)
#                 self.on_ground = False
#             else:
#                 step = 1 if self.velocity.y > 0 else -1

#                 while not self.world.is_collide_at(self.rect.move(0, step)):
#                     self.move(0, step)

#                 self.velocity.y = 0

#                 if step < 0:
#                     self.on_ground = True
#         except Exception as e:
#             print("Exception: ", e)

#     def move(self, dx, dy):
#         self.rect.x += dx
#         self.rect.y += dy

#         for entity in self.attached_entities:
#             entity.move(dx, dy)

#     def apply_gravity(self, dt):
#         if not self.on_ground:
#             # gravity is an acceleration; scale by dt
#             self.add_velocity(0, -self.gravity * dt)
#         else:
#             self.velocity.y = 0

#     def jump(self, force):
#         self.add_velocity(0, force)
#         self.on_ground = False
    
#     def add_velocity(self, vx, vy):
#         self.velocity.x += (vx * self.speed)
#         self.velocity.y += (vy * self.speed)

#     def set_velocity(self, vx, vy):
#         if vx:
#             self.velocity.x = vx
#         if vy:
#             self.velocity.y = vy

#     def get_name(self):
#         return self.name
    
#     def get_rect(self) -> pygame.Rect:
#         return self.rect
    
#     def get_pos(self) -> tuple:
#         return (self.rect.x, self.rect.y)
    
#     def get_pos_tile(self) -> tuple:
#         return (
#             round(self.rect.x / game_property.TILE_SIZE, 2),
#             round(self.rect.y / game_property.TILE_SIZE, 2)
#         )
    
#     def load(self, data, add_map=None):

#         if add_map is None:
#             add_map = {}

#         mapping = {
#             "uuid": "uuid",
#             "x": ("rect", "x"),
#             "y": ("rect", "y"),
#             "w": ("rect", "width"),
#             "h": ("rect", "height"),
#             "vx": ("velocity", "x"),
#             "vy": ("velocity", "y"),
#             "name": "name",
#             "gravity": "gravity",
#             "speed": "speed",
#             "display_name": "display_name",
#             "displayed_name": "displayed_name",
#         }

#         mapping.update(add_map)

#         # Vérification
#         required = list(mapping.keys())
#         missing = [k for k in required if k not in data]
#         if missing:
#             print(f"Champs manquants: {missing}")
#             return None

#         # Assignation complexe
#         for key, target in mapping.items():
#             if isinstance(target, tuple):
#                 obj, attr = target
#                 setattr(getattr(self, obj), attr, data[key])
#             else:
#                 setattr(self, target, data[key])

#         self.update_vars()
#         return self

#     def to_json(self, type_="Entity", dict_=None):

#         if dict_ is None:
#             dict_ = {}

#         data = {
#             "type": type_,
#             "uuid": str(self.uuid),
#             "x": self.rect.x,
#             "y": self.rect.y,
#             "w": self.rect.width,
#             "h": self.rect.height,
#             "vx": self.velocity.x,
#             "vy": self.velocity.y,
#             "gravity": self.gravity,
#             "speed": self.speed,
#             "display_name": self.display_name,
#             "displayed_name": self.displayed_name,
#             "name": self.name,
#             "live_time": self.live_time,
#         }

#         data.update(dict_)   # ajoute les champs supplémentaires

#         return data
    
# class Annimation:
#     ATTACK = "attack"
#     NONE = "none"

# class Living_entity(Entity):
#     def __init__(self, rect, world=None, name="Unamed entity", displayed_name="", health=20, max_health=20, drops=None, collidable=True, invulnerable=False, live_time=None):
#         super().__init__(rect, world, name, None, None, display_name=False, collidable=collidable, live_time=live_time, displayed_name=displayed_name)
#         self.max_health = max_health
#         self.health = health
#         if not drops:
#             drops = []
#         self.drops = drops
#         self.invulnerable = invulnerable

#         self.orientation = "left"
#         self.last_vx = 0

#         self.reset_annimation()
#         self.reset_take_damage()

#         self.knockback_timer = 0
#         self.knockback_resistance = 0.0
#         self.walk_animation = 0
    
#     def update(self, dt, update_live=True):
#         if self.annim_time > 0:
#             self.annim_time -= dt
#         else:
#             self.reset_annimation()

#         if self.health <= 0:
#             self.kill()
#             return
        
#         if self.annim_damage_time > 0:
#             self.annim_damage_time -= dt
#         else:
#             self.reset_take_damage()

#         if self.knockback_timer > 0:
#             self.knockback_timer -= dt
        
#         return super().update(dt, update_live)

#     def set_orientation(self, orientation):
#         if self.annim_time > 0 and self.annim_orientation:
#             return True
#         else:
#             self.annim_orientation = None
        
#         if self.orientation != orientation:
#             self.orientation = orientation
#             self.update_texture()
#             return True
#         return False
    
#     def get_anim_direction(self) -> int:
#         if self.annim_orientation:
#             if self.annim_orientation == "right":
#                 return 1
#             if self.annim_orientation == "left":
#                 return -1
#         return 0

#     def get_orientation(self):
#         if self.annim_orientation:
#             return self.annim_orientation
#         return self.orientation

#     def start_annimation(self, time: float, dirrection: str, annim_type: Annimation):
#         self.annim_time = time
#         self.annim_orientation = dirrection
#         self.annim_type = annim_type

#         self.update_texture()

#     def render(self, screen, cam_rect, color=(0, 0, 255)):
#         super().render(screen, cam_rect, color)
#         if self.annim_time > 0:
#             self.render_annimation()

#         if self.health < self.max_health:
#             self.render_health_bar(screen, cam_rect)

#     def render_health_bar(self, screen, cam_rect):
#         draw_x, draw_y = game_property.world_to_screen(
#             self.rect.x, self.rect.y, self.rect.height, cam_rect
#         )

#         bar_width = self.rect.width * 1.5
#         bar_height = 10

#         health_ratio = max(0, self.health / self.max_health)

#         bar_x = draw_x - (bar_width - self.rect.width) // 2
#         bar_y = draw_y - self.display_name_surface_height + 10

#         # fond
#         pygame.draw.rect(screen, (60, 0, 0), (bar_x, bar_y, bar_width, bar_height))

#         # vie
#         pygame.draw.rect(
#             screen,
#             (0, 220, 0),
#             (bar_x, bar_y, bar_width * health_ratio, bar_height)
#         )

#         # contour (propre visuellement)
#         pygame.draw.rect(
#             screen,
#             (255, 255, 255),
#             (bar_x, bar_y, bar_width, bar_height),
#             1
#         )
    
#     def render_annimation(self):
#         pass

#     def reset_annimation(self):
#         self.annim_time = 0
#         self.annim_orientation = None
#         self.annim_type = None
#         self.update_orientation()

#         self.update_texture()

#     def add_velocity(self, vx, vy):
#         super().add_velocity(vx, vy)
#         self.update_orientation()
    
#     def set_velocity(self, vx, vy):
#         super().set_velocity(vx, vy)
#         self.update_orientation()

#     def update_orientation(self):
#         if self.velocity.x > 0:
#             self.set_orientation("right")
#         elif self.velocity.x < 0:
#             self.set_orientation("left")

#     def get_int_direction(self):
#         if self.get_orientation() == "right":
#             return 1
#         else:
#             return -1

#     def apply_damage(self, damage, dx):
#         if not self.is_taking_damage and not self.invulnerable:
#             self.health -= damage * game_property.DAMAGE_COEF

#             knockback_force = 10
#             vx = dx * knockback_force
#             vy = 10

#             self.add_velocity(vx, vy)
#             self.take_damage()

#             self.knockback_timer = 0.2

#     def take_damage(self):
#         self.is_taking_damage = True
#         self.annim_damage_time = 0.2
    
#     def reset_take_damage(self):
#         self.is_taking_damage = False
#         self.annim_damage_time = 0

#     def update_texture(self):
#         pass

#     def drop_item(self, itemStack, direction=None):
#         if not itemStack:
#             return

#         mid_x = self.rect.x + self.rect.width // 2
#         quart_y = self.rect.y + self.rect.height // 4
        
#         entity = Item(self.world, itemStack, (mid_x + self.get_int_direction() * self.rect.width, quart_y))

#         if direction is None:
#             direction = self.get_int_direction()
#         entity.add_velocity(self.get_int_direction() * 5, 5)
#         self.world.create_entity(entity)

#     def kill(self):
#         super().kill()
#         if self.drops:
#             for item in self.drops:
#                 self.drop_item(item, random.choice([-1, -0.7, -0.4, 0.4, 0.7, 1]))

#     def load(self, data, add_map=None):

#         if add_map is None:
#             add_map = {}

#         map_ = {
#             "health": "health",
#             "max_health": "max_health",
#             "orientation": "orientation",
#         }

#         map_.update(add_map)

#         if not super().load(data, map_):
#             return None
#         self.update_orientation()

#         drops_= []
#         if data.get("drops", None) is not None:
#             drops = data.get("drops")
#             for dict_drop in drops:
#                 item = inventory.ItemStack()
#                 item.load(dict_drop)
#                 if item:
#                     drops_.append(item)
#                 else:
#                     return None
#         else:
#             return None
#         return self

#     def to_json(self, type_="Living_entity", dict_=None):
#         if dict_ is None:
#             dict_ = {}

#         drops = []
#         if self.drops:
#             for drop_item in self.drops:
#                 drops.append(drop_item.to_json())

#         data = {
#             "health": self.health,
#             "max_health": self.max_health,
#             "orientation": self.orientation,
#             "drops": drops
#         }

#         data.update(dict_)

#         return super().to_json(type_, data)

# class Humanoid(Living_entity):
#     def __init__(self, rect, world=None, name="Humanoid entity", displayed_name="", health=20, max_health=20, drops=None, collidable=True, invulnerable=False,
#                  leg_texture: TextureType = None, 
#                  arm_texture: TextureType = None, 
#                  body_texture: TextureType = None, 
#                  head_texture: TextureType = None
#                  ):
        
#         super().__init__(rect, world, name, displayed_name, health, max_health, drops, collidable, invulnerable)

#         self.arm_angle = 0
#         self.init_texture(head_texture, body_texture, leg_texture, arm_texture)
    
#     def init_texture(self, head_texture, body_texture, leg_texture, arm_texture):

#         def build(tex, size):
#             base = pygame.transform.scale(tex, size)
#             flipped = pygame.transform.flip(base, True, False)

#             return {
#                 "right": base,
#                 "left": flipped
#             }

#         def tint_pack(tex_dict, color):
#             return {
#                 "right": tint_surface(tex_dict["right"], color),
#                 "left": tint_surface(tex_dict["left"], color)
#             }

#         # -------------------------
#         # BASE SIZES
#         # -------------------------
#         head_size = (self.rect.width - 4, self.rect.width - 4)
#         body_size = (self.rect.width, self.rect.width)
#         leg_size = ((self.rect.width - 2) // 2, self.rect.width)
#         arm_size = (self.rect.width // 2, self.rect.width)

#         # -------------------------
#         # BASE TEXTURES
#         # -------------------------
#         self.textures = {
#             "head": build(context.get_resource_pack().texture_manager().get_texture(head_texture), head_size),
#             "body": build(context.get_resource_pack().texture_manager().get_texture(body_texture), body_size),
#             "leg": build(context.get_resource_pack().texture_manager().get_texture(leg_texture), leg_size),
#             "arm": build(context.get_resource_pack().texture_manager().get_texture(arm_texture), arm_size),
#         }

#         # -------------------------
#         # RED VARIANT (exemple)
#         # -------------------------
#         red_color = (200, 100, 100)

#         self.textures_red = {
#             "head": tint_pack(self.textures["head"], red_color),
#             "body": tint_pack(self.textures["body"], red_color),
#             "leg": tint_pack(self.textures["leg"], red_color),
#             "arm": tint_pack(self.textures["arm"], red_color),
#         }

#         self.textures_outline = {}

#         for part in self.textures:

#             self.textures_outline[part] = {
#                 "right": create_outline_surface(
#                     self.textures[part]["right"]
#                 ),
#                 "left": create_outline_surface(
#                     self.textures[part]["left"]
#                 )
#             }

#     def blit_outline(self, screen, surface, pos):

#         offset = (
#             surface.get_width() // 2,
#             surface.get_height() // 2
#         )

#         screen.blit(
#             surface,
#             (
#                 pos[0] - 3,
#                 pos[1] - 3
#             )
#         )

#     def render(self, screen, cam_rect, use_red=False, outline=False):

#         if outline:
#             tex = self.textures_outline
#         else:
#             tex = self.textures_red if use_red else self.textures

#         gap_outline = 3 if outline else 0

#         orientation = self.get_orientation()
#         head = tex["head"][orientation]
#         body = tex["body"][orientation]
#         leg  = tex["leg"][orientation]
#         arm  = tex["arm"][orientation]

#         # =========================
#         # HEAD (avec world_to_screen)
#         draw_x, draw_y = game_property.world_to_screen(
#             self.rect.x, self.rect.y, self.rect.height, cam_rect
#         )
#         draw_x += 2
#         draw_y += 4
#         if head:
#             screen.blit(
#                 head,
#                 (
#                     draw_x - gap_outline,
#                     draw_y - gap_outline
#                 )
#             )

#         # =========================
#         # BASE POSITION (évite recalculs)
#         base_x = self.rect.x - cam_rect.x
#         base_y = cam_rect.height - (self.rect.y - cam_rect.y) - self.rect.height

#         # =========================
#         # BODY
#         if body:

#             pos = (
#                 base_x - gap_outline,
#                 base_y + self.rect.width - gap_outline
#             )

#             screen.blit(body, pos)

#         # =========================
#         # LEG
#         if leg:

#             pos = (
#                 base_x + 2 - gap_outline,
#                 base_y + self.rect.width * 2 - gap_outline
#             )

#             screen.blit(leg, pos)

#             pos = (
#                 base_x + 2 + (self.rect.width - 4) // 2 - gap_outline,
#                 base_y + self.rect.width * 2 - gap_outline
#             )

#             screen.blit(leg, pos)

#         # =========================
#         # ARM

#         if self.get_orientation() == "left":
#             arm_x = base_x + self.rect.width // 2
#             angle = -self.arm_angle
#         else:
#             arm_x = base_x
#             angle = self.arm_angle

#         arm_y = base_y + self.rect.width

#         if arm:
#             # Position de l'épaule
#             pivot = pygame.Vector2(
#                 arm_x + arm.get_width() // 2,
#                 arm_y
#             )

#             # Point de rotation dans le sprite
#             offset = pygame.Vector2(
#                 0,
#                 arm.get_height() / 2
#             )

#             rotated_arm, arm_rect = rotate_around_pivot(
#                 arm,
#                 angle,
#                 pivot,
#                 offset
#             )

#             screen.blit(rotated_arm, (
#                 arm_rect.x - gap_outline,
#                 arm_rect.y - gap_outline
#             ))
        

# class Npc(Humanoid):
#     def __init__(self, rect=None, world=None, name="Npc entity", displayed_name="NPC", health=20, max_health=20, drops=None, collidable=True, gender="male"):
#         if not rect:
#             rect = pygame.Rect(0, game_property.CHUNK_MAX_HEIGHT * game_property.TILE_SIZE, game_property.TILE_SIZE - 5, game_property.TILE_SIZE * 2.5)

#         leg_texture = TextureType.PLAYER_LEG_MALE
#         if gender == "female":
#             leg_texture = TextureType.PLAYER_LEG_FEMALE

#         arm_texture = TextureType.PLAYER_ARM_MALE
#         if gender == "female":
#             arm_texture = TextureType.PLAYER_ARM_FEMALE

#         head_texture = TextureType.PLAYER_HEAD_MALE
#         if gender == "female":
#             head_texture = TextureType.PLAYER_HEAD_FEMALE

#         body_texture = TextureType.PLAYER_BODY_MALE
#         if gender == "female":
#             body_texture = TextureType.PLAYER_BODY_FEMALE

#         super().__init__(rect, world, name, displayed_name=displayed_name, health=health, max_health=max_health, drops=drops, collidable=collidable,
#                          leg_texture=leg_texture,
#                          arm_texture=arm_texture,
#                          body_texture=body_texture,
#                          head_texture=head_texture, 
#                          invulnerable=True)
        
#         self.highlight_distance = 75
#         self.highlight = False
        
#     def render(self, screen, cam_rect):

#         if self.highlight:

#             super().render(
#                 screen,
#                 cam_rect,
#                 False,
#                 True
#             )

#             # margin_x = self.display_name_margin_x
#             # self.display_name_margin_x = 0
#             # super().render_display_name(screen, cam_rect, x_offset=25)
            
#             # self.display_name_margin_x = margin_x
#             # self.render_input(screen, cam_rect, x_offset=25)

#         # else:
#         #     super().render_display_name(screen, cam_rect)

#         super().render_display_name(screen, cam_rect)

#         super().render(
#             screen,
#             cam_rect,
#             False,
#             False
#         )

#     def render_input(self, screen, cam_rect, x_offset=0, y_offset=0):
#         draw_x, draw_y = game_property.world_to_screen(
#             self.rect.x, self.rect.y, self.rect.height, cam_rect
#         )

#         draw_x += self.dif_pos_render[0]
#         draw_y -= self.dif_pos_render[1]

#         surface = pygame.Surface((x_offset, self.display_name_surface_height), pygame.SRCALPHA)
#         surface.fill((0, 0, 0, 150))

#         text = self.font.render("[E]", True, (255, 255, 255))
#         surface.blit(text, (self.display_name_margin_x, self.display_name_margin_y))

#         # Centrer au-dessus du joueur
#         _x = draw_x + self.rect.width / 2 - self.display_name_surface_width / 2
#         _y = draw_y - self.display_name_surface_height - 5 - y_offset

#         screen.blit(surface, (_x, _y))

        

#     def update(self, dt):
        
#         if self.highlight:
#             self.set_displayed_name(self.name)
            
#         self.highlight = False

#         for p in self.world.get_entities(Player):
#             distance = pygame.Vector2(
#                 self.rect.center
#             ).distance_to(
#                 p.rect.center
#             )

#             if distance <= self.highlight_distance:
#                 if not self.highlight:
#                     self.set_displayed_name("[E] " + self.name)
#                 self.highlight = True


#         return super().update(dt)


# class PlayerOld(Humanoid):
#     def __init__(self, world=None, name="", rect=None, max_health=40, gender="male"):
#         if not rect:
#             rect = pygame.Rect(0, game_property.CHUNK_MAX_HEIGHT * game_property.TILE_SIZE, game_property.TILE_SIZE - 5, game_property.TILE_SIZE * 2.5)

#         leg_texture = TextureType.PLAYER_LEG_MALE
#         if gender == "female":
#             leg_texture = TextureType.PLAYER_LEG_FEMALE

#         arm_texture = TextureType.PLAYER_ARM_MALE
#         if gender == "female":
#             arm_texture = TextureType.PLAYER_ARM_FEMALE

#         head_texture = TextureType.PLAYER_HEAD_MALE
#         if gender == "female":
#             head_texture = TextureType.PLAYER_HEAD_FEMALE

#         body_texture = TextureType.PLAYER_BODY_MALE
#         if gender == "female":
#             body_texture = TextureType.PLAYER_BODY_FEMALE

#         super().__init__(rect, world, name, displayed_name=name, max_health=max_health, health=max_health, 
#                          leg_texture=leg_texture,
#                          arm_texture=arm_texture,
#                          body_texture=body_texture,
#                          head_texture=head_texture)

#         self.inventory = inventory.Entity_Inventory(self)
#         self.speed = game_property.PLAYER_SPEED

#     def render(self, screen, cam_rect):
#         orientation = self.get_orientation()

#         # 🎯 Clignotement damage
#         use_red = False
#         if self.is_taking_damage:
#             if int(self.annim_damage_time * 20) % 2 == 0:
#                 use_red = True

#         # RENDER PLAYER
#         # =========================
#         # NOM
#         super().render_display_name(screen, cam_rect)
#         super().render(screen, cam_rect, use_red)

#         # =========================
#         # BASE POSITION (évite recalculs)
#         base_x = self.rect.x - cam_rect.x
#         base_y = cam_rect.height - (self.rect.y - cam_rect.y) - self.rect.height

#         # =========================
#         # ITEM / ARME
#         selected_item = self.inventory.ui.get_selected_item()

#         if selected_item:
#             item_property = selected_item.item_property

#             self.arm_angle = 20

#             if isinstance(item_property, game_type.Tool):

#                 if isinstance(item_property, game_type.Bow_tool):
#                     texture = selected_item.get_texture()

#                     self.arm_angle = 50

#                     if texture:
#                         weapon_size = int(self.rect.width * 1.8)
#                         texture = pygame.transform.scale(texture, (weapon_size, weapon_size))

#                         # 🎯 position main
#                         if orientation == "right":
#                             hand_x = base_x + int(self.rect.width * 0.75)
#                         else:
#                             hand_x = base_x + int(self.rect.width * 0.25)

#                         hand_y = base_y + int(self.rect.width * 1.2)

#                         # 🎯 flip
#                         if orientation == "left":
#                             texture = pygame.transform.flip(texture, True, False)

#                         # 🎯 pivot
#                         if orientation == "right":
#                             offset = pygame.Vector2(weapon_size * 0.2, 0)
#                         else:
#                             offset = pygame.Vector2(-weapon_size * 0.2, 0)

#                         angle = -30 * self.get_int_direction()

#                         pivot = pygame.Vector2(hand_x, hand_y)

#                         rotated_image, rotated_rect = rotate_around_pivot(
#                             texture,
#                             angle,
#                             pivot,
#                             offset
#                         )

#                         screen.blit(rotated_image, rotated_rect.topleft)
#                 else:

#                     texture = selected_item.get_texture()

#                     if texture:
#                         weapon_size = int(self.rect.width * 1.8)
#                         texture = pygame.transform.scale(texture, (weapon_size, weapon_size))

#                         # 🎯 position main
#                         if orientation == "right":
#                             hand_x = base_x + int(self.rect.width * 0.75)
#                         else:
#                             hand_x = base_x + int(self.rect.width * 0.25)

#                         hand_y = base_y + int(self.rect.width * 1.2)

#                         # 🎯 flip
#                         if orientation == "left":
#                             texture = pygame.transform.flip(texture, True, False)

#                         # 🎯 pivot
#                         if orientation == "right":
#                             offset = pygame.Vector2(weapon_size * 0.2, 0)
#                         else:
#                             offset = pygame.Vector2(-weapon_size * 0.2, 0)

#                         # 🎯 animation attaque
#                         if self.is_attacking():
#                             progress = self.annim_time
#                             angle = math.sin(progress * 10) * 80 * self.get_anim_direction()
#                         else:
#                             angle = 0

#                         pivot = pygame.Vector2(hand_x, hand_y)

#                         rotated_image, rotated_rect = rotate_around_pivot(
#                             texture,
#                             angle,
#                             pivot,
#                             offset
#                         )

#                         screen.blit(rotated_image, rotated_rect.topleft)

#             else:
#                 # 🎯 item normal
#                 if orientation == "left":
#                     item_x = base_x + self.rect.width // 2 - self.rect.width // 3 * 2
#                 else:
#                     item_x = base_x + self.rect.width // 3 * 2

#                 item_y = base_y + self.rect.width + self.rect.width // 2

#                 selected_item.render(
#                     screen,
#                     (item_x, item_y),
#                     draw_number=False,
#                     texture_size=(self.rect.width // 2, self.rect.width // 2)
#                 )
#         else:
#             self.arm_angle = 0

#     def render_hit_box(self, screen, cam_rect, color=(255, 255, 255), width=1):
#         if self.is_attacking():
#             selected_item = self.inventory.ui.get_selected_item()
#             if selected_item:
#                 if isinstance(selected_item.item_property, game_type.Attack_tool):
#                     self.render_hit_box_with_rect(screen, cam_rect, rect=self.get_rect_attack(), color=(255, 0, 0))
#         return super().render_hit_box(screen, cam_rect, color, width)

#     def get_rect(self):
#         return super().get_rect()
    
#     def get_rect_attack(self):
#         self.temp_rect = self.rect.copy()
#         self.temp_rect.x += self.get_anim_direction() * ATTACK_RANGE
#         return self.temp_rect


#     def update(self, dt):

#         if self.is_attacking():
#             selected_item = self.inventory.ui.get_selected_item()
#             if selected_item:
#                 if isinstance(selected_item.item_property, game_type.Attack_tool):

#                     entities = self.world.get_entities_by_rect(self.get_rect_attack())
#                     for entity in entities:
#                         if entity is not self and isinstance(entity, Living_entity):

#                             self.world.apply_damage_to_entity(entity, selected_item.item_property.get_attack_damage(), self.get_anim_direction(), self)

#                             # entity.apply_damage(selected_item.item_property.get_attack_damage(), self.get_anim_direction())

#         for entity in self.world.get_entities(Arrow):
#             if not entity.stucked or not entity.can_be_picked:
#                 continue

#             if entity.attached_to is not None:
#                 continue

#             if self.rect.colliderect(entity.rect):

#                 # ajouter une flèche à l'inventaire
#                 self.inventory.add_item(
#                     inventory.ItemStack(game_type.ItemProperty.ARROW, 1)
#                 )

#                 entity.kill()
                    
#         return super().update(dt)

#     def set_orientation(self, orientation):
#         if super().set_orientation(orientation):
#             self.update_texture()

#     def drop_item_index(self, itemIndex=None):
#         if not itemIndex:
#             item = self.inventory.ui.get_selected_item()
#             itemIndex = self.inventory.ui.selected_index
#         else:
#             item = self.inventory.get_item(itemIndex)

#         if item:
#             self.drop_item(item)
#             self.inventory.delete_item(itemIndex)
    
#     def use_selected_item(self, cam_rect):
#         selected_item = self.inventory.ui.get_selected_item()
#         if selected_item:
#             if isinstance(selected_item.item_property, game_type.Tool):
#                 sx, sy = pygame.mouse.get_pos() 
#                 mx, my = game_property.screen_to_world(sx, sy, 0, cam_rect) 
                
#                 direction = pygame.Vector2(mx - self.rect.centerx, my - self.rect.centery)

#                 if direction.length() != 0:
#                     direction = direction.normalize()
#                     self.use_item(direction)
#             elif isinstance(selected_item.item_property, game_type.Consumable):
                
#                 if isinstance(selected_item.item_property, game_type.Hanger_consumable):
#                     print(f"health={self.health}, life_regen={selected_item.item_property.life_regen}, max_health={self.max_health}")
#                     self.health = min(self.health + selected_item.item_property.life_regen, self.max_health)

#                 self.inventory.delete_item(self.inventory.ui.selected_index)

#     def stop_use_selected_item(self, cam_rect):
#         selected_item = self.inventory.ui.get_selected_item()
#         if selected_item:
#             if isinstance(selected_item.item_property, game_type.Tool):
#                 sx, sy = pygame.mouse.get_pos() 
#                 mx, my = game_property.screen_to_world(sx, sy, 0, cam_rect) 
                
#                 direction = pygame.Vector2(mx - self.rect.centerx, my - self.rect.centery)

#                 if direction.length() != 0:
#                     direction = direction.normalize()
#                     self.use_item(direction)
    
#     def use_item(self, direction):
#         selected_item = self.inventory.ui.get_selected_item()

#         if isinstance(selected_item.item_property, game_type.Bow_tool):
#             bow_use = selected_item.used
#             if bow_use:
#                 if not self.inventory.has_item(game_type.ItemProperty.ARROW):
#                     return

#                 self.inventory.delete_item_property(game_type.ItemProperty.ARROW, 1)

#                 selected_item.used = False
#                 if direction.x > 0:
#                     direction_str = "right"
#                 else:
#                     direction_str = "left"

#                 self.start_annimation(1/4, direction_str, Annimation.NONE)

#                 speed = 30
#                 v = direction * speed

#                 origin = pygame.Vector2(self.rect.centerx, self.rect.centery)

#                 selected_item.use()

#                 arrow = Arrow(
#                     (origin.x, origin.y),
#                     v,
#                     self,
#                     self.world,
#                 )
#                 self.world.create_entity(arrow)
#             else:
#                 if self.inventory.has_item(game_type.ItemProperty.ARROW):
#                     selected_item.used = True

#     def kill(self):
#         self.drops.extend(self.inventory.get_all_items())
#         super().kill()

#     def get_force_selected_item(self, block_property):
#         item = self.get_selected_item()

#         if item:

#             item_pro = item.item_property
#             if item_pro and block_property:
#                 if isinstance(item_pro, game_type.Pickaxe_tool):
#                     if block_property.weakness == game_type.Pickaxe_tool:
#                         return item_pro.power
                    
#                 if isinstance(item_pro, game_type.Axe_tool):
#                     if block_property.weakness == game_type.Axe_tool:
#                         return item_pro.power
#         return game_property.DEFAULT_BREAK_POWER
    
#     def get_selected_item(self):
#         return self.inventory.get_item(self.inventory.ui.selected_index)

#     def is_attacking(self):
#         if self.annim_type:
#             if self.annim_type == Annimation.ATTACK:
#                 return True
#         return False

#     def try_attack(self, cam_rect):
#         selected_item = self.inventory.ui.get_selected_item()
#         if selected_item:
#             if isinstance(selected_item.item_property, game_type.Attack_tool):
#                 sx, sy = pygame.mouse.get_pos()
#                 mx, my = game_property.screen_to_world(sx, sy, 0, cam_rect)

#                 direction = pygame.Vector2(mx - self.rect.centerx, my - self.rect.centery)

#                 if direction.length() != 0:
#                     direction = direction.normalize()
                    
#                     self.attack(direction)

#     def attack(self, v):
#         dx, dy = v

#         orientation = None
#         if dx < 0:
#             orientation = "left"
#         elif dx > 0:
#             orientation = "right"

#         self.start_annimation(1/4 * 3, orientation, Annimation.ATTACK)

#     def to_json(self, type_="Player", dict_=None):
#         if dict_ is None:
#             dict_ = {}

#         data = {
#             "inventory": self.inventory.to_json(),
#         }

#         data.update(dict_)
        
#         return super().to_json(type_, data)
     
#     def load(self, data, add_map=None):
#         self.inventory = self.inventory.load(data.get("inventory", None))
#         if self.inventory is None:
#             return None
#         if super().load(data, add_map) is None:
#             return None
#         self.update_texture()
#         return self

# class Item(Entity):
#     def __init__(self, world=None, _item=None, pos=(0, 0), size=(game_property.SIZE_ITEM, game_property.SIZE_ITEM), timer_picked=1):
#         rect = pygame.Rect(pos[0], pos[1], size[0], size[1])
#         super().__init__(rect, world, "Item", live_time=240)
#         self.phase = random.random() * math.pi * 2
#         self._item = _item
#         self.t = 0

#         self.update_texture()
#         self._can_be_picked = False
#         self.timer_picked = timer_picked

#     def get_item(self):
#         return self._item

#     def can_be_picked(self):
#         return self._can_be_picked

#     def update_texture(self):
#         if self._item is None:
#             return

#         texture = self.get_item().item_property.get_texture()

#         if texture is None:
#             print(f"Texture introuvable pour {self.get_item().item_property.texture}")
#             return

#         self.texture = pygame.transform.scale(
#             texture,
#             (game_property.SIZE_ITEM, game_property.SIZE_ITEM)
#         )

#     def render(self, screen, cam_rect):
        
#         offset_y = math.sin(self.t + self.phase) * 5

#         self.dif_pos_render = (0, offset_y)
        
#         super().render(screen, cam_rect, None)
#         #super().render_hit_box(screen, cam_rect)

#     def update(self, dt):
#         super().update(dt, False)
#         self.t = pygame.time.get_ticks() / 500

#         if self.timer_picked <= 0:
#             self._can_be_picked = True

#             super().update_live_time(dt)
#         else:
#             self.timer_picked -= dt

#     def load(self, data, add_map=None):

#         if add_map is None:
#             add_map = {}

#         if not super().load(data, add_map):
#             return None
        
#         if data.get("item_type", None) is None:
#             return None
        
#         self._item = game_type.ItemProperty.from_dict(data["item_type"])

#         self.t = random.Random().randint(0, 100) / 500
#         self.update_texture()
#         return self

#     def to_json(self, type_="Item", dict_=None):
#         if dict_ is None:
#             dict_ = {}

#         data = {
#             "item_type": self.get_item().to_json(),
#         }

#         data.update(dict_)

#         return super().to_json(type_, data)

# class Mob(Living_entity):
#     DETECTION_DISTANCE = None

#     def __init__(self, rect, inventory=None, world=None, name="Unamed entity", health=20, max_health=20, IA=True, spawn_point=None):
#         super().__init__(rect, world, name, health, max_health)
#         self.auto_jump = True
#         self.IA = IA
#         self.spawn_point = spawn_point

#         self.move_timer = 0
#         self.move_direction = 0
#         self.move_speed = 120

#         self.inventory = inventory

#     def update(self, dt):
#         if abs(self.velocity.x) > 5:
#             self.walk_animation += dt * 10

#         # Décrémenter le timer
#         if self.IA:
#             self.move_timer -= dt

#             if self.move_timer <= 0:
#                 self.move_timer = random.uniform(2, 5)

#                 # choisir une direction
#                 self.move_direction = random.choice([-1, 0, 1])

#         self.apply_horizontal_target()

#         self.apply_auto_jump()

#         # Appel du super pour appliquer le mouvement
#         super().update(dt)

#     def get_nearest_player(self):
#         near = super().get_nearest_player(self.DETECTION_DISTANCE)
#         if near:
#             return near[0]
#         return None

#     def apply_auto_jump(self):
#         if self.auto_jump:
#             if self.on_ground and not self.in_liquid and self.can_auto_jump():
#                 self.set_velocity(
#                     None,
#                     game_property.JUMP_VELOCITY // 3 * 2 * self.speed
#                 )
#                 self.on_ground = False
#             elif self.in_liquid and self.can_auto_jump(water=True):
#                 self.set_velocity(
#                     None,
#                     (game_property.JUMP_VELOCITY // 3 * 2 * self.speed) // 3
#                 )

#     def can_auto_jump(self, water=False):
#         # bloc devant au niveau des pieds
#         front = self.rect.copy()
#         front.x += self.move_direction * 5

#         if not self.world.is_collide_at(front):
#             return False

#         # bloc au-dessus de l'obstacle
#         above = front.copy()
#         above.y += game_property.TILE_SIZE

#         # si un bloc est au-dessus, c'est trop haut
#         if not water and self.world.is_collide_at(above):
#             return False

#         return True

#     def apply_horizontal_target(self):
#         ia_control = self.knockback_timer <= 0

#         if ia_control:
#             target = self.move_direction * self.move_speed

#             if target > 0:
#                 vx = max(self.velocity.x, target)
#             elif target < 0:
#                 vx = min(self.velocity.x, target)
#             else:
#                 vx = self.velocity.x
#         else:
#             vx = self.velocity.x

#         self.set_velocity(vx, None)

#     def load(self, data, add_map=None):
#         if add_map is None:
#             add_map = {}

#         map_ = {
#             "IA": "IA",
#             "auto_jump": "auto_jump",
#         }
#         map_.update(add_map)
        
#         self.inventory = inventory.Entity_Inventory(self)
#         self.inventory = self.inventory.load(data.get("inventory", None))
        
#         if super().load(data, add_map) is None:
#             return None
#         return self
    
#     def to_json(self, type_="Mob", dict_=None):
#         if dict_ is None:
#             dict_ = {}

#         data = {
#             "IA": self.IA,
#             "auto_jump": self.auto_jump,
#             "inventory": self.inventory.to_json() if self.inventory else None
#         }

#         data.update(dict_)
        
#         return super().to_json(type_, data)
    

# class MobHumanoid(Mob):
#     def __init__(self, rect, inventory=None, world=None, name="Unamed entity", health=20, max_health=20, IA=True, spawn_point=None,
#                  leg_texture: TextureType = None, 
#                  arm_texture: TextureType = None, 
#                  body_texture: TextureType = None, 
#                  head_texture: TextureType = None
#                  ):
#         super().__init__(rect, inventory, world, name, health, max_health, IA, spawn_point)
#         self.init_texture(head_texture, body_texture, leg_texture, arm_texture)

#         self.arm_angle = 0

#     def init_texture(self, head_texture, body_texture, leg_texture, arm_texture):

#         def build(tex, size):
#             base = pygame.transform.scale(tex, size)
#             flipped = pygame.transform.flip(base, True, False)

#             return {
#                 "right": base,
#                 "left": flipped
#             }

#         def tint_pack(tex_dict, color):
#             return {
#                 "right": tint_surface(tex_dict["right"], color),
#                 "left": tint_surface(tex_dict["left"], color)
#             }

#         # -------------------------
#         # BASE SIZES
#         # -------------------------
#         head_size = (self.rect.width - 4, self.rect.width - 4)
#         body_size = (self.rect.width, self.rect.width)
#         leg_size = ((self.rect.width - 2) // 2, self.rect.width)
#         arm_size = (self.rect.width // 2, self.rect.width)

#         # -------------------------
#         # BASE TEXTURES
#         # -------------------------
#         self.textures = {
#             "head": build(context.get_resource_pack().texture_manager().get_texture(head_texture), head_size),
#             "body": build(context.get_resource_pack().texture_manager().get_texture(body_texture), body_size),
#             "leg": build(context.get_resource_pack().texture_manager().get_texture(leg_texture), leg_size),
#             "arm": build(context.get_resource_pack().texture_manager().get_texture(arm_texture), arm_size),
#         }

#         # -------------------------
#         # RED VARIANT (exemple)
#         # -------------------------
#         red_color = (200, 100, 100)

#         self.textures_red = {
#             "head": tint_pack(self.textures["head"], red_color),
#             "body": tint_pack(self.textures["body"], red_color),
#             "leg": tint_pack(self.textures["leg"], red_color),
#             "arm": tint_pack(self.textures["arm"], red_color),
#         }

#         self.textures_outline = {}

#         for part in self.textures:

#             self.textures_outline[part] = {
#                 "right": create_outline_surface(
#                     self.textures[part]["right"]
#                 ),
#                 "left": create_outline_surface(
#                     self.textures[part]["left"]
#                 )
#             }

#     def render(self, screen, cam_rect, outline=False):

#         gap_outline = 3 if outline else 0

#         # 🎯 Gestion du clignotement (effet Terraria)
#         light = self.world.get_entity_light(self)
#         brightness = light / 15

#         use_red = False
#         if self.is_taking_damage:
#             # clignote rapidement
#             if int(self.annim_damage_time * 20) % 2 == 0:
#                 use_red = True

#         if outline:
#             tex = self.textures_outline
#         else:
#             tex = self.textures_red if use_red else self.textures

#         orientation = self.get_orientation()
#         head = tex["head"][orientation]
#         body = tex["body"][orientation]
#         leg  = tex["leg"][orientation]
#         arm  = tex["arm"][orientation]

#         head = apply_brightness(head, brightness)
#         body = apply_brightness(body, brightness)
#         leg = apply_brightness(leg, brightness)
#         arm = apply_brightness(arm, brightness)

#         # =========================
#         # HEAD (avec world_to_screen)
#         draw_x, draw_y = game_property.world_to_screen(
#             self.rect.x, self.rect.y, self.rect.height, cam_rect
#         )
#         draw_x += 2
#         draw_y += 4
#         if head:
#             screen.blit(
#                 head,
#                 (
#                     draw_x - gap_outline,
#                     draw_y - gap_outline
#                 )
#             )

#         # =========================
#         # BASE POSITION (évite recalculs)
#         base_x = self.rect.x - cam_rect.x
#         base_y = cam_rect.height - (self.rect.y - cam_rect.y) - self.rect.height

#         # =========================
#         # BODY
#         if body:

#             pos = (
#                 base_x - gap_outline,
#                 base_y + self.rect.width - gap_outline
#             )

#             screen.blit(body, pos)

#         # =========================
#         # LEG
#         if leg:

#             pos = (
#                 base_x + 2 - gap_outline,
#                 base_y + self.rect.width * 2 - gap_outline
#             )

#             screen.blit(leg, pos)

#             pos = (
#                 base_x + 2 + (self.rect.width - 4) // 2 - gap_outline,
#                 base_y + self.rect.width * 2 - gap_outline
#             )

#             screen.blit(leg, pos)

#         # =========================
#         # ARM

#         if self.get_orientation() == "left":
#             arm_x = base_x + self.rect.width // 2
#             angle = -self.arm_angle
#         else:
#             arm_x = base_x
#             angle = self.arm_angle

#         arm_y = base_y + self.rect.width

#         if arm:
#             # Position de l'épaule
#             pivot = pygame.Vector2(
#                 arm_x + arm.get_width() // 2,
#                 arm_y
#             )

#             # Point de rotation dans le sprite
#             offset = pygame.Vector2(
#                 0,
#                 arm.get_height() / 2
#             )

#             rotated_arm, arm_rect = rotate_around_pivot(
#                 arm,
#                 angle,
#                 pivot,
#                 offset
#             )

#             screen.blit(rotated_arm, (
#                 arm_rect.x - gap_outline,
#                 arm_rect.y - gap_outline
#             ))

#         super().render(screen, cam_rect, None)


# class Zombie(MobHumanoid):
#     DETECTION_DISTANCE = game_property.TILE_SIZE * 20

#     def __init__(self, rect=None, world=None, name="Unamed entity", health=20, max_health=20, moving=True, spawn_point=None):
#         if not rect:
#             rect = pygame.Rect(0, game_property.CHUNK_MAX_HEIGHT * game_property.TILE_SIZE, game_property.TILE_SIZE - 5, game_property.TILE_SIZE * 2.5)
#         super().__init__(rect, None, world, name, health, max_health, moving, spawn_point,
#                          leg_texture=TextureType.ZOMBIE_LEG,
#                          arm_texture=TextureType.ZOMBIE_ARM,
#                          body_texture=TextureType.ZOMBIE_BODY,
#                          head_texture=TextureType.ZOMBIE_HEAD,
#                          )

#         self.attack_cooldown = 0
    
#     def update(self, dt):
#         self.detected_player = self.get_nearest_player()

#         self.attack_cooldown -= dt

#         # Animation du bras
#         if abs(self.velocity.x) > 5:
#             # Bras levé devant quand il marche
#             self.arm_angle = 90 + math.sin(self.walk_animation) * 10
#         else:
#             # Bras le long du corps au repos
#             self.arm_angle = 0

#         # Aucun joueur à portée -> déplacement aléatoire
#         if self.detected_player is None:
#             return super().update(dt)

#         # Joueur détecté -> le poursuivre
#         else:
#             # Bord droit du zombie -> bord gauche du joueur
#             ATTACK_RANGE = 10

#             ARM_REACH = 18

#             # Création de la hitbox des bras
#             if self.orientation == "right":
#                 attack_rect = pygame.Rect(
#                     self.rect.right,
#                     self.rect.y - 10,
#                     ARM_REACH,
#                     self.rect.height + 20
#                 )
#             else:
#                 attack_rect = pygame.Rect(
#                     self.rect.left - ARM_REACH,
#                     self.rect.y - 10,
#                     ARM_REACH,
#                     self.rect.height + 20
#                 )


#             # Le joueur est à portée du bras
#             if attack_rect.colliderect(self.detected_player.rect):

#                 self.move_direction = 0

#                 if self.attack_cooldown <= 0:
#                     self.attack(self.detected_player)
#                     self.attack_cooldown = 0.8


#             # Sinon on poursuit le joueur
#             else:

#                 # Joueur à droite
#                 if self.rect.centerx < self.detected_player.rect.centerx:
#                     distance = self.detected_player.rect.left - self.rect.right

#                     if distance > ATTACK_RANGE:
#                         self.move_direction = 1
#                     else:
#                         self.move_direction = 0


#                 # Joueur à gauche
#                 else:
#                     distance = self.rect.left - self.detected_player.rect.right

#                     if distance > ATTACK_RANGE:
#                         self.move_direction = -1
#                     else:
#                         self.move_direction = 0
            
#             super().apply_horizontal_target()

#             super().apply_auto_jump()

#         return super().update(dt)
        
#     def attack(self, player):
#         # apply damage
#         self.world.apply_damage_to_entity(player, 15, self.move_direction, self)

#         print("Zombie attacks player!", player.get_name())
#         pass

#     def set_orientation(self, orientation):
#         if super().set_orientation(orientation):
#             self.update_texture()

#     def update_texture(self):
#         self.head_texture = context.get_resource_pack().texture_manager().get_texture(TextureType.ZOMBIE_HEAD)
#         self.head_texture = pygame.transform.scale(self.head_texture, (self.rect.width- 4, self.rect.width - 4))

#         self.body_texture = context.get_resource_pack().texture_manager().get_texture(TextureType.ZOMBIE_BODY)
#         self.body_texture = pygame.transform.scale(self.body_texture, (self.rect.width, self.rect.width))

#         self.leg_texture = context.get_resource_pack().texture_manager().get_texture(TextureType.ZOMBIE_LEG)
#         self.leg_texture = pygame.transform.scale(self.leg_texture, (self.rect.width - 4, self.rect.width))
        
#         self.arm_texture = context.get_resource_pack().texture_manager().get_texture(TextureType.ZOMBIE_ARM)
#         self.arm_texture = pygame.transform.scale(self.arm_texture, (self.rect.width // 2, self.rect.width))

#         if self.orientation == "right":
#             self.head_texture = pygame.transform.flip(self.head_texture, True, False)
#             self.body_texture = pygame.transform.flip(self.body_texture, True, False)
#             self.leg_texture = pygame.transform.flip(self.leg_texture, True, False)
#             self.arm_texture = pygame.transform.flip(self.arm_texture, True, False)
        
#         self.head_texture_red = tint_surface(self.head_texture, (200, 100, 100))
#         self.body_texture_red = tint_surface(self.body_texture, (200, 100, 100))
#         self.leg_texture_red = tint_surface(self.leg_texture, (200, 100, 100))
#         self.arm_texture_red = tint_surface(self.arm_texture, (200, 100, 100))

#     def to_json(self, type_="Zombie", dict_=None):
#         if dict_ is None:
#             dict_ = {}

#         data = {
            
#         }

#         data.update(dict_)
        
#         return super().to_json(type_, data)
        
#     def __str__(self):
#         return f"Zombie(pos:{self.get_pos_tile()})"

# class Skeleton(MobHumanoid):
#     DETECTION_DISTANCE = game_property.TILE_SIZE * 15

#     MIN_DISTANCE = game_property.TILE_SIZE * 0.5   # distance minimale (il recule si trop proche)
#     SHOOT_DISTANCE = game_property.TILE_SIZE * 9 # commence à bander l'arc

#     def __init__(self, rect=None, world=None, name="Unamed entity", health=20, max_health=20, IA=True, spawn_point=None):
#         if not rect:
#             rect = pygame.Rect(0, game_property.CHUNK_MAX_HEIGHT * game_property.TILE_SIZE, game_property.TILE_SIZE - 5, game_property.TILE_SIZE * 2.5)
#         super().__init__(rect, inventory=None, world=world, name=name, health=health, max_health=max_health, IA=IA, spawn_point=spawn_point,
#                          leg_texture=TextureType.SKELETON_LEG,
#                          arm_texture=TextureType.SKELETON_ARM,
#                          body_texture=TextureType.SKELETON_BODY,
#                          head_texture=TextureType.SKELETON_HEAD,
#                          )
#         self.update_texture()
#         self.inventory = inventory.Entity_Inventory(self, size=1)

#         self.inventory.add_item(inventory.ItemStack(game_type.ItemProperty.BOW, 1, 999))

#         self.timer_draw_bow = 0
#         self.attack_cooldown = 0
#         self.is_drawing_bow = False

#     def render(self, screen, cam_rect):
#         super().render(screen, cam_rect)

#     def update(self, dt):

#         self.attack_cooldown -= dt
#         self.timer_draw_bow -= dt

#         bow = self.inventory.get_item(0)

#         if self.has_bow():

#             player = self.get_nearest_player()

#             if player:

#                 distance = self.rect.centerx - player.rect.centerx
#                 abs_distance = abs(distance)


#                 # Trop proche -> reculer
#                 if abs_distance < self.MIN_DISTANCE:

#                     self.is_drawing_bow = False
#                     bow.used = False

#                     if distance > 0:
#                         self.move_direction = 1
#                     else:
#                         self.move_direction = -1


#                 # Trop loin -> avancer
#                 elif abs_distance > self.SHOOT_DISTANCE:

#                     self.is_drawing_bow = False
#                     bow.used = False

#                     if distance > 0:
#                         self.move_direction = -1
#                     else:
#                         self.move_direction = 1


#                 # Bonne distance -> tirer
#                 else:

#                     self.move_direction = 0

#                     self.try_use_bow()


#             else:
#                 self.attack_cooldown = 0
#                 self.is_drawing_bow = False

#                 if bow:
#                     bow.used = False


#         return super().update(dt)
    
#     def try_use_bow(self):
#         bow = self.inventory.get_item(0)

#         if bow is None:
#             return

#         # Attendre le cooldown
#         if self.attack_cooldown > 0:
#             return

#         # Début de l'armement
#         if not self.is_drawing_bow:
#             self.is_drawing_bow = True
#             self.timer_draw_bow = 0.7
#             bow.used = True
#             return

#         # Arc encore en train d'être armé
#         if self.timer_draw_bow > 0:
#             return

#         # Tir
#         bow.used = False
#         self.is_drawing_bow = False
#         self.attack_cooldown = 0.2

#         self.use_bow()


#     def use_bow(self):
#         bow = self.inventory.get_item(0)

#         if bow is None:
#             return

#         player = self.get_nearest_player()

#         if player is None:
#             return

#         origin = pygame.Vector2(self.rect.center)
#         target = pygame.Vector2(
#             player.rect.centerx,
#             player.rect.bottom
#         )

#         dx = target.x - origin.x
#         dy = target.y - origin.y

#         speed = 30
#         gravity = game_property.GRAVITY

#         # discriminant
#         discriminant = (
#             speed**4
#             - gravity * (gravity * dx**2 + 2 * dy * speed**2)
#         )

#         # impossible de toucher avec cette vitesse
#         if discriminant < 0:
#             # tir direct si trop loin
#             direction = (target - origin).normalize()
#             velocity = direction * speed

#         else:
#             # angle de tir (trajectoire basse)
#             angle = math.atan(
#                 (
#                     speed**2 - math.sqrt(discriminant)
#                 )
#                 /
#                 (gravity * dx)
#             )

#             # correction si joueur à gauche
#             if dx < 0:
#                 angle += math.pi

#             velocity = pygame.Vector2(
#                 math.cos(angle) * speed,
#                 -math.sin(angle) * speed
#             )


#         arrow = Arrow(
#             origin,
#             velocity,
#             self,
#             self.world,
#             can_be_picked=False
#         )

#         self.world.create_entity(arrow)

    
#     def has_bow(self):
#         item = self.inventory.get_item(0)
        
#         if item:
#             item_property = item.item_property

#             if isinstance(item_property, game_type.Tool):

#                 if isinstance(item_property, game_type.Bow_tool):
#                     return True
#         return False
    
#     def render(self, screen, cam_rect):

#         # =========================
#         # BASE POSITION (évite recalculs)
#         base_x = self.rect.x - cam_rect.x
#         base_y = cam_rect.height - (self.rect.y - cam_rect.y) - self.rect.height

#         orientation = self.get_orientation()

#         # =========================
#         # ITEM / ARME
#         item = self.inventory.get_item(0)

#         if item:
#             item_property = item.item_property

#             if isinstance(item_property, game_type.Tool):

#                 if isinstance(item_property, game_type.Bow_tool):
#                     texture = item.get_texture()

#                     self.arm_angle = 50

#                     if texture:
#                         weapon_size = int(self.rect.width * 1.8)
#                         texture = pygame.transform.scale(texture, (weapon_size, weapon_size))

#                         # 🎯 position main
#                         if orientation == "right":
#                             hand_x = base_x + int(self.rect.width * 0.75)
#                         else:
#                             hand_x = base_x + int(self.rect.width * 0.25)

#                         hand_y = base_y + int(self.rect.width * 1.2)

#                         # 🎯 flip
#                         if orientation == "left":
#                             texture = pygame.transform.flip(texture, True, False)

#                         # 🎯 pivot
#                         if orientation == "right":
#                             offset = pygame.Vector2(weapon_size * 0.2, 0)
#                         else:
#                             offset = pygame.Vector2(-weapon_size * 0.2, 0)

#                         angle = -30 * self.get_int_direction()

#                         pivot = pygame.Vector2(hand_x, hand_y)

#                         rotated_image, rotated_rect = rotate_around_pivot(
#                             texture,
#                             angle,
#                             pivot,
#                             offset
#                         )

#                         screen.blit(rotated_image, rotated_rect.topleft)
#             else:
#                 self.arm_angle = 20
#         else:
#             self.arm_angle = 50

#         super().render(screen, cam_rect)
    
#     def to_json(self, type_="Skeleton", dict_=None):
#         if dict_ is None:
#             dict_ = {}

#         data = {
            
#         }

#         data.update(dict_)
        
#         return super().to_json(type_, data)
        
#     def __str__(self):
#         return f"Skeleton(pos:{self.get_pos_tile()})"
 
 
# =====================================================================
#  ENTITÉ EN PARTIES (indépendante, n'hérite pas de Entity)
# =====================================================================
class PartEntity:
    """Base d'une partie : position relative + taille."""
 
    kind = "part"
 
    def __init__(self, offset=(0, 0), size=(16, 16), name="part", visible=True):
        self.offset = pygame.Vector2(offset)
        self.size = (int(size[0]), int(size[1]))
        self.name = name
        self.visible = visible
        self.parent = None  # renseigné par EntityParted.add_part
 
    def get_local_rect(self) -> pygame.Rect:
        """Rect relatif à l'origine de l'entité, miroir appliqué."""
        w, h = self.size
        x = int(self.offset.x)
        if self.parent is not None and self.parent.flip_x:
            x = -x - w
        return pygame.Rect(x, int(self.offset.y), w, h)

    def get_world_rect(self) -> pygame.Rect:
        ox, oy = self.parent.origin if self.parent else (0, 0)
        return self.get_local_rect().move(ox, oy)
 
 
class TexturePart(PartEntity):
    kind = "texture"

    def __init__(self, texture_type=None, offset=(0, 0), size=None, name="texture_part",
                 color=(255, 255, 255), z_index=0, alpha=255, flip_x=False, flip_y=False,
                 visible=True, angle=0, pivot=(0, 0), attach_to=None):

        texture = context.get_resource_pack().texture_manager().get_texture(texture_type)
        if size is None:                                   # la taille doit exister AVANT super().__init__
            size = texture.get_size() if texture else (16, 16)
        super().__init__(offset, size, name, visible)

        self._rot_cache = {}                               # AVANT set_texture (qui l'utilise)
        self.flip_x = False
        self.flip_y = False
        self.set_texture(texture)

        self.texture_name = str(texture_type)
        self.color = color
        self.z_index = z_index
        self.alpha = alpha

        self.angle = angle          # degrés, sens anti-horaire
        self.pivot = pygame.Vector2(pivot)
        self.attach_to = attach_to

        self.set_flip(flip_x, flip_y)

    def set_texture(self, texture):
        self.texture = texture
        self.base_texture = pygame.transform.scale(texture, self.size) if texture else None
        self._refresh_texture()                            # garde le flip propre + le miroir de l'entité

    def _mirrored(self) -> bool:
        return self.parent is not None and self.parent.flip_x

    def _refresh_texture(self):
        """Reconstruit la texture affichée (flip propre à la part XOR flip de l'entité)."""
        if self.base_texture:
            fx = self.flip_x != self._mirrored()
            self.visible_texture = pygame.transform.flip(self.base_texture, fx, self.flip_y)
        else:
            self.visible_texture = None
        self._rot_cache.clear()

    def set_flip(self, x=False, y=False):
        if x != self.flip_x or y != self.flip_y:
            self.flip_x, self.flip_y = x, y
            self._refresh_texture()

    def set_angle(self, angle):
        self.angle = angle % 360

    def _get_rotated(self, angle):                         # une seule version, avec le paramètre
        key = round(angle) % 360
        img = self._rot_cache.get(key)
        if img is None:
            img = pygame.transform.rotate(self.visible_texture, key)
            if len(self._rot_cache) > 360:
                self._rot_cache.clear()
            self._rot_cache[key] = img
        return img

    def render(self, screen, cam_rect, brightness=1.0, entity_alpha=255, offset=(0, 0)):
        if not self.visible:
            return

        rect = self.get_world_rect()
        draw_x, draw_y = game_property.world_to_screen(rect.x, rect.y, rect.height, cam_rect)
        draw_x += offset[0]
        draw_y -= offset[1]

        alpha = int(self.alpha * entity_alpha / 255)
        shade = int(255 * brightness)

        if self.visible_texture:
            center, angle = self._rotate_point(self._screen_center(cam_rect, offset), cam_rect, offset)

            img = self._get_rotated(angle) if angle else self.visible_texture
            tex = img.copy()
            tex.fill((shade, shade, shade, 255), special_flags=pygame.BLEND_RGB_MULT)
            tex.set_alpha(alpha)

            screen.blit(tex, (round(center.x - tex.get_width() / 2),
                            round(center.y - tex.get_height() / 2)))
    
    def _screen_center(self, cam_rect, offset):
        rect = self.get_world_rect()
        x, y = game_property.world_to_screen(rect.x, rect.y, rect.height, cam_rect)
        return pygame.Vector2(x + offset[0] + self.size[0] / 2,
                              y - offset[1] + self.size[1] / 2)

    def _own_rotation(self):
        if self._mirrored():
            return -self.angle, pygame.Vector2(-self.pivot.x, self.pivot.y)
        return self.angle, self.pivot

    def _rotate_point(self, point, cam_rect, offset):
        """Applique à `point` la rotation de cette part, puis celle de la part dont elle dépend.
        Renvoie (nouveau_point, angle_total)."""
        angle, pivot = self._own_rotation()
        if angle:
            pivot_screen = self._screen_center(cam_rect, offset) + pivot
            point = pivot_screen + (point - pivot_screen).rotate(-round(angle))

        parent = self.parent.get_part(self.attach_to) if (self.attach_to and self.parent) else None
        if parent is not None and parent is not self:
            point, parent_angle = parent._rotate_point(point, cam_rect, offset)
            angle += parent_angle
        return point, angle
 
 
class CollisionPart(PartEntity):
    """Partie uniquement physique (hitbox), invisible sauf en debug."""
 
    kind = "collision"
 
    def __init__(self, offset=(0, 0), size=(16, 16), name="collision_part",
                 solid=True, tag=None, visible=True):
        super().__init__(offset, size, name, visible)
        self.solid = solid
        self.tag = tag      # ex: "head", "feet", "weak_point"
 
    def render_hit_box(self, screen, cam_rect, color=(255, 0, 0), width=1):
        rect = self.get_world_rect()
        draw_x, draw_y = game_property.world_to_screen(rect.x, rect.y, rect.height, cam_rect)
        pygame.draw.rect(screen, color, (draw_x, draw_y, rect.width, rect.height), width)
 

class EntityBis:
    def __init__(self, world, pos=(0, 0), parts=None, name="Unamed entity", 
                 display_name=None, anim_file=None, lifetime=None, speed=None):
        self.world = world
        self.pos = pygame.Vector2(pos)

        self.uuid = uuid.uuid4()
        self.is_alive = True
        self.display_name = display_name
        self.name = name
        
        self.spawn_time = pygame.time.get_ticks()
        self.on_ground = False
        self.velocity = pygame.Vector2(0, 0)
        if not speed:
            speed = game_property.ENTITY_SPEED
        self.speed = speed

        self.temp_rect = None
        self.attached_entities = []
        self.attached_to = None
        self.alpha_texture = 255

        self.parts = parts or []
        for part in self.parts:
            part.parent = self   

        self.flip_x = False
        self.local_bounds = pygame.Rect(0, 0, 0, 0)
        self.rect = pygame.Rect(0, 0, 0, 0)
        self._recompute_bounds()

        clips = AnimationClip.load_file(anim_file) if anim_file else {}
        self.animator = Animator(self.parts, clips)
        self.animator.play("idle")
        self.in_liquid = False

        self.action_ctx = {}
        self.animator.on_event = self._on_animation_event
        self.flying = False

        self.lifetime = lifetime
        self.age = 0.0
        self.fly_speed = self.speed
        self.auto_flip = True

        self._hold_name = None
        self._hold_timer = 0.0
        self.drops = []

    #
    # ORIENTATION
    #

    def set_flip(self, x: bool):
        if self.flip_x != x:
            self.flip_x = x
            self.update_flip()

    def get_flip(self) -> bool:
        return self.flip_x

    def update_flip(self):
        for part in self.parts:
            if part.kind == "texture":
                part._refresh_texture()
        self._recompute_bounds()

    def add_drop(self, itemStack):
        self.drops.append(itemStack)

    def remove_drop(self, itemStack):
        if itemStack in self.drops:
            self.drops.remove(itemStack)

    #
    # MOVEMENT
    #

    @property
    def origin(self):
        """Point d'ancrage entier : base des offsets de toutes les parts."""
        return (round(self.pos.x), round(self.pos.y))

    def _recompute_bounds(self):
        rects = [p.get_local_rect() for p in self.hitboxes()]
        self.local_bounds = rects[0].unionall(rects[1:]) if rects else pygame.Rect(0, 0, 0, 0)
        self.rect.size = self.local_bounds.size
        self._sync_rect()

    def _sync_rect(self):
        ox, oy = self.origin
        self.rect.x = ox + self.local_bounds.x
        self.rect.y = oy + self.local_bounds.y

    def bounding_rect(self):
        return self.rect

    def get_center(self) -> tuple:
        return self.rect.center

    def hitboxes(self, solid_only=False, tag=None):
        return [
            p for p in self.parts
            if p.kind == "collision"
            and (not solid_only or p.solid)
            and (tag is None or p.tag == tag)
        ]

    def bounding_rect(self):
        """Rect englobant toutes les hitbox : utile en broad-phase (entité vs entité)."""
        rects = [p.get_world_rect() for p in self.hitboxes()]
        return rects[0].unionall(rects[1:]) if rects else self.rect

    def get_visual_rect(self):
        rects = [p.get_world_rect() for p in self.parts if p.visible]
        return rects[0].unionall(rects[1:]) if rects else self.rect

    def _solid_rects_near(self, rect):
        return self.world.get_solid_rects_in(rect)

    def _collides_at(self, dx=0, dy=0):
        for part in self.hitboxes(solid_only=True):
            if self.world.is_collide_at(part.get_world_rect().move(dx, dy)):
                return True
        return False

    def tp(self, x, y):
        self.pos.x = x
        self.pos.y = y
        self._sync_rect()

    def tp_tile(self, x, y):
        return self.tp(x * game_property.TILE_SIZE + game_property.TILE_SIZE // 2, y * game_property.TILE_SIZE)

    def get_pos(self) -> tuple:
        return (self.pos.x, self.pos.y)
        
    def get_pos_tile(self) -> tuple:
        return (
            round(self.pos.x / game_property.TILE_SIZE, 2),
            round(self.pos.y / game_property.TILE_SIZE, 2)
        )

    def jump(self, force):
        self.add_velocity(0, force)
        self.on_ground = False
    
    def add_velocity(self, vx, vy):
        self.velocity.x += (vx * self.speed)
        self.velocity.y += (vy * self.speed)

    def set_velocity(self, vx, vy):
        if vx:
            self.velocity.x = vx
        if vy:
            self.velocity.y = vy

    #
    # PARTS
    #

    def add_part(self, part):
        part.parent = self
        self.animator.add_part(part)
        self.parts.append(part)
        self.parts.sort(key=lambda p: getattr(p, "z_index", 0))
        if part.kind == "texture":
            part._refresh_texture()
        else:
            self._recompute_bounds()

    def remove_part(self, name):
        part = self.animator.remove_part(name)
        if part is None:
            part = self.get_part(name)
        if part:
            part.parent = None
            self.parts.remove(part)
            if part.kind == "collision":
                self._recompute_bounds()
        return part

    def get_part(self, name) -> PartEntity:
        for part in self.parts:
            if part.name == name:
                return part
        return None

    #
    # BASE FUNCTIONS
    #

    def attach_self(self, parent):
        """Se plante dans `parent` : le parent déplacera cette entité."""
        self.attached_to = parent
        parent.attached_entities.append(self)
        self.velocity.update(0, 0)

    def translate(self, dx, dy):
        """Déplace l'entité et celles qui lui sont attachées."""
        self.pos += (dx, dy)
        self._sync_rect()
        for entity in self.attached_entities:
            entity.translate(dx, dy)

    def tp(self, x, y):
        delta = pygame.Vector2(x, y) - self.pos
        self.translate(delta.x, delta.y)

    def get_uuid(self):
        return self.uuid

    def kill(self):
        for itemStack in self.drops:
            self.drop_item(itemStack, random.choice([2, 1, 0, -1, -2]))
        self.is_alive = False
        for entity in self.attached_entities:
            entity.kill()

    def is_valid(self): 
        if self.world:
            if self.world.contains_entity(self):
                return True
        return False

    def get_name(self):
        return self.name

    def get_anim_direction(self):
        if self.flip_x:
            return -1
        else:
            return 1
    
    #
    # UPDATES
    #

    def update(self, dt, update_lifetime=True):
        if update_lifetime and self.lifetime != None:
            self.age += dt
            if self.age >= self.lifetime:
                self.kill()
                return

        if self.attached_to is not None:
            return
        start = self.pos.copy()
        self._apply_gravity(dt)

        if self.flying:
            pass
        elif self.in_liquid:
            self.velocity *= 0.84
        else:
            self.velocity.x *= 0.9

        # ----- HORIZONTAL -----
        if self._move_axis(0, self.velocity.x * dt):
            self.velocity.x = 0

        # ----- VERTICAL -----
        was_on_ground = self.on_ground
        impact = self.velocity.y
        if self._move_axis(1, self.velocity.y * dt):
            if impact < 0 and not was_on_ground:          # atterrissage
                self.apply_fall_dammage(pygame.Vector2(0, impact))
            self.velocity.y = 0

        # sol = on ne monte pas et un pixel plus bas est bloqué
        self.on_ground = self.velocity.y <= 0 and self._collides_at(0, -1)

        delta = self.pos - start
        if delta.length_squared() > 0:
            for entity in self.attached_entities:
                entity.translate(delta.x, delta.y)

        self._update_animation(dt)

    def _apply_gravity(self, dt):
        if self.flying:
            return
        if not self.on_ground:
            self.add_velocity(0, -game_property.GRAVITY * dt)
        else:
            self.velocity.y = 0

    def _move_and_collide(self, dt):
        self.on_ground = False

        if self._move_axis(0, self.velocity.x * dt):
            self.velocity.x = 0

        if self._move_axis(1, self.velocity.y * dt):
            if self.velocity.y < 0:       # on tombait → on touche le sol
                self.on_ground = True
                self.apply_fall_dammage(self.velocity.copy())
            self.velocity.y = 0

    def _move_axis(self, axis, amount):
        """Avance sur un axe (0=x, 1=y), collé au bloc si on est bloqué. Renvoie True si bloqué."""
        if amount == 0:
            return False

        cur = round(self.pos[axis])
        delta = round(self.pos[axis] + amount) - cur   # nombre de pixels entiers à parcourir

        if delta == 0:                                  # mouvement sous-pixel : on l'accumule
            self.pos[axis] += amount
            self._sync_rect()
            return False

        sign = 1 if delta > 0 else -1
        one = (sign, 0) if axis == 0 else (0, sign)
        full = (delta, 0) if axis == 0 else (0, delta)

        # Chemin rapide : petit déplacement libre → on le fait d'un coup
        # (|delta| < TILE_SIZE : impossible de sauter par-dessus une tuile entière)
        if abs(delta) < game_property.TILE_SIZE and not self._collides_at(*full):
            self.pos[axis] += amount
            self._sync_rect()
            return False

        # Chemin précis : pixel par pixel jusqu'au contact
        for _ in range(abs(delta)):
            if self._collides_at(*one):
                self.pos[axis] = round(self.pos[axis])      # collé au bloc
                self._sync_rect()
                return True
            self.pos[axis] += sign
            self._sync_rect()

        self.pos[axis] += amount - delta                    # reste sous-pixel
        self._sync_rect()
        return False

    # 
    # ANNIMATION
    #

    def play_action(self, name, direction=None, **ctx) -> bool:
        """Lance une action animée. Renvoie False si impossible (déjà occupé / clip inconnu)."""
        if not self.animator.has(name):
            print(f"[play_action] clip '{name}' introuvable. Clips chargés : {list(self.animator.clips)}")
            return False
        if self.animator.busy:
            return False    
        if direction is not None and direction.x != 0:
            self.set_flip(direction.x < 0)
        self.action_ctx = {"direction": direction, **ctx}
        self.animator.speed = 1.0
        self.animator.play(name, restart=True)
        return True

    def hold_action(self, name, direction=None, duration=0.15):
        """Action continue (casser un bloc...). À appeler à chaque frame tant qu'elle dure :
        elle s'arrête d'elle-même `duration` secondes après le dernier appel."""
        if not self.animator.has(name):
            return False
        if direction is not None and direction.x != 0:
            self.set_flip(direction.x < 0)
        self._hold_name = name
        self._hold_timer = duration
        return True

    def _on_animation_event(self, event, clip_name):
        handler = getattr(self, f"_event_{event}", None)
        if handler:
            handler(self.action_ctx)

    def _update_animation(self, dt):
        self._hold_timer = max(0.0, self._hold_timer - dt)

        if self.animator.busy:
            pass                                           # action ponctuelle (attaque, tir) : prioritaire
        elif self._hold_timer > 0 and self._hold_name:
            self.animator.play(self._hold_name)            # sans restart : le clip boucle normalement
            self.animator.speed = 1.0
        elif abs(self.velocity.x) > 0.1 and self.on_ground:
            self.animator.play("walk")
            self.animator.speed = max(0.5, min(2.0, abs(self.velocity.x) / self.speed))
        else:
            self.animator.play("idle")
            self.animator.speed = 1.0

        self.animator.update(dt)

    #
    # RENDERING
    #

    def recenter_origin(self):
        """Décale toutes les parts pour que l'origine soit au milieu horizontal des hitbox.
        À appeler UNE fois, à la fin de la construction (entité non retournée)."""
        shift = -self.local_bounds.centerx
        if shift == 0:
            return

        for part in self.parts:
            part.offset.x += shift

        # l'Animator mémorise la pose de repos : il faut la décaler aussi
        for name, (off, ang, alpha) in list(self.animator.rest.items()):
            self.animator.rest[name] = (off + pygame.Vector2(shift, 0), ang, alpha)

        self._recompute_bounds()

    def render(self, screen, cam_rect):
        brightness = game_property.get_brightness(self.world.get_entity_light(self))

        if self.auto_flip:
            if self.flip_x and self.velocity.x > 0:
                self.set_flip(False)
            elif not self.flip_x and self.velocity.x < 0:
                self.set_flip(True)

        for part in self.parts:
            if isinstance(part, TexturePart):
                part.render(screen, cam_rect, brightness=brightness)

    def render_hit_box(self, screen, cam_rect, color=(255, 255, 255)):
        return self.render_hitbox(screen, cam_rect, color)
    
    def render_hitbox(self, screen, cam_rect, color=(255, 255, 255)):
        for part in self.parts:
            if isinstance(part, CollisionPart):
                part.render_hit_box(screen, cam_rect, color)

    def render_hit_box_with_rect(self, screen, cam_rect, rect, color=(255, 0, 0), width=1):
        draw_x, draw_y = game_property.world_to_screen(rect.x, rect.y, rect.height, cam_rect)
        pygame.draw.rect(screen, color, (draw_x, draw_y, rect.width, rect.height), width)

    #
    # LOGIC
    #

    def apply_fall_dammage(self, vel):
        pass

    def drop_item(self, itemStack, direction=None):
        if not itemStack:
            return

        mid_x = self.pos.x
        quart_y = self.pos.y + self.rect.height // 3 * 2

        if direction is None:
            direction = -1 if self.flip_x else 1
        
        entity = Item(self.world, itemStack, (mid_x + direction * self.rect.width, quart_y))
        
        entity.add_velocity(direction * 5, 5)
        self.world.create_entity(entity)

    def load(self, data, add_map=None):
        if add_map is None:
            add_map = {}

        mapping = {
            "uuid": "uuid",
            "x": ("pos", "x"),
            "y": ("pos", "y"),
            "vx": ("velocity", "x"),
            "vy": ("velocity", "y"),
            "name": "name",
            "speed": "speed",
            "display_name": "display_name",
        }

        mapping.update(add_map)

        # Vérification
        required = list(mapping.keys())
        missing = [k for k in required if k not in data]
        if missing:
            print(f"Champs manquants: {missing}")
            return None

        # Assignation complexe
        for key, target in mapping.items():
            if isinstance(target, tuple):
                obj, attr = target
                setattr(getattr(self, obj), attr, data[key])
            else:
                setattr(self, target, data[key])
        return self

    def to_json(self, type_="Entity", dict_=None):

        if dict_ is None:
            dict_ = {}

        data = {
            "type": type_,
            "uuid": str(self.uuid),
            "x": self.pos.x,
            "y": self.pos.y,
            "vx": self.velocity.x,
            "vy": self.velocity.y,
            "speed": self.speed,
            "display_name": self.display_name,
            "name": self.name,
        }

        data.update(dict_)   # ajoute les champs supplémentaires

        return data

class LivingEntity(EntityBis):
    def __init__(self, world, pos=(0, 0), parts=None, name="Unamed entity", display_name=None, anim_file=None, health=20, max_health=20, drops=None, collidable=True, invulnerable=False, lifetime=None):
        super().__init__(world, pos, parts, name, display_name, anim_file, lifetime)
        self.max_health = max_health
        self.health = health
        if not drops:
            drops = []
        self.drops = drops
        self.invulnerable = invulnerable
        self.knockback_timer = 0
        self.is_taking_damage = False

    def render(self, screen, cam_rect, health_bar=True):
        if health_bar and self.health < self.max_health:
            self.render_health_bar(screen, cam_rect)
        return super().render(screen, cam_rect)

    def update(self, dt, update_live=True):
        if self.health <= 0:
            self.kill()
            return

        if self.knockback_timer > 0:
            self.knockback_timer -= dt
        else:
            self.is_taking_damage = False
        
        return super().update(dt, update_live)

    def apply_damage(self, damage, dx, attacker=None):
        if not self.is_taking_damage and not self.invulnerable:
            self.health -= damage * game_property.DAMAGE_COEF

            knockback_force = 10
            vx = dx * knockback_force
            vy = 10

            self.add_velocity(vx, vy)
            
            self.is_taking_damage = True
            self.knockback_timer = 0.2

    def render_health_bar(self, screen, cam_rect, life_color=(0, 220, 0), border=(255, 255, 255), background=(60, 0, 0)):
        rect = self.rect

        # coin haut-gauche du rect à l'écran
        draw_x, draw_y = game_property.world_to_screen(rect.x, rect.y, rect.height, cam_rect)

        bar_width = 75
        bar_height = 10

        health_ratio = min(1.0, max(0.0, self.health / self.max_health))

        bar_x = draw_x + (rect.width - bar_width) // 2     # centrée sur l'entité
        bar_y = draw_y - bar_height - 4                    # 4 px au-dessus de la tête

        # fond
        pygame.draw.rect(screen, background, (bar_x, bar_y, bar_width, bar_height))

        # vie
        pygame.draw.rect(screen, life_color, (bar_x, bar_y, bar_width * health_ratio, bar_height))

        # contour
        pygame.draw.rect(screen, border, (bar_x, bar_y, bar_width, bar_height), 1)

    def apply_fall_dammage(self, vel):
        y = abs(vel.y) - 1300
        if y > 0:
            damage = y // 10
            print("Fall dammage =", damage, "velocity y=", vel.y)
            self.apply_damage(damage, 0, None)
        return super().apply_fall_dammage(vel)

    def load(self, data, add_map=None):
        if add_map is None:
            add_map = {}

        map_ = {
            "health": "health",
            "max_health": "max_health",
            "flip_x": "flip_x",
        }

        map_.update(add_map)

        if not super().load(data, map_):
            return None
        self.update_flip()

        drops_= []
        if data.get("drops", None) is not None:
            drops = data.get("drops")
            for dict_drop in drops:
                item = inventory.ItemStack()
                item.load(dict_drop)
                if item:
                    drops_.append(item)
                else:
                    return None
        else:
            return None
        return self

    def to_json(self, type_="LivingEntity", dict_=None):
        if dict_ is None:
            dict_ = {}

        drops = []
        if self.drops:
            for drop_item in self.drops:
                drops.append(drop_item.to_json())

        data = {
            "health": self.health,
            "max_health": self.max_health,
            "flip_x": self.flip_x,
            "drops": drops
        }

        data.update(dict_)

        return super().to_json(type_, data)


class Mob(LivingEntity):
    def __init__(self, world, pos=(0, 0), parts=None, name="Mob", display_name=None,
                 anim_file=None, health=20, max_health=None, drops=None,
                 collidable=True, invulnerable=False, lifetime=None):
        super().__init__(world, pos, parts, name, display_name, anim_file,
                         health, max_health or health, drops, collidable, invulnerable, lifetime)
        T = game_property.TILE_SIZE
        self.auto_flip = False
        self.walk_speed = T * 1.2
        self.jump_force = 12
        self._wander_dir = 0
        self._wander_timer = 0.0

    # ---------- utilitaires ----------

    def _face(self, direction):
        if direction != 0:
            self.set_flip(direction < 0)    # textures dessinées vers la droite

    def _walk(self, direction, speed):
        if direction == 0:
            return
        self._face(direction)
        self.velocity.x = direction * speed
        if self.on_ground and self._collides_at(direction * 2, 0):     # obstacle devant : il saute
            self.jump(self.jump_force)

    def _is_valid_target(self, e):
        return e is not None and e is not self and e.is_alive and getattr(e, "health", 1) > 0

    def _nearest_player(self, max_dist):
        me = pygame.Vector2(self.rect.center)
        best, best_d = None, max_dist ** 2
        for p in self.world.get_entities(Player):
            if not self._is_valid_target(p):
                continue
            d = (pygame.Vector2(p.rect.center) - me).length_squared()
            if d < best_d:
                best, best_d = p, d
        return best

    def _distance_to(self, e):
        return (pygame.Vector2(e.rect.center) - pygame.Vector2(self.rect.center)).length()

    # ---------- comportement ----------

    def _wander(self, dt):
        self._wander_timer -= dt
        if self._wander_timer <= 0:
            self._wander_dir = random.choice([-1, 0, 0, 1])        # 0 = il se repose
            self._wander_timer = random.uniform(1.5, 4.0)
        self._walk(self._wander_dir, self.walk_speed)

    def _think(self, dt):
        self._wander(dt)

    def on_hurt(self, damage, dx, attacker):
        pass

    def apply_damage(self, damage, dx, attacker=None):
        was_hurt = self.is_taking_damage
        super().apply_damage(damage, dx)
        if self.is_taking_damage and not was_hurt:          # le dégât a vraiment été appliqué
            self.on_hurt(damage, dx, attacker)

    def update(self, dt, update_live=True):
        if self.health > 0 and not self.is_taking_damage:   # pendant le recul, l'IA ne contrôle pas
            self._think(dt)
        return super().update(dt, update_live)

class PassiveMob(Mob):
    def __init__(self, *args, flee_time=5.0, run_speed=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.flee_time = flee_time                       # secondes de fuite après un coup
        self.run_speed = run_speed or self.walk_speed * 2.2
        self._flee_timer = 0.0
        self._flee_dir = 1
        self._flee_from = None

    def on_hurt(self, damage, dx, attacker):
        self._flee_timer = self.flee_time                # chaque coup relance le chrono
        self._flee_from = attacker
        self._flee_dir = 1 if dx >= 0 else -1            # le recul le pousse à l'opposé de l'agresseur

    def _think(self, dt):
        if self._flee_timer <= 0:
            return self._wander(dt)

        self._flee_timer -= dt
        a = self._flee_from
        if self._is_valid_target(a):                     # continue de s'éloigner si l'agresseur le suit
            self._flee_dir = 1 if self.rect.centerx >= a.rect.centerx else -1
        self._walk(self._flee_dir, self.run_speed)

class AggressiveMob(Mob):
    def __init__(self, *args, damage=3, attack_range=None, attack_cooldown=1.0,
                 chase_speed=None, sight_range=None, **kwargs):
        super().__init__(*args, **kwargs)
        T = game_property.TILE_SIZE
        self.damage = damage
        self.attack_range = T * 0.3 if attack_range is None else attack_range
        self.attack_cooldown = attack_cooldown
        self.chase_speed = chase_speed or self.walk_speed * 2
        self.sight_range = sight_range or T * 12
        self.target = None
        self._attack_timer = 0.0

    def _update_target(self, dt):
        pass                                             # défini par NeutralMob / HostileMob

    def _think(self, dt):
        self._attack_timer = max(0.0, self._attack_timer - dt)
        self._update_target(dt)

        t = self.target
        if not self._is_valid_target(t):
            self.target = None
            return self._wander(dt)

        if self.animator.busy:                           # en pleine attaque : il ne bouge pas
            self.velocity.x = 0
            return

        dir_x = 1 if t.rect.centerx >= self.rect.centerx else -1
        self._face(dir_x)

        if self.rect.inflate(self.attack_range * 2, 0).colliderect(t.rect):
            self.velocity.x = 0
            self._try_attack(t, dir_x)
        else:
            self._walk(dir_x, self.chase_speed)

    def _try_attack(self, target, dir_x):
        if self._attack_timer > 0:
            return
        self._attack_timer = self.attack_cooldown
        if self.animator.has("attack"):                  # avec animation : le coup part à l'événement 'hit'
            self.play_action("attack", direction=pygame.Vector2(dir_x, 0), target=target)
        else:
            self._do_hit(target, dir_x)

    def _event_hit(self, ctx):
        target = ctx.get("target")
        if self._is_valid_target(target):
            self._do_hit(target, 1 if ctx["direction"].x >= 0 else -1)

    def _do_hit(self, target, dir_x):
        reach = self.rect.inflate(self.attack_range * 2 + 8, 0)      # petite tolérance
        if reach.colliderect(target.rect):
            self.world.apply_damage_to_entity(target, self.damage, dir_x, self)

class NeutralMob(AggressiveMob):
    """Tranquille tant qu'on ne le frappe pas, agressif ensuite pendant `anger_time` secondes."""
    def __init__(self, *args, anger_time=15.0, **kwargs):
        super().__init__(*args, **kwargs)
        self.anger_time = anger_time
        self._anger_timer = 0.0

    def on_hurt(self, damage, dx, attacker):
        if not self._is_valid_target(attacker):
            attacker = self._nearest_player(self.sight_range)     # si le monde ne transmet pas l'agresseur
        if attacker is not None:
            self.target = attacker
            self._anger_timer = self.anger_time                   # chaque coup relance la colère

    def _update_target(self, dt):
        if self.target is None:
            return
        self._anger_timer -= dt
        if self._anger_timer <= 0 or self._distance_to(self.target) > self.sight_range * 2:
            self.target = None

class HostileMob(AggressiveMob):
    """Attaque tout joueur qui entre dans son champ de vision."""
    def __init__(self, *args, scan_interval=0.5, **kwargs):
        super().__init__(*args, **kwargs)
        self.scan_interval = scan_interval
        self._scan_timer = 0.0

    def on_hurt(self, damage, dx, attacker):
        if self._is_valid_target(attacker):
            self.target = attacker                                # riposte sur celui qui le frappe

    def _update_target(self, dt):
        self._scan_timer -= dt
        if self._scan_timer > 0:
            return
        self._scan_timer = self.scan_interval                     # on ne scanne pas à chaque frame
        if self.target is None or self._distance_to(self.target) > self.sight_range * 1.5:
            self.target = self._nearest_player(self.sight_range)


class PLAYER_TYPE:
    MALE = "male"
    FEMALE = "female"

class Player(LivingEntity):
    def __init__(self, world, pos=(0, 0), name="Player entity", display_name=None, player_type=PLAYER_TYPE.MALE):
        super().__init__(world, pos, None, name, display_name, AnimationSet.PLAYER)
        width = game_property.TILE_SIZE - 5

        type_body = TextureType.DEFAULT
        type_head = TextureType.DEFAULT
        type_arm = TextureType.DEFAULT
        type_leg = TextureType.DEFAULT

        BODY_SIZE = (width, width)
        HEAD_SIZE = (width - 4, width - 4)
        LEG_SIZE = ((width - 2) // 2, width)
        ARM_SIZE = (width // 2, width)

        BODY_OFFSET = (0, LEG_SIZE[1])
        HEAD_OFFSET = (2, BODY_OFFSET[1] + BODY_SIZE[1])
        LEFT_LEG_OFFSET = ((width - LEG_SIZE[0] * 2) // 2, 0)

        if player_type == PLAYER_TYPE.MALE:
            type_body = TextureType.PLAYER_BODY_MALE
            type_head = TextureType.PLAYER_HEAD_MALE
            type_arm = TextureType.PLAYER_ARM_MALE
            type_leg = TextureType.PLAYER_LEG_MALE
        elif player_type == PLAYER_TYPE.FEMALE:
            type_body = TextureType.PLAYER_BODY_FEMALE
            type_head = TextureType.PLAYER_HEAD_FEMALE
            HEAD_SIZE = (HEAD_SIZE[0] + 6, HEAD_SIZE[1])
            HEAD_OFFSET = (HEAD_OFFSET[0] - 6, HEAD_OFFSET[1])
            type_arm = TextureType.PLAYER_ARM_FEMALE
            type_leg = TextureType.PLAYER_LEG_FEMALE

        ITEM_OFFHAND_SIZE = (width, width)
        ITEM_OFFHAND_OFFSET = (width // 2, LEG_SIZE[1] // 3 * 2)
        LEG_PIVOT = (0, -(LEG_SIZE[1] // 2))

        self.add_part(CollisionPart(size=(width, game_property.TILE_SIZE * 2.5), name="body_hitbox"))

        self.add_part(TexturePart(texture_type=type_body, size=BODY_SIZE, offset=BODY_OFFSET, name="body_texture", z_index=1))
        self.add_part(TexturePart(texture_type=type_head, size=HEAD_SIZE, offset=HEAD_OFFSET, name="head_texture", z_index=2))
        self.add_part(TexturePart(texture_type=type_leg, size=LEG_SIZE, offset=LEFT_LEG_OFFSET, name="left_leg_texture", z_index=3, pivot=LEG_PIVOT))
        self.add_part(TexturePart(texture_type=type_leg, size=LEG_SIZE, offset=(LEFT_LEG_OFFSET[0] + LEG_SIZE[0], 0), name="right_leg_texture", z_index=4, pivot=LEG_PIVOT))

        self.add_part(TexturePart(texture_type=type_arm, size=ARM_SIZE, offset=(2, LEG_SIZE[1] + BODY_SIZE[1] - 2 - ARM_SIZE[1]), name="arm_texture", z_index=6, pivot=(0, -(width // 2) // 2), angle=0))

        self.add_part(TexturePart(texture_type=TextureType.NONE, size=ITEM_OFFHAND_SIZE, offset=ITEM_OFFHAND_OFFSET, name="item_offhand", z_index=5, attach_to="arm_texture", angle=-30))

        self.recenter_origin()

        self.inventory = inventory.Entity_Inventory(self)
        self.speed = game_property.PLAYER_SPEED

        self._held = object()
        self._held_texture = object()

    def kill(self):
        for itemStack in self.inventory.get_all_items():
            self.add_drop(itemStack)
        return super().kill()

    def _refresh_held_item(self):
        selected = self.inventory.ui.get_selected_item()
        texture = selected.get_texture() if selected else None

        if selected is self._held and texture is self._held_texture:
            return                                     # ni l'objet ni sa texture n'ont changé
        self._held = selected
        self._held_texture = texture

        item_part = self.get_part("item_offhand")
        arm_part = self.get_part("arm_texture")
        if item_part is None or arm_part is None:
            print("[Player] parts introuvables, présentes :", [p.name for p in self.parts])
            return

        if selected:
            if isinstance(selected.item_property, game_type.Bow_tool):
                self.animator.set_rest("arm_texture", angle=50)
                item_part.angle = 140
            else:
                self.animator.set_rest("arm_texture", angle=30)
            item_part.set_texture(texture)
            item_part.angle = -30
        else:
            self.animator.set_rest("arm_texture", angle=0)
            item_part.set_texture(None)

    def render(self, screen, cam_rect):
        self._refresh_held_item()
        return super().render(screen, cam_rect, False)

    def get_rect_attack(self):
        self.temp_rect = self.get_part("body_hitbox").get_world_rect().copy()
        self.temp_rect.x += self.get_anim_direction() * ATTACK_RANGE
        return self.temp_rect

    def update(self, dt):
        for entity in self.world.get_entities(Arrow):
            if not entity.stucked or not entity.can_be_picked:
                continue

            if entity.attached_to is not None:
                continue

            if self.rect.colliderect(entity.rect):

                # ajouter une flèche à l'inventaire
                self.inventory.add_item(
                    inventory.ItemStack(game_type.ItemProperty.ARROW, 1)
                )

                entity.kill()
        return super().update(dt, False)

    def try_attack(self, cam_rect):
        selected_item = self.inventory.ui.get_selected_item()
        if selected_item:
            if isinstance(selected_item.item_property, game_type.Attack_tool):
                sx, sy = pygame.mouse.get_pos()
                mx, my = game_property.screen_to_world(sx, sy, 0, cam_rect)

                direction = pygame.Vector2(mx - self.rect.centerx, my - self.rect.centery)

                if direction.length() != 0:
                    direction = direction.normalize()
                    self.attack(direction)
    
    def drop_item_index(self, itemIndex=None):
        if not itemIndex:
            item = self.inventory.ui.get_selected_item()
            itemIndex = self.inventory.ui.selected_index
        else:
            item = self.inventory.get_item(itemIndex)

        if item:
            item_ = inventory.ItemStack(item.item_property, count=1, durability=item.durability, components=item.components)
            self.drop_item(item_)
            self.inventory.delete_item(itemIndex)
    
    def use_selected_item(self, cam_rect):
        selected_item = self.inventory.ui.get_selected_item()
        if selected_item:
            if isinstance(selected_item.item_property, game_type.Tool):
                sx, sy = pygame.mouse.get_pos() 
                mx, my = game_property.screen_to_world(sx, sy, 0, cam_rect) 
                
                direction = pygame.Vector2(mx - self.rect.centerx, my - self.rect.centery)

                if direction.length() != 0:
                    direction = direction.normalize()
                    self.use_item(direction)
            elif isinstance(selected_item.item_property, game_type.Consumable):
                
                if isinstance(selected_item.item_property, game_type.Hanger_consumable):
                    self.health = min(self.health + selected_item.item_property.life_regen, self.max_health)

                self.inventory.delete_item(self.inventory.ui.selected_index)

    def stop_use_selected_item(self, cam_rect):
        selected_item = self.inventory.ui.get_selected_item()
        if selected_item:
            if isinstance(selected_item.item_property, game_type.Tool):
                sx, sy = pygame.mouse.get_pos() 
                mx, my = game_property.screen_to_world(sx, sy, 0, cam_rect) 
                
                direction = pygame.Vector2(mx - self.rect.centerx, my - self.rect.centery)

                if direction.length() != 0:
                    direction = direction.normalize()
                    self.use_item(direction)

    def render_hitbox(self, screen, cam_rect, color=(255, 255, 255)):
        if self.is_attacking():
            selected_item = self.inventory.ui.get_selected_item()
            if selected_item:
                if isinstance(selected_item.item_property, game_type.Attack_tool):
                    self.render_hit_box_with_rect(screen, cam_rect, rect=self.get_rect_attack(), color=(255, 0, 0))
        return super().render_hitbox(screen, cam_rect, color)
    
    def use_item(self, direction):
        selected_item = self.inventory.ui.get_selected_item()

        if isinstance(selected_item.item_property, game_type.Bow_tool):
            if selected_item.used:
                if not self.inventory.has_item(game_type.ItemProperty.ARROW):
                    return
                if self.play_action("shoot", direction=direction, item=selected_item):
                    selected_item.used = False
            else:
                if self.inventory.has_item(game_type.ItemProperty.ARROW):
                    selected_item.used = True

    def _event_release_arrow(self, ctx):
        """Déclenché par l'événement 'release_arrow' du clip 'shoot'."""
        if not self.inventory.has_item(game_type.ItemProperty.ARROW):
            return                                          # la flèche a disparu entre-temps
        self.inventory.delete_item_property(game_type.ItemProperty.ARROW, 1)
        ctx["item"].use()

        origin = pygame.Vector2(self.rect.center)
        arrow = Arrow((origin.x, origin.y), ctx["direction"] * 30, self, self.world)
        self.world.create_entity(arrow)

    def attack(self, direction):
        self.play_action("attack", direction=direction)

    def _event_hit(self, ctx):
        if self.is_attacking():
            selected_item = self.inventory.ui.get_selected_item()
            if selected_item:
                if isinstance(selected_item.item_property, game_type.Attack_tool):

                    entities = self.world.get_entities_by_rect(self.get_rect_attack())
                    for entity in entities:
                        if entity is not self and isinstance(entity, LivingEntity):

                            self.world.apply_damage_to_entity(entity, selected_item.item_property.get_attack_damage(), self.get_anim_direction(), self)
    
    def get_force_selected_item(self, block_property):
        item = self.get_selected_item()

        if item:

            item_pro = item.item_property
            if item_pro and block_property:
                if isinstance(item_pro, game_type.Pickaxe_tool):
                    if block_property.weakness == game_type.Pickaxe_tool:
                        return item_pro.power
                    
                if isinstance(item_pro, game_type.Axe_tool):
                    if block_property.weakness == game_type.Axe_tool:
                        return item_pro.power
        return game_property.DEFAULT_BREAK_POWER
    
    def get_selected_item(self):
        return self.inventory.get_item(self.inventory.ui.selected_index)

    def is_attacking(self):
        return self.animator.busy and self.animator.current == "attack"

    def try_attack(self, cam_rect):
        selected_item = self.inventory.ui.get_selected_item()
        if selected_item:
            if isinstance(selected_item.item_property, game_type.Attack_tool):
                sx, sy = pygame.mouse.get_pos()
                mx, my = game_property.screen_to_world(sx, sy, 0, cam_rect)

                direction = pygame.Vector2(mx - self.rect.centerx, my - self.rect.centery)

                if direction.length() != 0:
                    direction = direction.normalize()
                    self.attack(direction)

    def to_json(self, type_="Player", dict_=None):
        if dict_ is None:
            dict_ = {}

        data = {
            "inventory": self.inventory.to_json(),
        }

        data.update(dict_)
        
        return super().to_json(type_, data)

    def load(self, data, add_map=None):
        self.inventory = self.inventory.load(data.get("inventory", None))
        if self.inventory is None:
            return None
        if super().load(data, add_map) is None:
            return None
        return self


class WitherHead(EntityBis):
    def __init__(self, world, pos=(0, 0), name="Wither head", size_coef=1,
                 direction=(1, 0), owner=None, speed=None, damage=5, lifetime=6.0):
        super().__init__(world, pos, None, name, None, None, lifetime=lifetime, speed=speed)

        size = int(game_property.TILE_SIZE * size_coef)
        HEAD_SIZE = (size, size)
        off = (-(size // 2), -(size // 2))          # origine au centre

        self.add_part(CollisionPart(offset=off, size=HEAD_SIZE, name="hitbox"))
        self.add_part(TexturePart(TextureType.WITHER_LITTLE_HEAD, size=HEAD_SIZE,
                                  offset=off, name="head"))

        self.flying = True
        self.direction = pygame.Vector2(direction)
        if self.direction.length() == 0:
            self.direction = pygame.Vector2(1, 0)
        self.direction.normalize_ip()

        self.owner = owner
        self.damage = damage

    def update(self, dt, update_live=True):
        self.velocity.update(self.direction * self.fly_speed)    # vitesse constante, sans inertie
        super().update(dt, update_live)

        # bloc touché : EntityBis a remis la vitesse de cet axe à 0
        if (self.direction.x and not self.velocity.x) or (self.direction.y and not self.velocity.y):
            self.kill()
            return

        # entité vivante touchée
        for entity in self.world.get_entities_by_rect(self.rect):
            if entity is self or entity is self.owner or isinstance(entity, WitherHead):
                continue
            if isinstance(entity, LivingEntity):
                if self.direction.x != 0:
                    knock = 1 if self.direction.x > 0 else -1
                else:                                           # tir vertical : on repousse à l'opposé de la tête
                    knock = 1 if entity.rect.centerx >= self.rect.centerx else -1

                self.world.apply_damage_to_entity(entity, self.damage, knock, self.owner)
                self.kill()
                return

class Wither(LivingEntity):
    def __init__(self, world, pos=(0, 0), name="Unamed wither", display_name=None, health=100, drops=None, invulnerable=False, coef_size=1):
        super().__init__(world, pos, None, name, display_name, None, health, 100, drops, True, invulnerable)

        self.coef_size = coef_size

        width = int((game_property.TILE_SIZE * 3.5 // 2) * 2 * coef_size)
        height = int((game_property.TILE_SIZE * 4) * coef_size)

        BODY_CORPS_SIZE = (width // 5, height // 3)
        BODY_CORPS_OFFSET = (width // 2 - BODY_CORPS_SIZE[0] // 2, height // 8)

        BODY_PART_SIZE_1 = (width // 4, height // 8)
        BODY_PART_SIZE_2 = (width // 5, height // 10)

        BODY_TOP_SIZE = ((width // 5) * 4, height // 8)
        BODY_TOP_OFFSET = ((width // 2) - BODY_TOP_SIZE[0] // 2, BODY_CORPS_OFFSET[1] + BODY_CORPS_SIZE[1])

        self.add_part(TexturePart(TextureType.WITHER_BODY_CORPS, size=BODY_CORPS_SIZE, offset=BODY_CORPS_OFFSET, z_index=1, name="body_corps"))

        self.add_part(TexturePart(TextureType.WITHER_BODY_PART, size=BODY_PART_SIZE_1, offset=(BODY_CORPS_OFFSET[0] - BODY_PART_SIZE_1[0], BODY_CORPS_OFFSET[1] + BODY_CORPS_SIZE[1] // 2), z_index=2, name="body_part_1"))
        self.add_part(TexturePart(TextureType.WITHER_BODY_PART, size=BODY_PART_SIZE_1, offset=(BODY_CORPS_OFFSET[0] + BODY_CORPS_SIZE[0], BODY_CORPS_OFFSET[1] + BODY_CORPS_SIZE[1] // 2), z_index=3, name="body_part_2", flip_x=True))

        self.add_part(TexturePart(TextureType.WITHER_BODY_PART, size=BODY_PART_SIZE_2, offset=(BODY_CORPS_OFFSET[0] - BODY_PART_SIZE_2[0], BODY_CORPS_OFFSET[1] + BODY_CORPS_SIZE[1] // 6), z_index=4, name="body_part_3"))
        self.add_part(TexturePart(TextureType.WITHER_BODY_PART, size=BODY_PART_SIZE_2, offset=(BODY_CORPS_OFFSET[0] + BODY_CORPS_SIZE[0], BODY_CORPS_OFFSET[1] + BODY_CORPS_SIZE[1] // 6), z_index=5, name="body_part_4", flip_x=True))

        self.add_part(TexturePart(TextureType.WITHER_TOP_BODY, size=BODY_TOP_SIZE, offset=BODY_TOP_OFFSET, z_index=6, name="body_top"))

        LITTLE_HEAD_SIZE = (BODY_TOP_SIZE[0] // 3, BODY_TOP_SIZE[0] // 3)
        self.add_part(TexturePart(TextureType.WITHER_LITTLE_HEAD, size=LITTLE_HEAD_SIZE, offset=(BODY_TOP_OFFSET[0] - LITTLE_HEAD_SIZE[0] // 2, BODY_TOP_OFFSET[1] + BODY_TOP_SIZE[1] // 2), z_index=7, name="little_head_1"))
        self.add_part(TexturePart(TextureType.WITHER_LITTLE_HEAD, size=LITTLE_HEAD_SIZE, offset=(BODY_TOP_OFFSET[0] + BODY_TOP_SIZE[0] - LITTLE_HEAD_SIZE[0] // 2, BODY_TOP_OFFSET[1] + BODY_TOP_SIZE[1] // 2), z_index=8, name="little_head_2"))

        HEAD_SIZE = (BODY_TOP_SIZE[0] // 2, BODY_TOP_SIZE[0] // 2)
        HEAD_OFFSET = ((width // 2) - HEAD_SIZE[0] // 2, BODY_TOP_OFFSET[1] + BODY_TOP_SIZE[1])
        self.add_part(TexturePart(TextureType.WITHER_HEAD, size=HEAD_SIZE, offset=HEAD_OFFSET, z_index=9, name="head"))

        # HITBOX
        self.add_part(CollisionPart(offset=(0, 0), size=(width, height), name="hitbox_body"))

        self.recenter_origin()

        T = game_property.TILE_SIZE
        self.flying = True
        self.keep_distance = T * 8
        self.tolerance = T * 1.5
        self.sight_range = T * 30
        self.shoot_range = T * 16

        self.fly_speed = game_property.ENTITY_SPEED * 4 # vitesse max d'approche (px/s)
        self.retreat_speed = T * 4       # vitesse max quand il recule
        self.slow_radius = T * 6         # distance sur laquelle il ralentit avant d'arriver
        self.ramp_time = 0.6             # durée du démarrage progressif (s)
        self._ramp = 0.0

        self.head_speed = T * 8         # vitesse des têtes (px/s)
        self.shoot_cooldown = 2.0
        self._shoot_timer = 1.0
        self._retarget_timer = 0.0
        self.target = None
        self.min_above = 0                  # px : le bas du Wither reste au moins à ce niveau au-dessus du bas de la cible
        self.floor_margin = T * 1           # il commence à remonter à cette distance de la limite

    def update(self, dt, update_live=True):
        self._retarget_timer -= dt
        if self._retarget_timer <= 0 or not self._valid_target(self.target):
            self.target = self._find_target()
            self._retarget_timer = 0.5      # on ne rescanne pas le monde à chaque frame

        self._ai_move(dt)
        self._ai_shoot(dt)
        return super().update(dt, update_live)

    def _floor_gap(self):
        """Distance au-dessus de la limite (négatif = déjà trop bas). None sans cible."""
        if not self.target:
            return None
        return self.rect.y - (self.target.rect.y + self.min_above)

    def _apply_floor(self, desired):
        gap = self._floor_gap()
        if gap is None:
            return
        if gap < self.floor_margin:
            lift = self.fly_speed * game_property._smoothstep((self.floor_margin - gap) / self.floor_margin)
            desired.y = max(desired.y, lift)

    def _clamp_floor(self, dt):
        gap = self._floor_gap()
        if gap is None:
            return
        max_down = max(0.0, gap) / max(dt, 1e-3)
        self.velocity.y = max(self.velocity.y, -max_down)

    def _valid_target(self, e):
        return (e is not None and e is not self and e.is_alive
                and isinstance(e, LivingEntity)) # and not isinstance(e, Wither)

    def _find_target(self):
        mine = pygame.Vector2(self.rect.center)
        best, best_d = None, self.sight_range ** 2
        for e in self.world.get_entities(LivingEntity):
            if not self._valid_target(e):
                continue
            d = (pygame.Vector2(e.rect.center) - mine).length_squared()
            if d < best_d:
                best, best_d = e, d
        return best

    def _ai_move(self, dt):
        desired = pygame.Vector2(0, 0)

        if self.target:
            to_target = pygame.Vector2(self.target.rect.center) - pygame.Vector2(self.rect.center)
            dist = to_target.length()

            if abs(to_target.x) > 8:
                self.set_flip(to_target.x < 0)

            if dist > 0:
                error = dist - self.keep_distance
                if error > self.tolerance:                      # trop loin : il approche
                    k = game_property._smoothstep((error - self.tolerance) / self.slow_radius)     # ease out
                    desired = to_target.normalize() * (self.fly_speed * k)
                elif error < -self.tolerance:                   # trop près : il recule
                    k = game_property._smoothstep((-error - self.tolerance) / self.slow_radius)
                    desired = -to_target.normalize() * (self.retreat_speed * k)

        # ease in : la vitesse monte progressivement après chaque arrêt
        moving = desired.length_squared() > 1
        step = dt / self.ramp_time
        self._ramp = min(1.0, self._ramp + step) if moving else max(0.0, self._ramp - step * 2)
        desired *= game_property._smoothstep(self._ramp)

        self._apply_floor(desired)                              # ← nouveau

        self.velocity += (desired - self.velocity) * min(1.0, 10 * dt)

        self._clamp_floor(dt) 

    def _ai_shoot(self, dt):
        self._shoot_timer -= dt
        if self._shoot_timer > 0 or not self.target:
            return

        head = self.get_part("head")
        origin = pygame.Vector2(head.get_world_rect().center)
        direction = pygame.Vector2(self.target.rect.center) - origin
        if direction.length() == 0 or direction.length() > self.shoot_range:
            return

        direction.normalize_ip()
        self.world.create_entity(WitherHead(
            self.world, (origin.x, origin.y),
            direction=direction, owner=self,
            speed=self.head_speed,
            lifetime=self.shoot_range * 1.5,
            size_coef=self.coef_size
        ))
        self._shoot_timer = self.shoot_cooldown

    def render(self, screen, cam_rect, health_bar=True):
        if health_bar:
            super().render_health_bar(screen, cam_rect, (207, 49, 235))
        return super().render(screen, cam_rect, False)

    def to_json(self, type_="Wither", dict_=None):
        return super().to_json(type_, dict_)


class Fox(PassiveMob):
    def __init__(self, world, pos=(0, 0), name="Fox entity", health=10, max_health=10):
        super().__init__(world, pos, None, name, None, AnimationSet.FOX, health, max_health, None, True, False, None, run_speed=game_property.ENTITY_SPEED * 4)

        BODY_SIZE = (game_property.TILE_SIZE * 2, game_property.TILE_SIZE // 4 * 3)

        # Visuel
        self.add_part(TexturePart(TextureType.FOX_BODY, offset=(0, game_property.TILE_SIZE // 2),  size=BODY_SIZE, name="body", z_index=99))

        self.add_part(TexturePart(TextureType.FOX_LEG, offset=(10, 0), size=(game_property.TILE_SIZE // 3, game_property.TILE_SIZE // 2), name="leg_right", z_index=1))
        self.add_part(TexturePart(TextureType.FOX_LEG, offset=(game_property.TILE_SIZE, 0), size=(game_property.TILE_SIZE // 3, game_property.TILE_SIZE // 2), name="leg_left", z_index=2))
        self.add_part(TexturePart(TextureType.FOX_TAIL,  offset=(-20, (game_property.TILE_SIZE // 2) + BODY_SIZE[1] // 2 - 6), size=(20, 12), name="tail",  z_index=3, flip_x=True))

        self.add_part(TexturePart(TextureType.FOX_EAR,  offset=(game_property.TILE_SIZE * 2 - 8 * 3, game_property.TILE_SIZE // 2 + BODY_SIZE[1]), size=(8, 8), name="ear",  z_index=10))

        # Physique
        self.add_part(CollisionPart((10, 0),  (game_property.TILE_SIZE * 1, game_property.TILE_SIZE // 2 + BODY_SIZE[1]), name="body_hitbox", tag="body"))
        self.recenter_origin()

        self.add_drop(inventory.ItemStack(game_type.ItemProperty.FOX_MEAT, count=2))
    
    def to_json(self, type_="Fox", dict_=None):
        return super().to_json(type_, dict_)


class Zombie(HostileMob):
    def __init__(self, *args, damage=3, attack_range=None, attack_cooldown=1, chase_speed=game_property.ENTITY_SPEED * 3, sight_range=None, **kwargs):
        super().__init__(*args, damage=damage, attack_range=attack_range, attack_cooldown=attack_cooldown, chase_speed=chase_speed, sight_range=sight_range, anim_file=AnimationSet.ZOMBIE, **kwargs)

        width = game_property.TILE_SIZE - 5
        BODY_SIZE = (width, width)
        HEAD_SIZE = (width - 4, width - 4)
        LEG_SIZE = ((width - 2) // 2, width)
        ARM_SIZE = (width // 2, width)

        BODY_OFFSET = (0, LEG_SIZE[1])
        HEAD_OFFSET = (2, BODY_OFFSET[1] + BODY_SIZE[1])
        LEFT_LEG_OFFSET = ((width - LEG_SIZE[0] * 2) // 2, 0)

        ITEM_OFFHAND_SIZE = (width, width)
        ITEM_OFFHAND_OFFSET = (width // 2, LEG_SIZE[1] // 3 * 2)
        LEG_PIVOT = (0, -(LEG_SIZE[1] // 2))

        self.add_part(CollisionPart(size=(width, game_property.TILE_SIZE * 2.5), name="body_hitbox"))

        self.add_part(TexturePart(texture_type=TextureType.ZOMBIE_BODY, size=BODY_SIZE, offset=BODY_OFFSET, name="body_texture", z_index=1))
        self.add_part(TexturePart(texture_type=TextureType.ZOMBIE_HEAD, size=HEAD_SIZE, offset=HEAD_OFFSET, name="head_texture", z_index=2))
        self.add_part(TexturePart(texture_type=TextureType.ZOMBIE_LEG, size=LEG_SIZE, offset=LEFT_LEG_OFFSET, name="left_leg_texture", z_index=3, pivot=LEG_PIVOT))
        self.add_part(TexturePart(texture_type=TextureType.ZOMBIE_LEG, size=LEG_SIZE, offset=(LEFT_LEG_OFFSET[0] + LEG_SIZE[0], 0), name="right_leg_texture", z_index=4, pivot=LEG_PIVOT))

        self.add_part(TexturePart(texture_type=TextureType.ZOMBIE_ARM, size=ARM_SIZE, offset=(2, LEG_SIZE[1] + BODY_SIZE[1] - 2 - ARM_SIZE[1]), name="arm_texture", z_index=6, pivot=(0, -(width // 2) // 2), angle=90))

        self.add_part(TexturePart(texture_type=TextureType.NONE, size=ITEM_OFFHAND_SIZE, offset=ITEM_OFFHAND_OFFSET, name="item_offhand", z_index=5, attach_to="arm_texture", angle=-30))

        self.recenter_origin()



class Arrow(EntityBis):
    TEXTURE_ANGLE = 45

    def __init__(self, pos, v_initial, sender, world=None, name="Arrow entity",
                 damage=10, penetration_depth=1, can_be_picked=True, lifetime=10):
        super().__init__(world, pos, None, name, None, None)
        self.auto_flip = False

        self.damage = damage
        self.penetration_depth = penetration_depth
        self.penetration_counter = 0
        self.sender = sender
        self.can_be_picked = can_be_picked
        self.stucked = False
        self.lifetime = lifetime
        self.age = 0.0              # ne compte que quand la flèche est plantée
        self._flight_time = 0.0
        self._embedded = 0.0

        size = game_property.TILE_SIZE
        hit = (size // 3) * 2
        # origine au centre : `pos` = centre de la flèche, la rotation se fait sur place
        self.add_part(CollisionPart(offset=(-(hit // 2), -(hit // 2)), size=(hit, hit),
                                    name="hitbox", solid=False))
        self.add_part(TexturePart(TextureType.ARROW, size=(size, size),
                                  offset=(-(size // 2), -(size // 2)), name="arrow"))

        self.add_velocity(v_initial.x, v_initial.y)
        self._update_angle()

    def get_damage(self):
        return self.damage

    @property
    def max_embed(self):
        """Profondeur max d'enfoncement (px). Avec penetration_depth=3 : 0,75 tuile."""
        return self.penetration_depth * game_property.TILE_SIZE / 4
    
    # ---------- orientation ----------

    def _update_angle(self):
        if self.velocity.length_squared() == 0:
            return

        theta = math.degrees(math.atan2(self.velocity.y, self.velocity.x))
        left = self.velocity.x < 0

        part = self.get_part("arrow")
        part.set_flip(left, False)                       # miroir si la flèche va vers la gauche

        # direction de la texture après flip : 45° → 135°
        base = (180 - self.TEXTURE_ANGLE) if left else self.TEXTURE_ANGLE
        part.set_angle(theta - base)

    # ---------- durée de vie ----------

    def _tick_lifetime(self, dt):
        self.age += dt
        remaining = self.lifetime - self.age
        if remaining <= 0:
            self.kill()
        elif remaining < 1.0:                      # fondu pendant la dernière seconde
            self.get_part("arrow").alpha = int(255 * remaining)

    # ---------- collisions ----------
    def _hit_entity(self, rect):
        for entity in self.world.get_entities_by_rect(rect):
            if entity is self or entity is self.sender or isinstance(entity, Arrow):
                continue
            if isinstance(entity, LivingEntity) and entity.is_alive:
                return entity
        return None

    # ---------- update ----------

    def update(self, dt, update_live=True):
        if self.stucked or self.attached_to is not None:
            if update_live:
                self._tick_lifetime(dt)
            return

        self._flight_time += dt
        if self._flight_time > 30:
            self.kill()
            return

        self._apply_gravity(dt)
        self.velocity.x *= 0.99
        self._update_angle()

        move = self.velocity * dt
        steps = int(max(abs(move.x), abs(move.y)) / (game_property.TILE_SIZE / 4)) + 1
        step = move / steps
        step_len = step.length()

        for _ in range(steps):
            prev = self.rect.copy()
            self.pos += step
            self._sync_rect()
            sweep = prev.union(self.rect)

            if self.world.is_collide_at(sweep):
                self._embedded += step_len
                if self._embedded >= self.max_embed:
                    self.stuck()
                    return
                continue

            entity = self._hit_entity(sweep)
            if entity:
                self.stuck(entity)
                return

    def stuck(self, entity=None):
        knock = 1 if self.velocity.x >= 0 else -1
        self.velocity.update(0, 0)
        self.stucked = True

        if entity:
            self.attach_self(entity)
            self.world.apply_damage_to_entity(entity, self.damage * 2, knock, self.sender)

class Item(EntityBis):
    def __init__(self, world=None, _item=None, pos=(0, 0), size=(game_property.SIZE_ITEM, game_property.SIZE_ITEM), timer_picked=1):
        super().__init__(world, pos, parts=None, name="Item", lifetime=240)
        self.phase = random.random() * math.pi * 2
        self._item = _item
        self.t = 0

        self._can_be_picked = False
        self.timer_picked = timer_picked

        SIZE = (game_property.SIZE_ITEM, game_property.SIZE_ITEM)
        self.add_part(TexturePart(None, size=SIZE, name="item"))
        self.update_texture()
        self.add_part(CollisionPart(size=SIZE, name="hitbox"))

    def update_texture(self):
        if self.get_item():
            self.get_part("item").set_texture(self.get_item().item_property.get_texture())

    def get_item(self):
        return self._item

    def can_be_picked(self):
        return self._can_be_picked

    def render(self, screen, cam_rect):        
        offset_y = math.sin(self.t + self.phase) * 5
        part = self.get_part("item")
        if part:
            part.offset.y = offset_y

        super().render(screen, cam_rect)

    def update(self, dt):
        self.t = pygame.time.get_ticks() / 500
        
        if self.timer_picked <= 0:
            self._can_be_picked = True
        else:
            self.timer_picked -= dt
        super().update(dt, True)

    def load(self, data, add_map=None):

        if add_map is None:
            add_map = {}

        if not super().load(data, add_map):
            return None
        
        if data.get("item_type", None) is None:
            return None
        
        self._item = game_type.ItemProperty.from_dict(data["item_type"])
        self.update_texture()
        self.t = random.Random().randint(0, 100) / 500
        return self

    def to_json(self, type_="Item", dict_=None):
        if dict_ is None:
            dict_ = {}

        data = {
            "item_type": self.get_item().to_json(),
        }

        data.update(dict_)

        return super().to_json(type_, data)

ENTITY_CLASSES = {
    "Player": Player,
    "Wither": Wither,
    "Fox": Fox,
    "Item": Item,
    "Zombie": Zombie,
}

def get_classe_by_str(text):
    return ENTITY_CLASSES.get(text)

def dict_to_entity(data, world):
    type_ = data.get("type")

    if not type_:
        return None

    cls = get_classe_by_str(type_)
    if not cls:
        print(f"Type inconnu: {type_}")
        return None

    entity = cls(world=world)
    return entity.load(data)

def dict_to_entitys(dict_of_entitys, world):
    entitys = []
    for entity_dict in dict_of_entitys:
        entity = dict_to_entity(entity_dict, world)
        if entity:
            entitys.append(entity)

    return entitys