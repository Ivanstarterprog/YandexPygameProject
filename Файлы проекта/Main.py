import pygame
import sys
import os
import math
import random

Fps = 60

size = WIDTH, HEIGHT = 800, 800
screen = pygame.display.set_mode(size)
pygame.display.set_caption("Hotline Python")
pygame.display.set_icon(pygame.image.load("Data/icon.ico"))
pygame.init()
pygame.mixer.init()

# Создаём заранее игровые звуки, которые будем в будущем вызывать
gunshot = pygame.mixer.Sound("Data/gunshot.mp3")
emptygun = pygame.mixer.Sound("Data/emptygun.mp3")
reload = pygame.mixer.Sound("Data/reload.mp3")
slow_mo_sound = pygame.mixer.Sound("Data/slow_mo_sound.mp3")
slow_mo_shot = pygame.mixer.Sound("Data/slowmo_gunshot.mp3")
reloaded_gun = pygame.mixer.Sound("Data/reloaded_gun.mp3")
get_shot = pygame.mixer.Sound("Data/mangetshot.mp3")
bulletfall = pygame.mixer.Sound("Data/bulletfallout.mp3")
all_sounds = [gunshot, emptygun, reload, slow_mo_sound, slow_mo_shot, reloaded_gun, get_shot, bulletfall]
battle_music = ["Data/action_song1.mp3", "Data/action_song2.mp3", "Data/action_song3.mp3"]


# создаём список музыки чтобы потом выбиралась случайная


def terminate():
    pygame.quit()
    sys.exit()


all_sprites = pygame.sprite.Group()
Cursors = pygame.sprite.Group()
Enemys = pygame.sprite.Group()
Players = pygame.sprite.Group()
Moveble_items = pygame.sprite.Group()
Vertical_left = pygame.sprite.Group()
Vertical_right = pygame.sprite.Group()
Horizontal_Down = pygame.sprite.Group()
Horizontal_Up = pygame.sprite.Group()
Blood = pygame.sprite.Group()
Bullets = pygame.sprite.Group()


def load_image(name, color_key=None):
    fullname = os.path.join('data', name)
    if not os.path.isfile(fullname):
        print(f"Файл с изображением '{fullname}' не найден")
        sys.exit()
    image = pygame.image.load(fullname)
    if color_key is not None:
        image = image.convert()
        if color_key == -1:
            color_key = image.get_at((0, 0))
        image.set_colorkey(color_key)
    else:
        image = image.convert_alpha()
    return image


class Particle(pygame.sprite.Sprite):  # Частичка крови
    def __init__(self, pos, dx, dy):
        super().__init__(Blood)
        self.image = pygame.Surface([7, 7])
        self.rect = pygame.Rect((pos[0], pos[1], 7, 7))
        self.rect.centerx = pos[0]
        self.rect.centery = pos[1]
        self.dx = dx
        self.dy = dy
        # Выбираем точку назначения
        self.wherex = random.randint(pos[0] - 1, pos[0] + 1)
        self.wherey = random.randint(pos[1] - 1, pos[1] + 1)
        self.second = 0  # пуля живёт 170 кадров, потому создаём счётчик чтобы знать когда её уничтожить

    def update(self):
        self.second += 1  # Увеличиваем счётчик
        pygame.draw.rect(screen, pygame.Color("red"), (self.rect.x, self.rect.y, 7, 7), 0)
        # пуля летит в выбранную точку
        if self.rect.centerx > self.wherex:
            self.rect.centerx -= self.dx
        if self.rect.centerx < self.wherex:
            self.rect.centerx += self.dx
        if self.rect.centery > self.wherey:
            self.rect.centery -= self.dy
        if self.rect.centery < self.wherey:
            self.rect.centery += self.dy
        # Уничтожаем кровь если она просуществовала 170 кадров или коснулась стены
        if self.second == 170:
            self.kill()
        if self.rect.centerx < 95 or self.rect.centerx > 620 or self.rect.centery < 100 or self.rect.centery > 700:
            self.kill()


class Interface(pygame.sprite.Sprite):  # Интерфейс
    def __init__(self, start_x, start_y, width, height, First_line):
        self.width = width
        self.height = height
        self.x = start_x
        self.y = start_y
        self.fl = First_line
        self.image = pygame.Surface([start_x, start_y])
        self.rect = pygame.Rect(start_x, start_y, width, height)

    def render(self, screen, render_thing):  # Выводим нужную информацию
        Text = self.fl
        font = pygame.font.Font("Data/justicelaser.ttf", 30)
        text = font.render(Text, 1, (255, 255, 255))
        screen.blit(text, (self.x, self.y))
        text = font.render(render_thing, 1, (255, 255, 255))
        x = self.x
        y = self.y + 40
        screen.blit(text, (x, y))


class Cursor(pygame.sprite.Sprite):  # Курсор
    image = load_image("crosshair.png")
    cursor = pygame.transform.scale(image, (15, 15))
    all_sprites.add()

    def __init__(self, *group):
        super().__init__(*group)
        self.image = Cursor.cursor
        self.rect = self.image.get_rect()

    def update(self, *args):
        # получаем местоположение курсора и берем её за середину изображения
        self.rect.x = args[0][0] - self.rect.width // 2
        self.rect.y = args[0][1] - self.rect.height // 2


class MoveObject(pygame.sprite.Sprite):  # Основа Класса Объектов
    def __init__(self, sheet, x=0, y=0):
        super().__init__(all_sprites)
        self.image = sheet
        self.original_image = self.image
        Moveble_items.add(self)
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.centery = y

    def rotate(self, x, y):  # Поворот объекта к нужным кардинатам
        rel_x, rel_y = x - self.rect.x, y - self.rect.y
        angle = (180 / math.pi) * -math.atan2(rel_y, rel_x)
        self.image = pygame.transform.rotate(self.original_image, int(angle))
        self.rect = self.image.get_rect(center=(self.rect.centerx, self.rect.centery))


class Player(MoveObject):  # Класс игрока
    def __init__(self):
        super().__init__(load_image("player.png"), 355, 400)
        self.speed = 2
        self.durability = 100  # Стамина игрока
        self.bullets = 10  # Количество патронов игрока
        self.is_reloading = False  # проверка перезарядки

    def update(self):
        # Проверяем не косается ли спрайт стену
        # Если нет, то в случае нажатого шифта и стамины не равной нулю, мы ускоряемся
        # Иначе идём с обычной скоростью
        if not pygame.sprite.spritecollideany(self, Vertical_left):
            if pygame.key.get_pressed()[pygame.K_a] and pygame.key.get_pressed()[
                pygame.K_LSHIFT] and self.durability != 0:
                self.rect.centerx -= 3
                if self.durability > 0:
                    self.durability -= 0.5
            elif pygame.key.get_pressed()[pygame.K_a]:
                self.rect.centerx -= 2
        if not pygame.sprite.spritecollideany(self, Vertical_right):
            if pygame.key.get_pressed()[pygame.K_d] \
                    and pygame.key.get_pressed()[pygame.K_LSHIFT] and self.durability != 0:
                self.rect.centerx += 3
                if self.durability > 0:
                    self.durability -= 0.5
            if pygame.key.get_pressed()[pygame.K_d]:
                self.rect.centerx += 2
        if not pygame.sprite.spritecollideany(self, Horizontal_Up):
            if pygame.key.get_pressed()[pygame.K_w] \
                    and pygame.key.get_pressed()[pygame.K_LSHIFT] and self.durability != 0:
                self.rect.centery -= 3
                if self.durability > 0:
                    self.durability -= 0.5
            if pygame.key.get_pressed()[pygame.K_w]:
                self.rect.centery -= 2
        if not pygame.sprite.spritecollideany(self, Horizontal_Down):
            if pygame.key.get_pressed()[pygame.K_s] \
                    and pygame.key.get_pressed()[pygame.K_LSHIFT] and self.durability != 0:
                self.rect.centery += 3
                if self.durability > 0:
                    self.durability -= 0.5
            if pygame.key.get_pressed()[pygame.K_s]:
                self.rect.centery += 2
        # если нажата кнопка R, игрок не перезаряжается а так же количество пуль ниже 10 то мы начинаем перезаряжать
        if pygame.key.get_pressed()[pygame.K_r]:
            if not self.is_reloading and self.bullets < 10:
                self.is_reloading = True
                reload.play()

    def reload(self):
        self.bullets = 10

    def shoot(self, *args):
        # Если количество пуль больше 0 то мы стреляем
        if self.bullets > 0 and not self.is_reloading:
            Bullet(self.rect.centerx, self.rect.centery, args[0][0], args[0][1], self, 20, args[1])
            self.bullets -= 1
        # Иначе воспроизводится звук холостого выстрела
        elif self.bullets == 0 and not self.is_reloading:
            emptygun.play()
        # Это всё если в данный момент не идёт перезарядка


score = 0  # Создаём для адекватной работы системы очков


class Enemy(MoveObject):  # Противник
    def __init__(self):
        super().__init__(load_image("enemy.png"))
        start = random.randint(1, 6)  # Выбираем случайную точку старта
        self.starting = True  # Проверяем стартует ли противник
        # Задаём Данные для старта
        if start == 1:
            self.rect.centerx = -20
            self.rect.centery = 355
            self.distancex = 130
            self.distancey = 355
        elif start == 2:
            self.rect.centerx = -20
            self.rect.centery = 663
            self.distancex = 130
            self.distancey = 663
        elif start == 3:
            self.rect.centerx = 820
            self.rect.centery = 129
            self.distancex = 590
            self.distancey = 129
            self.rotate(624, 129)
        elif start == 4:
            self.rect.centerx = 820
            self.rect.centery = 450
            self.distancex = 580
            self.distancey = 450
            self.rotate(624, 450)
        elif start == 5:
            self.rect.centerx = 134
            self.rect.centery = -20
            self.distancex = 134
            self.distancey = 130
            self.rotate(134, 105)
        else:
            self.rect.centerx = 580
            self.rect.centery = 820
            self.distancex = 580
            self.distancey = 675
            self.rotate(580, 675)

    def move(self):  # Выбираем случайную точку на карте, куда может пойти противник
        self.distancex = random.randint(110, 590)
        self.distancey = random.randint(130, 680)

    def shoot(self, x, y, object, slow_mo):  # Если противник живой, то он стреляет в сторону игрока
        if object.alive():
            Bullet(self.rect.centerx, self.rect.centery, x, y, self, 50, slow_mo)

    def update(self):
        if pygame.sprite.spritecollide(self, Players, True):  # если игрок пересекается с врагом, то он умирает
            pass
        if self.rect.centerx > self.distancex:
            self.rect.centerx -= 1
        if self.rect.centerx < self.distancex:
            self.rect.centerx += 1
        if self.rect.centery < self.distancey:
            self.rect.centery += 1
        if self.rect.centery > self.distancey:
            self.rect.centery -= 1
        # Если враг добрался до поля, то он переходит в боевой режим
        if self.rect.centerx == self.distancex and self.rect.centery == self.distancey and self.starting:
            self.starting = False


class Bullet(MoveObject):  # Пуля
    image = pygame.transform.scale(load_image("bullet.png"), (10, 5))

    def __init__(self, x, y, where_x, where_y, object, bullet_speed, slow_mo):
        super().__init__(self.image, x, y)
        if not slow_mo:  # Если включено замедленное время, то играет другой звук
            gunshot.play()
        else:
            slow_mo_shot.play()
        bulletfall.play()
        self.rotate(where_x, where_y)
        self.start = x, y
        self.where_x = where_x
        self.where_y = where_y
        self.speed = bullet_speed
        # Копируются группы игрока, врагов, а так же патронов. Это нужно чтобы при спавне пули она не уничтожала себи и стреляющего
        self.Players = Players.copy()
        self.Players.remove(object)
        self.Enemy = Enemys.copy()
        self.Enemy.remove(object)
        Bullets.add(self)
        self.Bullets = Bullets.copy()
        self.Bullets.remove(self)

    def update(self):
        global score
        # Признаюсь сразу - не лучшая формула для того, чтобы просчитать полёт снаряда
        # Я бы давно её исправил, но есть проблема - я сам не знаю как я составил эту формулу
        # Просто в один момент она возникла у меня в голове, и я попробовал её
        if self.where_x > self.start[0]:
            self.rect.centerx += (self.where_x - self.start[0]) // self.speed
        elif self.where_x < self.start[0]:
            self.rect.centerx += (self.where_x - self.start[0]) // self.speed
        if self.where_y < self.start[1]:
            self.rect.centery += (self.where_y - self.start[1]) // self.speed
        elif self.where_y > self.start[1]:
            self.rect.centery += (self.where_y - self.start[1]) // self.speed
        if pygame.sprite.spritecollide(self, self.Enemy, True):
            # Если мы попадаем по врагу, мы добавляем очки, а так же спавним кровь
            get_shot.play()
            numbers = range(-5, 6)
            for _ in range(30):
                Particle((self.rect.centerx, self.rect.centery), random.choice(numbers), random.choice(numbers))
            score += 100
            self.kill()
        if pygame.sprite.spritecollide(self, self.Players, True):  # Если Попадаем по игроку, то убиваем его
            self.kill()
        if pygame.sprite.spritecollide(self, self.Bullets, True):  # Если по пули, то удаляем её, и добавляем очки
            score += 50
            self.kill()
        if self.rect.centerx < 95 or self.rect.centerx > 620 or self.rect.centery < 100 or self.rect.centery > 700:
            # если мы улетаем за пределы карты, то уничтожаем пулю
            self.kill()


class InvinsibleLine(pygame.sprite.Sprite):
    def __init__(self, start_point, end_point, to_where):
        super().__init__(all_sprites)
        # Создаём п невидимую стену, чтобы проверить, может ли игрок переместиться
        # to_where Выбирает, вертикальная ли стенка, или горизонтальная
        if to_where == 1:
            self.image = pygame.Surface([0, end_point[1] - start_point[1]])
            self.rect = pygame.Rect(start_point[0], start_point[1], 1, end_point[1] - start_point[1])
        else:
            self.image = pygame.Surface([end_point[0] - start_point[0], 0])
            self.rect = pygame.Rect(start_point[0], start_point[1], end_point[0] - start_point[0], 1)


Cursors = pygame.sprite.Group()

clock = pygame.time.Clock()  # создаём объект clock

cursor = Cursor(Cursors)


def main_game():  # Главная игра
    global score
    score = 0  # Обнуляем очки
    # Удаляем оставшихся на карте объекты
    for enemy in Enemys:
        enemy.kill()
    for part in Blood:
        part.kill()
    for bullets in Bullets:
        bullets.kill()
    pygame.display.flip()
    # Создаём игрока
    player = Player()
    Players.add(player)
    all_sprites.add(player)
    # Обновляем счётчик кадров
    second = 0
    # Создаём рамки арены и загружаем свою арену
    Vertical_left.add(InvinsibleLine([95, 80], [95, 725], 1))
    Vertical_right.add(InvinsibleLine([617, 80], [617, 725], 1))
    Horizontal_Up.add(InvinsibleLine([95, 105], [646, 75], 2))
    Horizontal_Down.add(InvinsibleLine([95, 700], [617, 700], 2))
    image = load_image("map_fon.png")
    # Рисуем интерфейс, а конкретно - Стамину и количество патронов
    stamina = Interface(664, 200, 50, 50, "Stamina")
    bullets = Interface(664, 300, 50, 50, "Bullets")
    # переменная для проверки слоумо
    Slow_mo = False
    while player.alive():
        second += 1  # начинаем считать кадры
        # проверяем логику врогов в момент когда они уже стартовали
        for enemy in Enemys:
            if not enemy.starting:
                enemy.rotate(player.rect.centerx, player.rect.centery)
            if second % 10 == 0 and not enemy.starting:
                enemy.move()
            if second % random.randint(70, 150) == 0 and not enemy.starting:
                enemy.shoot(player.rect.centerx, player.rect.centery, player, Slow_mo)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                # Останавливаем звуи и убиваем игрока если заканчиваем гру
                for sound in all_sounds:
                    sound.stop()
                player.kill()
            if event.type == pygame.MOUSEMOTION:
                # Если мышка в рамках окна, мы рисуем прицел
                if pygame.mouse.get_focused():
                    cursor.update(event.pos)
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # Стреляем(знаю, очевидно =))
                player.shoot(event.pos, Slow_mo)
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
                # Проверяем включено ли замедление времени, и включаем/выключаем в отличии от его состояния
                if not Slow_mo:
                    Slow_mo = True
                    slow_mo_sound.play(loops=1000)
                else:
                    Slow_mo = False
                    slow_mo_sound.stop()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                # Если игрок нажимает ескейп, выключаем игру
                return score
        # поворачиваем игрока в сторону курсора
        player.rotate(cursor.rect.centerx, cursor.rect.centery)
        all_sprites.draw(screen)
        Blood.update()
        # Если включено замедление, а так же стамина больше нуля, то замедляем время
        if Slow_mo and player.durability > 0:
            Fps = 15  # Буквально замедление времени)
            if second % 1 == 0:
                player.durability -= 1
        else:
            Slow_mo = False
            Fps = 60
            slow_mo_sound.stop()
        # Если курсор в рамках окна, то мы его рисуем
        if pygame.mouse.get_focused():
            Cursors.draw(screen)
            pygame.mouse.set_visible(False)
        # Проверяем, Какой текст должен отображаться в пункте патронов
        if player.is_reloading:
            bullets_text = "Reload"
        else:
            bullets_text = str(player.bullets) + " / 10"
        bullets.render(screen, bullets_text)
        # Проверяем, перезаряжается ли игрок, а так же время перезарядки
        if player.bullets < 10 and second % 200 == 0 and player.is_reloading:
            player.bullets = 10
            player.is_reloading = False
            reloaded_gun.play()
        all_sprites.update()
        Blood.update()
        Bullets.update()
        pygame.display.flip()
        screen.blit(image, (0, 0))  # Отображаем Карту
        # рендерим информацию о стамине игрока
        stamina.render(screen, str(int(player.durability)))
        clock.tick(Fps)
        # Если врагов меньше 6, и нужное время, мы спавним врага
        if second % 200 == 0 and len(Enemys) < 6:
            for _ in range(6 - len(Enemys)):
                Enemys.add(Enemy())
        # востанавливаем Стамину игрока
        if player.durability < 100 and second % 5 == 0:
            print(player.durability)
            player.durability += 1
    return score
    pygame.quit()


def start_screen():  # Заставка, по своей логике идиентична примеру в уроке
    game_name = "Hotline Python"
    intro_text = ["Правила     игры", "",
                  "Периодически     на     карте     спавнятся     противники",
                  "Убивая     их     вы     получаете     очки",
                  "Игра     идет     до     смерти     игрока", "",
                  "Управление", "",
                  "WASD     -     Ходить,     Shift     -     Бег",
                  "R     -     Перезарядка",
                  "Левая кнопка мыши     -     Стрелять"
        , "Правая кнопка мыши     -     Замедление    вв Времени"]

    fon = pygame.transform.scale(load_image('menu_fon.jpg'), (WIDTH, HEIGHT))
    screen.blit(fon, (0, 0))
    font = pygame.font.Font('Data/justicelaser.ttf', 50)
    string_rendered = font.render(game_name, 1, pygame.Color('white'))
    intro_rect = string_rendered.get_rect()
    text_coord = 50
    intro_rect.top = text_coord
    intro_rect.x = WIDTH // 2 - string_rendered.get_width() // 2
    text_coord += intro_rect.height
    screen.blit(string_rendered, (intro_rect.x, 130))
    text_coord = 250

    font = pygame.font.Font('Data/rules_font.ttf', 20)
    for line in intro_text:
        string_rendered = font.render(line, 1, pygame.Color('white'))
        intro_rect = string_rendered.get_rect()
        text_coord += 10
        intro_rect.top += text_coord
        intro_rect.x = WIDTH // 2 - string_rendered.get_width() // 2
        text_coord += intro_rect.height
        screen.blit(string_rendered, intro_rect)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                terminate()
            elif event.type == pygame.KEYDOWN or \
                    event.type == pygame.MOUSEBUTTONDOWN:
                return  # начинаем игру
        if pygame.mouse.get_focused():
            pygame.mouse.set_visible(False)
        pygame.display.flip()
        clock.tick(Fps)


def game_over(score):  # Заставка конца игры, по своей логике идиентична примеру в уроке
    game_name = "Game Over"
    intro_text = ["Ваши  очки: ", " ",
                  str(score),
                  "",
                  "R - Начать с начала",
                  "",
                  "Спасибо  за   игру!"]

    fon = pygame.transform.scale(load_image('game_over_fon.jpg'), (WIDTH, HEIGHT))
    screen.blit(fon, (0, 0))
    font = pygame.font.Font('Data/justicelaser.ttf', 50)
    string_rendered = font.render(game_name, 1, pygame.Color('white'))
    intro_rect = string_rendered.get_rect()
    text_coord = 200
    intro_rect.top = text_coord
    intro_rect.x = WIDTH // 2 - string_rendered.get_width() // 2
    text_coord += intro_rect.height
    screen.blit(string_rendered, (intro_rect.x, 130))
    text_coord = 300

    font = pygame.font.Font('Data/rules_font.ttf', 20)
    for line in intro_text:
        string_rendered = font.render(line, 1, pygame.Color('white'))
        intro_rect = string_rendered.get_rect()
        text_coord += 10
        intro_rect.top += text_coord
        intro_rect.x = WIDTH // 2 - string_rendered.get_width() // 2
        text_coord += intro_rect.height
        screen.blit(string_rendered, intro_rect)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                terminate()
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return 'Not restart'
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                return "restart"  # начинаем игру
        if pygame.mouse.get_focused():
            pygame.mouse.set_visible(False)
        pygame.display.flip()
        clock.tick(Fps)


def music_restart(music):  # чтобы не повторять несколько раз строчки связанные с воспроизведением музыки
    pygame.mixer.music.load(music)
    pygame.mixer.music.set_volume(0.4)
    pygame.mixer.music.play()


if __name__ == "__main__":
    # по очереди запускаем стартовый экран, саму игру а так же экран конца игры
    music_restart("Data/title_song.mp3")
    start_screen()
    # выбираем случайную боевую музыку
    music_restart(random.choice(battle_music))
    score = main_game()  # получаем очки
    while True:
        music_restart("Data/Game_over_song.mp3")
        if game_over(score) == "restart":  # Ресуем очки, а так же если игрок решает перезапустить игру
            # то мы её перезапускаем
            music_restart(random.choice(battle_music))
            score = main_game()
        else:
            break
