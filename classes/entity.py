import pygame
from classes import game_property, inventory, game_type
import math
import random
import uuid
from classes.texture_manager import TextureType

def rotate_around_pivot(image, angle, pivot, offset):
    rotated_image = pygame.transform.rotate(image, angle)
    rotated_offset = offset.rotate(-angle)
    rect = rotated_image.get_rect(center=pivot + rotated_offset)
    return rotated_image, rect

def tint_surface(surface, color):
    tinted = surface.copy()
    tinted.fill(color, special_flags=pygame.BLEND_RGB_MULT)
    return tinted

ATTACK_RANGE = 30

class Entity:
    texture_manager = None

    def __init__(self, world, rect, name="Unamed entity", texture=None, dif_pos_render=None, display_name=False, gravity=game_property.GRAVITY, collidable=True):
        self.uuid = uuid.uuid4()
        self.rect = rect
        self.name = name
        self.texture = texture
        self.display_name = display_name
        self.world = world
        self.spawn_time = pygame.time.get_ticks()
        self.font = pygame.font.SysFont("Arial", 14)
        self.gravity = gravity
        self.collidable = collidable
        self.is_alive = True
        if dif_pos_render is None:
            dif_pos_render = [0, 0]
        self.dif_pos_render = dif_pos_render

        self.on_ground = False
        self.auto_jump = False

        self.velocity = pygame.Vector2(0, 0)

        self.speed = game_property.ENTITY_SPEED

        self.display_name_text_surface = self.font.render(self.name, True, (255, 255, 255))

        self.display_name_margin_x = 8
        self.display_name_margin_y = 4

        self.display_name_surface_width = self.display_name_text_surface.get_width() + self.display_name_margin_x * 2
        self.display_name_surface_height = self.display_name_text_surface.get_height() + self.display_name_margin_y * 2

        self.display_name_surface = pygame.Surface((self.display_name_surface_width, self.display_name_surface_height), pygame.SRCALPHA)

        self.temp_rect = None
        self.attached_entities = []
        self.attached_to = None

    def attach_self(self, entity):
        self.attached_to = entity
        entity.add_attached_entity(self)

    def add_attached_entity(self, entity):
        self.attached_entities.append(entity)

    def update_vars(self):
        self.display_name_text_surface = self.font.render(self.name, True, (255, 255, 255))

        self.display_name_margin_x = 8
        self.display_name_margin_y = 4

        self.display_name_surface_width = self.display_name_text_surface.get_width() + self.display_name_margin_x * 2
        self.display_name_surface_height = self.display_name_text_surface.get_height() + self.display_name_margin_y * 2

        self.display_name_surface = pygame.Surface((self.display_name_surface_width, self.display_name_surface_height), pygame.SRCALPHA)
    
    def get_uuid(self):
        return self.uuid
    
    def kill(self):
        self.is_alive = False
        for entity in self.attached_entities:
            entity.kill()

    def render(self, screen, cam_rect, color=(0, 0, 255)):
        draw_x, draw_y = game_property.world_to_screen(
            self.rect.x, self.rect.y, self.rect.height, cam_rect
        )
        draw_x += self.dif_pos_render[0]
        draw_y -= self.dif_pos_render[1]

        if self.texture:
            screen.blit(self.texture, (draw_x, draw_y))
        elif color:
            pygame.draw.rect(screen, color, (draw_x, draw_y, self.rect.width, self.rect.height))

    def render_display_name(self, screen, cam_rect):
        draw_x, draw_y = game_property.world_to_screen(
            self.rect.x, self.rect.y, self.rect.height, cam_rect
        )

        draw_x += self.dif_pos_render[0]
        draw_y -= self.dif_pos_render[1]

        # Surface fond semi-transparent
        chat_surface = pygame.Surface((self.display_name_surface_width, self.display_name_surface_height), pygame.SRCALPHA)
        chat_surface.fill((0, 0, 0, 150))

        # Ajouter texte dans la surface
        chat_surface.blit(self.display_name_text_surface, (self.display_name_margin_x, self.display_name_margin_y))

        # Centrer au-dessus du joueur
        name_x = draw_x + self.rect.width / 2 - self.display_name_surface_width / 2
        name_y = draw_y - self.display_name_surface_height - 5

        screen.blit(chat_surface, (name_x, name_y))

    def render_hit_box(self, screen, cam_rect, color=(255, 255, 255), width=1):
        self.render_hit_box_with_rect(screen, cam_rect, color=(255, 255, 255), width=1, rect=self.rect)

    def render_hit_box_with_rect(self, screen, cam_rect, rect=None, color=(255, 255, 255), width=1):
        draw_x, draw_y = game_property.world_to_screen(rect.x, rect.y, rect.height, cam_rect)
        pygame.draw.rect(screen, color, (draw_x, draw_y, rect.width, rect.height), width)

    def render_highlight(self, screen, cam_rect, color=(255, 255, 255)):
        self.render_hit_box(screen, cam_rect, color, width=2)

    def tp(self, x, y):
        self.rect.x = x
        self.rect.y = y

    def update(self, dt):
        
        try:
            self.apply_gravity(dt)

            self.velocity.x *= 0.9

            new_x = self.rect.x + self.velocity.x * dt
            new_y = self.rect.y + self.velocity.y * dt


            # ----- HORIZONTAL -----
            self.temp_rect = self.rect.copy()
            self.temp_rect.x = new_x

            if not self.world.is_collide_at(self.temp_rect):
                self.move(new_x - self.rect.x, 0)
            else:
                step = 1 if self.velocity.x > 0 else -1

                while not self.world.is_collide_at(self.rect.move(step, 0)):
                    self.move(step, 0)

                self.velocity.x = 0


            # ----- VERTICAL -----
            self.temp_rect = self.rect.copy()
            self.temp_rect.y = new_y

            if not self.world.is_collide_at(self.temp_rect):
                self.move(0, new_y - self.rect.y)
                self.on_ground = False
            else:
                step = 1 if self.velocity.y > 0 else -1

                while not self.world.is_collide_at(self.rect.move(0, step)):
                    self.move(0, step)

                self.velocity.y = 0

                if step < 0:
                    self.on_ground = True
        except Exception as e:
            print("Exception: ", e)

    def move(self, dx, dy):
        self.rect.x += dx
        self.rect.y += dy

        for entity in self.attached_entities:
            entity.move(dx, dy)

    def apply_gravity(self, dt):
        if not self.on_ground:
            # gravity is an acceleration; scale by dt
            self.add_velocity(0, -self.gravity * dt)
        else:
            self.velocity.y = 0
    
    def add_velocity(self, vx, vy):
        self.velocity.x += (vx * self.speed)
        self.velocity.y += (vy * self.speed)

    def set_velocity(self, vx, vy):
        if vx:
            self.velocity.x = vx
        if vy:
            self.velocity.y = vy

    def get_name(self):
        return self.name
    
    def get_rect(self) -> pygame.Rect:
        return self.rect
    
    def get_pos(self) -> tuple:
        return (self.rect.x, self.rect.y)
    
    def load(self, data, add_map=None):

        if add_map is None:
            add_map = {}

        mapping = {
            "uuid": "uuid",
            "x": ("rect", "x"),
            "y": ("rect", "y"),
            "w": ("rect", "width"),
            "h": ("rect", "height"),
            "vx": ("velocity", "x"),
            "vy": ("velocity", "y"),
            "name": "name",
            "gravity": "gravity",
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

        self.update_vars()
        return self

    def to_json(self, type_="Entity", dict_=None):

        if dict_ is None:
            dict_ = {}

        data = {
            "type": type_,
            "uuid": str(self.uuid),
            "x": self.rect.x,
            "y": self.rect.y,
            "w": self.rect.width,
            "h": self.rect.height,
            "vx": self.velocity.x,
            "vy": self.velocity.y,
            "gravity": self.gravity,
            "speed": self.speed,
            "display_name": self.display_name,
            "name": self.name,
        }

        data.update(dict_)   # ajoute les champs supplémentaires

        return data
    
class Annimation:
    ATTACK = "attack"
    NONE = "none"

class Living_entity(Entity):
    def __init__(self, world, rect, name="Unamed entity", health=20, max_health=20, drops=None, collidable=True):
        super().__init__(world, rect, name, None, None, False, collidable=collidable)
        self.max_health = max_health
        self.health = health
        self.drops = drops

        self.orientation = "left"
        self.last_vx = 0

        self.reset_annimation()
        self.reset_take_damage()
    
    def update(self, dt):
        if self.annim_time > 0:
            self.annim_time -= dt
        else:
            self.reset_annimation()

        if self.health <= 0:
            self.kill()
            return
        
        if self.annim_damage_time > 0:
            self.annim_damage_time -= dt
        else:
            self.reset_take_damage()
        
        return super().update(dt)

    def set_orientation(self, orientation):
        if self.annim_time > 0 and self.annim_orientation:
            return True
        else:
            self.annim_orientation = None
        
        if self.orientation != orientation:
            self.orientation = orientation
            self.update_texture()
            return True
        return False
    
    def get_anim_direction(self) -> int:
        if self.annim_orientation:
            if self.annim_orientation == "right":
                return 1
            if self.annim_orientation == "left":
                return -1
        return 0

    def get_orientation(self):
        if self.annim_orientation:
            return self.annim_orientation
        return self.orientation

    def start_annimation(self, time: float, dirrection: str, annim_type: Annimation):
        self.annim_time = time
        self.annim_orientation = dirrection
        self.annim_type = annim_type

        self.update_texture()

    def render(self, screen, cam_rect, color=(0, 0, 255)):
        super().render(screen, cam_rect, color)
        if self.annim_time > 0:
            self.render_annimation()

        if self.health < self.max_health:
            self.render_health_bar(screen, cam_rect)

    def render_health_bar(self, screen, cam_rect):
        draw_x, draw_y = game_property.world_to_screen(
            self.rect.x, self.rect.y, self.rect.height, cam_rect
        )

        bar_width = self.rect.width * 1.5
        bar_height = 10

        health_ratio = max(0, self.health / self.max_health)

        bar_x = draw_x - (bar_width - self.rect.width) // 2
        bar_y = draw_y - self.display_name_surface_height + 10

        # fond
        pygame.draw.rect(screen, (60, 0, 0), (bar_x, bar_y, bar_width, bar_height))

        # vie
        pygame.draw.rect(
            screen,
            (0, 220, 0),
            (bar_x, bar_y, bar_width * health_ratio, bar_height)
        )

        # contour (propre visuellement)
        pygame.draw.rect(
            screen,
            (255, 255, 255),
            (bar_x, bar_y, bar_width, bar_height),
            1
        )
    
    def render_annimation(self):
        pass

    def reset_annimation(self):
        self.annim_time = 0
        self.annim_orientation = None
        self.annim_type = None
        self.update_orientation()

        self.update_texture()

    def add_velocity(self, vx, vy):
        super().add_velocity(vx, vy)
        self.update_orientation()
    
    def set_velocity(self, vx, vy):
        super().set_velocity(vx, vy)
        self.update_orientation()

    def update_orientation(self):
        if self.velocity.x > 0:
            self.set_orientation("right")
        elif self.velocity.x < 0:
            self.set_orientation("left")

    def get_int_direction(self):
        if self.get_orientation() == "right":
            return 1
        else:
            return -1
    
    def render_display_name(self, screen, cam_rect):
        return super().render_display_name(screen, cam_rect)

    def apply_damage(self, damage, dx):
        # Appliquer les dégâts
        if not self.is_taking_damage:
            self.health -= damage * game_property.DAMAGE_COEF

            # Knockback horizontal
            knockback_force = 10
            vx = dx * knockback_force
            vy = 10 # petit saut vers le haut

            self.add_velocity(vx, vy)
            self.take_damage()

            print("Taking damage: ", damage * game_property.DAMAGE_COEF)

    def take_damage(self):
        self.is_taking_damage = True
        self.annim_damage_time = 0.2
    
    def reset_take_damage(self):
        self.is_taking_damage = False
        self.annim_damage_time = 0

    def update_texture(self):
        pass

    def load(self, data, add_map=None):

        if add_map is None:
            add_map = {}

        map_ = {
            "health": "health",
            "max_health": "max_health",
            "orientation": "orientation",
        }

        map_.update(add_map)

        if not super().load(data, map_):
            return None
        self.update_orientation()

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

    def to_json(self, type_="Living_entity", dict_=None):
        if dict_ is None:
            dict_ = {}

        drops = []
        if self.drops:
            for drop_item in self.drops:
                drops.append(drop_item.to_json())

        data = {
            "health": self.health,
            "max_health": self.max_health,
            "orientation": self.orientation,
            "drops": drops
        }

        data.update(dict_)

        return super().to_json(type_, data)

class Arrow_entity(Living_entity):
    def __init__(self, world, pos, v_initial, sender, name="Arrow entity", texture=None, damage=10, penetration_depth=3):
        self.damage = damage
        self.penetration_depth = penetration_depth
        self.penetration_counter = 0

        rect = pygame.Rect(pos[0], pos[1], game_property.TILE_SIZE, game_property.TILE_SIZE)

        super().__init__(world, rect, name)
        self.sender = sender

        if texture is None:
            texture = self.texture_manager.get_texture(TextureType.ARROW)
        self.texture = texture
        self.stucked = False

        self.add_velocity(v_initial.x, v_initial.y)

    def get_damage(self):
        return self.damage
    
    def render(self, screen, cam_rect):
        texture = self.texture

        # position écran
        draw_x, draw_y = game_property.world_to_screen(
            self.rect.x, self.rect.y, self.rect.height, cam_rect
        )

        # angle basé sur la vitesse
        if self.velocity.length() > 0:
            angle = -self.velocity.angle_to(pygame.Vector2(1, 0)) - 45
        else:
            angle = 0

        # pivot = centre
        pivot = pygame.Vector2(
            draw_x + self.rect.width / 2,
            draw_y + self.rect.height / 2
        )

        offset = pygame.Vector2(0, 0)

        rotated_image, rotated_rect = rotate_around_pivot(
            texture,
            angle,
            pivot,
            offset
        )

        screen.blit(rotated_image, rotated_rect.topleft)

    def move(self, x, y):
        return super().move(x, y)

    def update(self, dt):
        if self.stucked:
            return

        # --- PHYSIQUE ---
        self.apply_gravity(dt)
        self.velocity.x *= 0.99

        dx = self.velocity.x * dt
        dy = self.velocity.y * dt

        # nombre de steps (IMPORTANT)
        steps = int(max(abs(dx), abs(dy)) / (game_property.TILE_SIZE / 4)) + 1

        step_x = dx / steps
        step_y = dy / steps

        for _ in range(steps):

            new_rect = self.rect.move(step_x, step_y)

            # ----- COLLISION BLOCS -----
            if self.world.is_collide_at(new_rect):

                self.penetration_counter += 1

                if self.penetration_counter >= self.penetration_depth:
                    self.stuck()
                    return

                # on continue mais ralenti / ou on "pousse dans le mur"
                self.rect = new_rect
                continue

            # ----- COLLISION ENTITÉS -----
            for entity in self.world.get_entities():
                if entity == self or entity == self.sender or isinstance(entity, Arrow_entity):
                    continue

                if isinstance(entity, Living_entity):
                    if new_rect.colliderect(entity.rect):
                        self.penetration_counter += 1

                        if self.penetration_counter >= self.penetration_depth:
                            self.stuck(entity)
                            return

                        # on continue mais ralenti / ou on "pousse dans le mur"
                        self.rect = new_rect
                        continue

            # appliquer le step
            self.rect = new_rect
    
    def stuck(self, entity=None):
        if entity:
            self.attach_self(entity)
            entity.apply_damage(self.damage * 2, 0)
        
        self.stucked = True
            

class Player(Living_entity):
    def __init__(self, world, name="", rect=None, max_health=40):
        if not rect:
            rect = pygame.Rect(0, game_property.CHUNK_MAX_HEIGHT * game_property.TILE_SIZE, game_property.TILE_SIZE - 5, game_property.TILE_SIZE * 2.5)
        super().__init__(world, rect, name, max_health=max_health, health=max_health)
        self.inventory = inventory.Entity_Inventory(self)
        self.speed = game_property.PLAYER_SPEED
        
        self.update_texture()

    def render(self, screen, cam_rect):
        orientation = self.get_orientation()

        # 🎯 Clignotement damage
        use_red = False
        if self.is_taking_damage:
            if int(self.annim_damage_time * 20) % 2 == 0:
                use_red = True

        # 🎯 Choix textures
        if use_red:
            head = self.head_texture_red
            body = self.body_texture_red
            leg = self.leg_texture_red
            arm = self.arm_texture_red
        else:
            head = self.head_texture
            body = self.body_texture
            leg = self.leg_texture
            arm = self.arm_texture

        # =========================
        # HEAD (avec world_to_screen)
        draw_x, draw_y = game_property.world_to_screen(
            self.rect.x, self.rect.y, self.rect.height, cam_rect
        )
        draw_x += 2
        draw_y += 4
        screen.blit(head, (draw_x, draw_y))

        # =========================
        # BASE POSITION (évite recalculs)
        base_x = self.rect.x - cam_rect.x
        base_y = cam_rect.height - (self.rect.y - cam_rect.y) - self.rect.height

        # =========================
        # BODY
        screen.blit(body, (base_x, base_y + self.rect.width))

        # =========================
        # LEG
        screen.blit(leg, (base_x + 2, base_y + self.rect.width * 2))

        # =========================
        # ARM
        if orientation == "left":
            arm_x = base_x + self.rect.width // 2
        else:
            arm_x = base_x

        arm_y = base_y + self.rect.width
        screen.blit(arm, (arm_x, arm_y))

        # =========================
        # ITEM / ARME
        selected_item = self.inventory.ui.get_selected_item()

        if selected_item:
            item_property = selected_item.item_property

            if isinstance(item_property, game_type.Tool):

                if isinstance(item_property, game_type.Bow_tool):
                    texture = item_property.get_texture()

                    if texture:
                        weapon_size = int(self.rect.width * 1.8)
                        texture = pygame.transform.scale(texture, (weapon_size, weapon_size))

                        # 🎯 position main
                        if orientation == "right":
                            hand_x = base_x + int(self.rect.width * 0.75)
                        else:
                            hand_x = base_x + int(self.rect.width * 0.25)

                        hand_y = base_y + int(self.rect.width * 1.2)

                        # 🎯 flip
                        if orientation == "left":
                            texture = pygame.transform.flip(texture, True, False)

                        # 🎯 pivot
                        if orientation == "right":
                            offset = pygame.Vector2(weapon_size * 0.2, 0)
                        else:
                            offset = pygame.Vector2(-weapon_size * 0.2, 0)

                        angle = -30 * self.get_int_direction()

                        pivot = pygame.Vector2(hand_x, hand_y)

                        rotated_image, rotated_rect = rotate_around_pivot(
                            texture,
                            angle,
                            pivot,
                            offset
                        )

                        screen.blit(rotated_image, rotated_rect.topleft)
                else:

                    texture = item_property.get_texture()

                    if texture:
                        weapon_size = int(self.rect.width * 1.8)
                        texture = pygame.transform.scale(texture, (weapon_size, weapon_size))

                        # 🎯 position main
                        if orientation == "right":
                            hand_x = base_x + int(self.rect.width * 0.75)
                        else:
                            hand_x = base_x + int(self.rect.width * 0.25)

                        hand_y = base_y + int(self.rect.width * 1.2)

                        # 🎯 flip
                        if orientation == "left":
                            texture = pygame.transform.flip(texture, True, False)

                        # 🎯 pivot
                        if orientation == "right":
                            offset = pygame.Vector2(weapon_size * 0.2, 0)
                        else:
                            offset = pygame.Vector2(-weapon_size * 0.2, 0)

                        # 🎯 animation attaque
                        if self.is_attacking():
                            progress = self.annim_time
                            angle = math.sin(progress * 10) * 80 * self.get_anim_direction()
                        else:
                            angle = 0

                        pivot = pygame.Vector2(hand_x, hand_y)

                        rotated_image, rotated_rect = rotate_around_pivot(
                            texture,
                            angle,
                            pivot,
                            offset
                        )

                        screen.blit(rotated_image, rotated_rect.topleft)

            else:
                # 🎯 item normal
                if orientation == "left":
                    item_x = base_x + self.rect.width // 2 - self.rect.width // 3 * 2
                else:
                    item_x = base_x + self.rect.width // 3 * 2

                item_y = base_y + self.rect.width + self.rect.width // 2

                selected_item.render(
                    screen,
                    (item_x, item_y),
                    draw_number=False,
                    texture_size=(self.rect.width // 2, self.rect.width // 2)
                )

        # =========================
        # NOM
        super().render_display_name(screen, cam_rect)
        super().render(screen, cam_rect, None)

    def render_hit_box(self, screen, cam_rect, color=(255, 255, 255), width=1):
        if self.is_attacking():
            selected_item = self.inventory.ui.get_selected_item()
            if selected_item:
                if isinstance(selected_item.item_property, game_type.Attack_tool):
                    self.render_hit_box_with_rect(screen, cam_rect, rect=self.get_rect_attack(), color=(255, 0, 0))
        return super().render_hit_box(screen, cam_rect, color, width)

    def get_rect(self):
        return super().get_rect()
    
    def get_rect_attack(self):
        self.temp_rect = self.rect.copy()
        self.temp_rect.x += self.get_anim_direction() * ATTACK_RANGE
        return self.temp_rect

    def update_texture(self):
        self.head_texture = self.texture_manager.get_texture(TextureType.PLAYER_HEAD)
        self.head_texture = pygame.transform.scale(self.head_texture, (self.rect.width- 4, self.rect.width - 4))

        self.body_texture = self.texture_manager.get_texture(TextureType.PLAYER_BODY)
        self.body_texture = pygame.transform.scale(self.body_texture, (self.rect.width, self.rect.width))

        self.leg_texture = self.texture_manager.get_texture(TextureType.PLAYER_LEG)
        self.leg_texture = pygame.transform.scale(self.leg_texture, (self.rect.width - 4, self.rect.width))
        
        self.arm_texture = self.texture_manager.get_texture(TextureType.PLAYER_ARM)
        self.arm_texture = pygame.transform.scale(self.arm_texture, (self.rect.width // 2, self.rect.width))

        if self.get_orientation() == "right":
            self.head_texture = pygame.transform.flip(self.head_texture, True, False)
            self.body_texture = pygame.transform.flip(self.body_texture, True, False)
            self.leg_texture = pygame.transform.flip(self.leg_texture, True, False)
            self.arm_texture = pygame.transform.flip(self.arm_texture, True, False)

        self.head_texture_red = tint_surface(self.head_texture, (200, 100, 100))
        self.body_texture_red = tint_surface(self.body_texture, (200, 100, 100))
        self.leg_texture_red = tint_surface(self.leg_texture, (200, 100, 100))
        self.arm_texture_red = tint_surface(self.arm_texture, (200, 100, 100))
    
    

    def update(self, dt):

        if self.is_attacking():
            selected_item = self.inventory.ui.get_selected_item()
            if selected_item:
                if isinstance(selected_item.item_property, game_type.Attack_tool):

                    entities = self.world.get_entities_by_rect(self.get_rect_attack())
                    for entity in entities:
                        if entity is not self and isinstance(entity, Living_entity):
                            entity.apply_damage(selected_item.item_property.get_attack_damage(), self.get_anim_direction())

        for entity in self.world.get_entities():
            if isinstance(entity, Arrow_entity):
                if not entity.stucked:
                    continue

                if entity.attached_to is not None:
                    continue

                if self.rect.colliderect(entity.rect):

                    # ajouter une flèche à l'inventaire
                    self.inventory.add_item(
                        inventory.ItemStack(game_type.ItemProperty.ARROW, 1)
                    )

                    entity.kill()
                    
        return super().update(dt)

    def set_orientation(self, orientation):
        if super().set_orientation(orientation):
            self.update_texture()

    def drop_item(self, itemIndex=None):
        if not itemIndex:
            item = self.inventory.ui.get_selected_item()
            itemIndex = self.inventory.ui.selected_index
        else:
            item = self.inventory.get_item(itemIndex)

        if item:
            mid_x = self.rect.x + self.rect.width // 2
            quart_y = self.rect.y + self.rect.height // 4
            
            entity = Item(self.world, item.item_property, (mid_x + self.get_int_direction() * self.rect.width, quart_y))

            entity.add_velocity(self.get_int_direction() * 5, 5)
            self.world.create_entity(entity)

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

    def stop_use_selected_item(self, cam_rect):
        self.use_selected_item(cam_rect)
    
    def use_item(self, direction):
        selected_item = self.inventory.ui.get_selected_item()

        if isinstance(selected_item.item_property, game_type.Bow_tool):
            bow_use = selected_item.item_property.used
            if bow_use:
                if not self.inventory.has_item(game_type.ItemProperty.ARROW):
                    return

                self.inventory.delete_item_property(game_type.ItemProperty.ARROW, 1)

                selected_item.item_property.used = False
                if direction.x > 0:
                    direction_str = "right"
                else:
                    direction_str = "left"

                self.start_annimation(1/4, direction_str, Annimation.NONE)

                speed = 30
                v = direction * speed

                origin = pygame.Vector2(self.rect.centerx, self.rect.centery)

                selected_item.item_property.use()

                arrow = Arrow_entity(
                    self.world,
                    (origin.x, origin.y),
                    v,
                    self
                )
                self.world.create_entity(arrow)
            else:
                if self.inventory.has_item(game_type.ItemProperty.ARROW):
                    selected_item.item_property.used = True

                    

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
        if self.annim_type:
            if self.annim_type == Annimation.ATTACK:
                return True
        return False

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

    def attack(self, v):
        dx, dy = v

        orientation = None
        if dx < 0:
            orientation = "left"
        elif dx > 0:
            orientation = "right"

        self.start_annimation(1/4 * 3, orientation, Annimation.ATTACK)

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
        self.update_texture()
        return self

class Item(Entity):
    def __init__(self, world, item_type=None, pos=(0, 0), size=(game_property.SIZE_ITEM, game_property.SIZE_ITEM)):
        rect = pygame.Rect(pos[0], pos[1], size[0], size[1])
        super().__init__(world, rect, "Item")
        self.phase = random.random() * math.pi * 2
        self.item_type = item_type
        self.t = 0

        self.update_texture()

    def update_texture(self):
        if self.item_type is None:
            return

        texture = self.item_type.get_texture()

        if texture is None:
            print(f"Texture introuvable pour {self.item_type.texture}")
            return

        self.texture = pygame.transform.scale(
            texture,
            (game_property.SIZE_ITEM, game_property.SIZE_ITEM)
        )

    def render(self, screen, cam_rect, color=(0, 0, 255)):
        
        offset_y = math.sin(self.t + self.phase) * 5

        self.dif_pos_render = (0, offset_y)
        
        super().render(screen, cam_rect, color)
        #super().render_hit_box(screen, cam_rect)

    def update(self, dt):
        super().update(dt)
        self.t = pygame.time.get_ticks() / 500

    def load(self, data, add_map=None):

        if add_map is None:
            add_map = {}

        if not super().load(data, add_map):
            return None
        
        if data.get("item_type", None) is None:
            return None
        
        self.item_type = game_type.ItemProperty.from_dict(data["item_type"])

        self.t = random.Random().randint(0, 100) / 500
        self.update_texture()
        return self

    def to_json(self, type_="Item", dict_=None):
        if dict_ is None:
            dict_ = {}

        data = {
            "item_type": self.item_type.to_json(),
        }

        data.update(dict_)

        return super().to_json(type_, data)

class Mob(Living_entity):
    def __init__(self, world, rect, name="Unamed entity", health=20, max_health=20, IA=True):
        super().__init__(world, rect, name, health, max_health)
        self.auto_jump = True
        self.IA = IA

        self.move_timer = 0
        self.move_direction = 0
        self.move_speed = 3

    def update(self, dt):
        # Si le timer est écoulé, choisir une nouvelle direction
        if self.move_timer <= 0:
            self.move_direction = random.choice([-1, 1, 0])  # gauche ou droite
            self.move_timer = random.randint(0, 6)  # se déplacer pendant 3 secondes
            self.move_speed = random.randint(80, 120)

        target = self.move_direction * self.move_speed

        if target != 0:
            if target > 0:
                vx = max(self.velocity.x, target)
            else:
                vx = min(self.velocity.x, target)
        else:
            vx = self.velocity.x

        self.set_velocity(vx, None)

        # Décrémenter le timer
        self.move_timer -= dt

        if self.auto_jump:
            self.front_rect = self.rect.copy()
            self.front_rect.x += self.move_direction * 5  # quelques pixels devant
            self.front_rect.y += 1  # au niveau du sol

            if self.world.is_collide_at(self.front_rect) and self.on_ground:
                # appliquer un saut
                self.set_velocity(None, game_property.JUMP_VELOCITY // 3 * 2 * self.speed)
                self.on_ground = False

        # Appel du super pour appliquer le mouvement
        super().update(dt)

    def load(self, data, add_map=None):
        if add_map is None:
            add_map = {}

        map_ = {
            "IA": "IA",
            "auto_jump": "auto_jump",
        }
        map_.update(add_map)
        
        return super().load(data, map_)
    
    def to_json(self, type_="Mob", dict_=None):
        if dict_ is None:
            dict_ = {}

        data = {
            "IA": self.IA,
            "auto_jump": self.auto_jump,
        }

        data.update(dict_)
        
        return super().to_json(type_, data)

class Zobmie(Mob):
    def __init__(self, world, rect=None, name="Unamed entity", health=20, max_health=20, moving=True):
        rect = pygame.Rect(0, game_property.CHUNK_MAX_HEIGHT * game_property.TILE_SIZE, game_property.TILE_SIZE - 5, game_property.TILE_SIZE * 2.5)
        super().__init__(world, rect, name, health, max_health, moving)
        self.update_texture()

    def render(self, screen, cam_rect):
        # 🎯 Gestion du clignotement (effet Terraria)
        use_red = False
        if self.is_taking_damage:
            # clignote rapidement
            if int(self.annim_damage_time * 20) % 2 == 0:
                use_red = True

        # 🎯 Choix des textures
        if use_red:
            head = self.head_texture_red
            body = self.body_texture_red
            leg = self.leg_texture_red
            arm = self.arm_texture_red
        else:
            head = self.head_texture
            body = self.body_texture
            leg = self.leg_texture
            arm = self.arm_texture

        # =========================
        # HEAD
        draw_x, draw_y = game_property.world_to_screen(
            self.rect.x, self.rect.y, self.rect.height, cam_rect
        )
        draw_x += 2
        draw_y += 4
        screen.blit(head, (draw_x, draw_y))

        # =========================
        # BODY
        draw_x = self.rect.x - cam_rect.x
        draw_y = cam_rect.height - (self.rect.y - cam_rect.y) - self.rect.height + self.rect.width
        screen.blit(body, (draw_x, draw_y))

        # =========================
        # LEG
        draw_x = self.rect.x - cam_rect.x + 2
        draw_y = cam_rect.height - (self.rect.y - cam_rect.y) - self.rect.height + self.rect.width * 2
        screen.blit(leg, (draw_x, draw_y))

        # =========================
        # ARM (différent selon orientation)
        if self.orientation == "left":
            draw_x = self.rect.x - cam_rect.x + self.rect.width // 2
        else:
            draw_x = self.rect.x - cam_rect.x

        draw_y = cam_rect.height - (self.rect.y - cam_rect.y) - self.rect.height + self.rect.width
        screen.blit(arm, (draw_x, draw_y))

        super().render(screen, cam_rect, None)

    def set_orientation(self, orientation):
        if super().set_orientation(orientation):
            self.update_texture()

    def update_texture(self):
        self.head_texture = self.texture_manager.get_texture(TextureType.ZOMBIE_HEAD)
        self.head_texture = pygame.transform.scale(self.head_texture, (self.rect.width- 4, self.rect.width - 4))

        self.body_texture = self.texture_manager.get_texture(TextureType.ZOMBIE_BODY)
        self.body_texture = pygame.transform.scale(self.body_texture, (self.rect.width, self.rect.width))

        self.leg_texture = self.texture_manager.get_texture(TextureType.ZOMBIE_LEG)
        self.leg_texture = pygame.transform.scale(self.leg_texture, (self.rect.width - 4, self.rect.width))
        
        self.arm_texture = self.texture_manager.get_texture(TextureType.ZOMBIE_ARM)
        self.arm_texture = pygame.transform.scale(self.arm_texture, (self.rect.width // 2, self.rect.width))

        if self.orientation == "right":
            self.head_texture = pygame.transform.flip(self.head_texture, True, False)
            self.body_texture = pygame.transform.flip(self.body_texture, True, False)
            self.leg_texture = pygame.transform.flip(self.leg_texture, True, False)
            self.arm_texture = pygame.transform.flip(self.arm_texture, True, False)
        
        self.head_texture_red = tint_surface(self.head_texture, (200, 100, 100))
        self.body_texture_red = tint_surface(self.body_texture, (200, 100, 100))
        self.leg_texture_red = tint_surface(self.leg_texture, (200, 100, 100))
        self.arm_texture_red = tint_surface(self.arm_texture, (200, 100, 100))

    def to_json(self, type_="Zombie", dict_=None):
        if dict_ is None:
            dict_ = {}

        data = {
            
        }

        data.update(dict_)
        
        return super().to_json(type_, data)

ENTITY_CLASSES = {
    "Zombie": Zobmie,
    "Player": Player,
    "Item": Item,
}

def dict_to_entity(data, world):
    type_ = data.get("type")

    if not type_:
        return None

    cls = ENTITY_CLASSES.get(type_)
    if not cls:
        print(f"Type inconnu: {type_}")
        return None

    entity = cls(world)
    return entity.load(data)

def dict_to_entitys(dict_of_entitys, world):
    entitys = []
    for entity_dict in dict_of_entitys:
        entity = dict_to_entity(entity_dict, world)
        if entity:
            entitys.append(entity)

    return entitys