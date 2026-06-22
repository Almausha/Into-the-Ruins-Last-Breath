from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import math
import time
import random
WIN_W, WIN_H = 1200, 650
BOUNDARY      = 550
BUNKER_X1     = -BOUNDARY
BUNKER_X2     = -250
BUNKER_Y1     = -200
BUNKER_Y2     =  200
BUNKER_WALL_H = 120
BUNKER_WALL_T = 18
DOOR_W        = 60
BUILDINGS = [
    dict(cx=-200, cy=460,  w=160, d=140, h=185, door_side='S', has_obj=True,  obj_type='water_bottle'),
    dict(cx= 100, cy=470,  w=150, d=130, h=200, door_side='S', has_obj=True,  obj_type='first_aid'),
    dict(cx= 390, cy=455,  w=160, d=145, h=175, door_side='S', has_obj=False, obj_type=None),
    dict(cx=-150, cy=-465, w=155, d=135, h=190, door_side='N', has_obj=True,  obj_type='food_freezer'),
    dict(cx= 180, cy=-470, w=160, d=140, h=180, door_side='N', has_obj=False, obj_type=None),
    dict(cx= 430, cy=-455, w=145, d=130, h=195, door_side='N', has_obj=True,  obj_type='oxygen_tanker'),
    dict(cx= 460, cy= 280, w=130, d=155, h=185, door_side='W', has_obj=True,  obj_type='gun_box'),
    dict(cx= 465, cy= -80, w=130, d=150, h=200, door_side='W', has_obj=True,  obj_type='light_box'),
]
TOTAL_KITS = sum(1 for b in BUILDINGS if b['has_obj'])

OBJ_GLOW = {
    'water_bottle':  (0.30, 0.60, 0.90),
    'first_aid':     (0.85, 0.15, 0.15),
    'food_freezer':  (0.20, 0.70, 0.90),
    'oxygen_tanker': (0.20, 0.50, 0.80),
    'gun_box':       (0.80, 0.60, 0.10),
    'light_box':     (0.90, 0.65, 0.15),
}

ROCK_CLUSTERS = [
    (-160,   0, 4, 18), ( -50,  40, 3, 16), (  60, -20, 4, 20),
    (-100, 200, 3, 15), (  80, 310, 4, 18), ( -80,-220, 3, 16),
    ( 120,-330, 4, 18), ( 280,  80, 3, 15), ( 370, -60, 4, 17),
]

random.seed(77)
OUTSIDE_DEBRIS = []
for _ in range(50):
    _dx = random.randint(-BOUNDARY+20, BOUNDARY-20)
    _dy = random.randint(-BOUNDARY+20, BOUNDARY-20)
    if BUNKER_X1 <= _dx <= BUNKER_X2 and BUNKER_Y1 <= _dy <= BUNKER_Y2:
        continue
    OUTSIDE_DEBRIS.append((_dx, _dy, random.uniform(7,28), random.uniform(7,24), random.uniform(4,16)))

random.seed(12)
CRACK_LINES = [
    (random.randint(-BOUNDARY,BOUNDARY), random.randint(-BOUNDARY,BOUNDARY),
     random.randint(12,90), random.uniform(0,math.pi))
    for _ in range(40)
]

TABLE_CX = (BUNKER_X1 + BUNKER_X2) / 2
TABLE_CY = 0.0
TABLE_HW = 38
TABLE_HD = 30

ENEMY_SPAWN_POINTS = [
    ( 400,  400), (-100,  480), ( 300, -420),
    ( 480,  100), ( 480, -200), ( 200,  480),
    ( 100, -480), ( 450,  300), ( 350, -350),
]
MAX_ENEMIES       = 2
ENEMY_SPEED       = 55.0
ENEMY_RADIUS      = 22.0
ENEMY_DMG_RANGE   = 50.0
ENEMY_BOUNCE_DIST = 55.0
ENEMY_SPAWN_CD    = 12.0

game_state = "INTRO"

PLAYER_START_X   = float(BUNKER_X1 + 80)
PLAYER_START_Y   = 0.0
PLAYER_START_ANG = 40.0

px, py, pz = PLAYER_START_X, PLAYER_START_Y, 0.0
p_ang      = PLAYER_START_ANG
P_SPEED    = 23
P_ROT      = 15.0
jump_vel   = 0.0
is_jumping = False
GRAVITY    = 600.0
JUMP_INIT  = 280.0
P_RADIUS   = 22.0

player_hearts  = 10
invincible_t   = 0.0
rope_dmg_t     = 0.0
rock_dmg_t     = 0.0
enemy_dmg_t    = 0.0
dmg_flash_type = ""

current_tool = 0
TOOL_NAMES   = ["HAMMER", "KNIFE", "GUN"]

cam_h        = 180.0
cam_v        = 28.0
cam_r        = 380.0
CAM_R_MIN    = 100.0
CAM_R_MAX    = 900.0
fovY         = 65.0
first_person = False

POLLUTION_MAX_TIME = 10.0
pollution          = 0.0
POLL_MOVE_DRAIN    = 0.001
POLL_FIRE_DRAIN    = 0.002
POLL_KIT_REWARD    = 0.10

score       = 0
SCORE_KIT   = 10
SCORE_ENEMY = 15

bullets      = []
BULLET_SPEED = 900.0
BULLET_LIFE  = 2.5
BULLET_R     = 5.0
miss_count   = 0
ammo         = 15
shoot_cd     = 0.0

enemies        = []
enemy_spawn_cd = 5.0

wall_hits = {}
collected = set()
rope_cut  = [False] * len(BUILDINGS)

win_bounce_t    = 0.0
gameover_t      = 0.0
flash_timer     = 0.0
fall_angle      = 0.0
dmg_label_t     = 0.0
start_time      = time.time()
last_frame      = time.time()
gameover_reason = ""
key_w = False
key_s = False
key_a = False
key_d = False


def dist2(ax, ay, bx, by):
    return math.sqrt((ax-bx)**2 + (ay-by)**2)


def set_ortho_2d():
    glDisable(GL_DEPTH_TEST)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, WIN_W, 0, WIN_H)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()


def restore_3d():
    glMatrixMode(GL_MODELVIEW)
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    glEnable(GL_DEPTH_TEST)


def draw_text_colored(x, y, text, r, g, b, font=GLUT_BITMAP_HELVETICA_18):
    set_ortho_2d()
    glColor3f(r, g, b)
    glRasterPos2f(x, y)
    for ch in text:
        glutBitmapCharacter(font, ord(ch))
    restore_3d()


def draw_text_large(x, y, text, r=0.80, g=0.70, b=0.45):
    draw_text_colored(x, y, text, r, g, b, font=GLUT_BITMAP_HELVETICA_18)


def draw_rect_2d(x, y, w, h, r, g, b):
    set_ortho_2d()
    glColor3f(r, g, b)
    glBegin(GL_QUADS)
    glVertex2f(x,   y)
    glVertex2f(x+w, y)
    glVertex2f(x+w, y+h)
    glVertex2f(x,   y+h)
    glEnd()
    restore_3d()


def draw_line_2d(x0, y0, x1, y1, r, g, b):
    set_ortho_2d()
    glColor3f(r, g, b)
    glBegin(GL_LINES)
    glVertex2f(x0, y0)
    glVertex2f(x1, y1)
    glEnd()
    restore_3d()


def draw_wire_cube_manual(sx, sy, sz):
    hx, hy, hz = sx/2, sy/2, sz/2
    corners = [
        (-hx,-hy,-hz), (hx,-hy,-hz), (hx,hy,-hz), (-hx,hy,-hz),
        (-hx,-hy, hz), (hx,-hy, hz), (hx,hy, hz), (-hx,hy, hz),
    ]
    edges = [(0,1),(1,2),(2,3),(3,0),(4,5),(5,6),(6,7),(7,4),(0,4),(1,5),(2,6),(3,7)]
    glBegin(GL_LINES)
    for a, b in edges:
        glVertex3f(*corners[a])
        glVertex3f(*corners[b])
    glEnd()


def draw_dark_overlay(r, g, b):
    set_ortho_2d()
    glColor3f(r, g, b)
    glBegin(GL_QUADS)
    glVertex2f(0, 0)
    glVertex2f(WIN_W, 0)
    glVertex2f(WIN_W, WIN_H)
    glVertex2f(0, WIN_H)
    glEnd()
    restore_3d()

def draw_filled_circle_2d(cx, cy, radius, r, g, b, segments=32):
    glColor3f(r, g, b)
    for i in range(segments):
        a0 = 2.0*math.pi*i/segments
        a1 = 2.0*math.pi*(i+1)/segments
        glBegin(GL_QUADS)
        glVertex2f(cx, cy)
        glVertex2f(cx + radius*math.cos(a0), cy + radius*math.sin(a0))
        glVertex2f(cx + radius*math.cos(a1), cy + radius*math.sin(a1))
        glVertex2f(cx, cy)
        glEnd()


def draw_circle_outline_2d(cx, cy, radius, r, g, b, segments=32):
    glColor3f(r, g, b)
    for i in range(segments):
        a0 = 2.0*math.pi*i/segments
        a1 = 2.0*math.pi*(i+1)/segments
        glBegin(GL_LINES)
        glVertex2f(cx + radius*math.cos(a0), cy + radius*math.sin(a0))
        glVertex2f(cx + radius*math.cos(a1), cy + radius*math.sin(a1))
        glEnd()


def draw_floor_tile_outline(gx, gy, tile):
    glBegin(GL_LINES)
    glVertex3f(gx,      gy,      0.5)
    glVertex3f(gx+tile, gy,      0.5)
    glVertex3f(gx+tile, gy,      0.5)
    glVertex3f(gx+tile, gy+tile, 0.5)
    glVertex3f(gx+tile, gy+tile, 0.5)
    glVertex3f(gx,      gy+tile, 0.5)
    glVertex3f(gx,      gy+tile, 0.5)
    glVertex3f(gx,      gy,      0.5)
    glEnd()

def manual_disk(inner_r, outer_r, segments=16):
    for i in range(segments):
        a0 = 2.0 * math.pi * i / segments
        a1 = 2.0 * math.pi * (i + 1) / segments
        cos0, sin0 = math.cos(a0), math.sin(a0)
        cos1, sin1 = math.cos(a1), math.sin(a1)
        if inner_r <= 0:
            glBegin(GL_QUADS)
            glVertex3f(0.0, 0.0, 0.0)
            glVertex3f(outer_r * cos0, outer_r * sin0, 0.0)
            glVertex3f(outer_r * cos1, outer_r * sin1, 0.0)
            glVertex3f(0.0, 0.0, 0.0)
            glEnd()
        else:
            glBegin(GL_QUADS)
            glVertex3f(inner_r * cos0, inner_r * sin0, 0.0)
            glVertex3f(outer_r * cos0, outer_r * sin0, 0.0)
            glVertex3f(outer_r * cos1, outer_r * sin1, 0.0)
            glVertex3f(inner_r * cos1, inner_r * sin1, 0.0)
            glEnd()

def solid_sphere(radius, slices=12, stacks=10):
    q = gluNewQuadric()
    gluSphere(q, radius, slices, stacks)


def draw_background_color(r, g, b):
    glDisable(GL_DEPTH_TEST)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, WIN_W, 0, WIN_H)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    glColor3f(r, g, b)
    glBegin(GL_QUADS)
    glVertex2f(0,     0)
    glVertex2f(WIN_W, 0)
    glVertex2f(WIN_W, WIN_H)
    glVertex2f(0,     WIN_H)
    glEnd()
    glMatrixMode(GL_MODELVIEW)
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    glEnable(GL_DEPTH_TEST)


def reset_game():
    global px, py, pz, p_ang, jump_vel, is_jumping, current_tool
    global player_hearts, invincible_t, rope_dmg_t, rock_dmg_t, enemy_dmg_t
    global pollution, score, bullets, miss_count, ammo, shoot_cd
    global wall_hits, collected, rope_cut
    global win_bounce_t, gameover_t, flash_timer, fall_angle
    global start_time, game_state, cam_h, cam_v, cam_r, first_person
    global enemies, enemy_spawn_cd, dmg_label_t, dmg_flash_type
    global key_w, key_s, key_a, key_d

    px, py, pz     = PLAYER_START_X, PLAYER_START_Y, 0.0
    p_ang          = PLAYER_START_ANG
    jump_vel       = 0.0
    is_jumping     = False
    current_tool   = 0
    player_hearts  = 10
    invincible_t   = 0.0
    rope_dmg_t     = 0.0
    rock_dmg_t     = 0.0
    enemy_dmg_t    = 0.0
    dmg_flash_type = ""
    dmg_label_t    = 0.0
    pollution      = 0.0
    score          = 0
    bullets        = []
    miss_count     = 0
    ammo           = 15
    shoot_cd       = 0.0
    wall_hits      = {}
    collected      = set()
    rope_cut       = [False] * len(BUILDINGS)
    enemies        = []
    enemy_spawn_cd = 5.0
    win_bounce_t   = 0.0
    gameover_t     = 0.0
    flash_timer    = 0.0
    fall_angle     = 0.0
    start_time     = time.time()
    game_state     = "PLAY"
    key_w          = False
    key_s          = False
    key_a          = False
    key_d          = False
    cam_h          = 180.0
    cam_v          = 28.0
    cam_r          = 380.0
    first_person   = False


def inside_bunker_area(x, y):
    return (BUNKER_X1+BUNKER_WALL_T < x < BUNKER_X2-BUNKER_WALL_T and
            BUNKER_Y1+BUNKER_WALL_T < y < BUNKER_Y2-BUNKER_WALL_T)


def in_bunker_door_zone(x, y):
    return (abs(x-BUNKER_X2) < BUNKER_WALL_T+P_RADIUS+4 and abs(y) < DOOR_W-P_RADIUS)


def building_box(b):
    hw = b['w']/2 + BUNKER_WALL_T
    hd = b['d']/2 + BUNKER_WALL_T
    return b['cx']-hw, b['cy']-hd, b['cx']+hw, b['cy']+hd


def in_building_door(b, x, y, bidx=None):
    if bidx is None:
        try:
            bidx = BUILDINGS.index(b)
        except:
            bidx = -1
   
    if bidx >= 0 and not rope_cut[bidx]:
        return False  
  
    hw, hd = b['w']/2, b['d']/2
    cx, cy = b['cx'], b['cy']
    ds     = b['door_side']
    gap    = 52
    
    if ds == 'N':
        return abs(x-cx) < gap and abs(y-(cy+hd)) < BUNKER_WALL_T+P_RADIUS+4
    if ds == 'S':
        return abs(x-cx) < gap and abs(y-(cy-hd)) < BUNKER_WALL_T+P_RADIUS+4
    if ds == 'E':
        return abs(y-cy) < gap and abs(x-(cx+hw)) < BUNKER_WALL_T+P_RADIUS+4
    return abs(y-cy) < gap and abs(x-(cx-hw)) < BUNKER_WALL_T+P_RADIUS+4

def inside_building(b, x, y):
    try:
        bidx = BUILDINGS.index(b)
        if not rope_cut[bidx]:
            return False  
    except:
        pass

    hw = b['w']/2 - BUNKER_WALL_T - 2
    hd = b['d']/2 - BUNKER_WALL_T - 2
    return abs(x-b['cx']) < hw and abs(y-b['cy']) < hd


def check_collision(nx, ny):
    if abs(nx) > BOUNDARY-P_RADIUS or abs(ny) > BOUNDARY-P_RADIUS:
        return False
    crosses_front = (px < BUNKER_X2-P_RADIUS) != (nx < BUNKER_X2-P_RADIUS)
    if crosses_front:
        if not in_bunker_door_zone(nx, ny):
            return False
    if BUNKER_X1 < nx < BUNKER_X2:
        if abs(ny-BUNKER_Y2) < BUNKER_WALL_T+P_RADIUS:
            return False
        if abs(ny-BUNKER_Y1) < BUNKER_WALL_T+P_RADIUS:
            return False
    if BUNKER_Y1 < ny < BUNKER_Y2:
        if abs(nx-BUNKER_X1) < BUNKER_WALL_T+P_RADIUS:
            return False
    if abs(nx-TABLE_CX) < TABLE_HW+P_RADIUS and abs(ny-TABLE_CY) < TABLE_HD+P_RADIUS:
        return False
    for b in BUILDINGS:
        bx0, by0, bx1, by1 = building_box(b)
        if not (bx0-5 < nx < bx1+5 and by0-5 < ny < by1+5):
            continue
        if inside_building(b, nx, ny):
            continue
        if in_building_door(b, nx, ny):
            continue
        if bx0 < nx < bx1 and by0 < ny < by1:
            return False
    return True
def check_rock_collision(nx, ny):
    if pz >= 30:
        return False
    random.seed(88)
    for rcx, rcy, count, base_r in ROCK_CLUSTERS:
        for _ in range(count):
            rx = rcx + random.uniform(-base_r*1.4, base_r*1.4)
            ry = rcy + random.uniform(-base_r*1.0, base_r*1.0)
            rr = base_r * random.uniform(0.55, 1.0)
            if dist2(nx, ny, rx, ry) < rr+P_RADIUS-5:
                return True
    return False


def player_in_rope_zone():
    for i, b in enumerate(BUILDINGS):
        if rope_cut[i]:
            continue
        hw, hd = b['w']/2, b['d']/2
        cx, cy = b['cx'], b['cy']
        ds     = b['door_side']
        if ds == 'N':
            rx, ry = cx, cy+hd
        elif ds == 'S':
            rx, ry = cx, cy-hd
        elif ds == 'E':
            rx, ry = cx+hw, cy
        else:
            rx, ry = cx-hw, cy
        if dist2(px, py, rx, ry) < 45:
            return i
    return -1


def check_win():
    global game_state
    if len(collected) >= TOTAL_KITS and inside_bunker_area(px, py):
        game_state = "WIN"


def interact():
    global flash_timer, score, pollution
    if current_tool == 1:
        for i, b in enumerate(BUILDINGS):
            if rope_cut[i]:
                continue
            hw, hd = b['w']/2, b['d']/2
            cx, cy = b['cx'], b['cy']
            ds     = b['door_side']
            if ds == 'N':
                rx, ry = cx, cy+hd
            elif ds == 'S':
                rx, ry = cx, cy-hd
            elif ds == 'E':
                rx, ry = cx+hw, cy
            else:
                rx, ry = cx-hw, cy
            if dist2(px, py, rx, ry) < 80:
                rope_cut[i] = True
                return

    if current_tool == 0:
        for bidx, b in enumerate(BUILDINGS):
            if not b['has_obj'] or bidx in collected:
                continue
            cx, cy = b['cx'], b['cy']
            hw, hd = b['w']/2, b['d']/2
            ds     = b['door_side']
            if ds == 'S':
                wx, wy, wlen, wax = cx,         cy+hd*0.35, b['w']-30, 'x'
            elif ds == 'N':
                wx, wy, wlen, wax = cx,         cy-hd*0.35, b['w']-30, 'x'
            elif ds == 'W':
                wx, wy, wlen, wax = cx+hw*0.35, cy,         b['d']-30, 'y'
            else:
                wx, wy, wlen, wax = cx-hw*0.35, cy,         b['d']-30, 'y'
            if dist2(px, py, wx, wy) > 110:
                continue
            n = max(2, int(wlen/30))
            for i in range(n):
                key = (bidx, i)
                if wall_hits.get(key, 3) <= 0:
                    continue
                offset = -wlen/2 + (i+0.5)*(wlen/n)
                sx = wx+offset if wax == 'x' else wx
                sy = wy        if wax == 'x' else wy+offset
                if dist2(px, py, sx, sy) < 75:
                    wall_hits[key] = wall_hits.get(key, 3) - 1
                    flash_timer = 0.10
                    if all(wall_hits.get((bidx,j), 3) <= 0 for j in range(n)):
                        collected.add(bidx)
                        score     += SCORE_KIT
                        pollution  = max(0.0, pollution-POLL_KIT_REWARD)
                    return


def fire_bullet():
    global ammo, pollution, shoot_cd, flash_timer
    if current_tool != 2 or ammo <= 0 or shoot_cd > 0:
        return
    rad = math.radians(p_ang)
    bdx = math.sin(rad)
    bdy = math.cos(rad)
    bullets.append({
        'x': px+bdx*30, 'y': py+bdy*30, 'z': pz+50,
        'dx': bdx, 'dy': bdy, 'life': BULLET_LIFE
    })
    ammo       -= 1
    pollution   = min(1.0, pollution+POLL_FIRE_DRAIN)
    shoot_cd    = 0.25
    flash_timer = 0.05


def update_bullets(dt):
    global miss_count, pollution, score, game_state, gameover_reason, gameover_t
    to_del = []
    for idx, b in enumerate(bullets):
        b['x']    += b['dx'] * BULLET_SPEED * dt
        b['y']    += b['dy'] * BULLET_SPEED * dt
        b['life'] -= dt
        dead = False

        if not dead:
            for en in enemies:
                if en.get('dead', False):
                    continue
                if dist2(b['x'], b['y'], en['x'], en['y']) < ENEMY_RADIUS+BULLET_R:
                    en['dead']   = True
                    en['dead_t'] = 0.0
                    score       += SCORE_ENEMY
                    dead         = True
                    break

        if b['life'] <= 0 or abs(b['x']) > BOUNDARY or abs(b['y']) > BOUNDARY:
            if b['life'] > 0:
                miss_count += 1
                if miss_count >= 10:
                    game_state      = "OVER"
                    gameover_reason = "Too many missed shots! Wasted all ammunition."
                    gameover_t      = 0.0
            dead = True

        if not dead:
            for bidx, bld in enumerate(BUILDINGS):
                if not bld['has_obj'] or bidx in collected:
                    continue
                cx, cy = bld['cx'], bld['cy']
                hw, hd = bld['w']/2, bld['d']/2
                ds     = bld['door_side']
                if ds == 'S':
                    wx, wy, wlen, wax = cx,         cy+hd*0.35, bld['w']-30, 'x'
                elif ds == 'N':
                    wx, wy, wlen, wax = cx,         cy-hd*0.35, bld['w']-30, 'x'
                elif ds == 'W':
                    wx, wy, wlen, wax = cx+hw*0.35, cy,         bld['d']-30, 'y'
                else:
                    wx, wy, wlen, wax = cx-hw*0.35, cy,         bld['d']-30, 'y'
                n2 = max(2, int(wlen/30))
                for j in range(n2):
                    key = (bidx, j)
                    if wall_hits.get(key, 3) <= 0:
                        continue
                    off = -wlen/2 + (j+0.5)*(wlen/n2)
                    sx  = wx+off if wax == 'x' else wx
                    sy  = wy     if wax == 'x' else wy+off
                    if dist2(b['x'], b['y'], sx, sy) < 22:
                        wall_hits[key] = wall_hits.get(key, 3) - 1
                        if all(wall_hits.get((bidx,k), 3) <= 0 for k in range(n2)):
                            collected.add(bidx)
                            score     += SCORE_KIT
                            pollution  = max(0.0, pollution-POLL_KIT_REWARD)
                        dead = True
                        break
                if dead:
                    break

        if dead:
            to_del.append(idx)

    for i in reversed(to_del):
        bullets.pop(i)


def enemy_blocked_by_bunker(ex, ey):
    margin = ENEMY_RADIUS + 5
    return (BUNKER_X1-margin < ex < BUNKER_X2+margin and
            BUNKER_Y1-margin < ey < BUNKER_Y2+margin)


def spawn_enemy():
    if len([e for e in enemies if not e.get('dead', False)]) >= MAX_ENEMIES:
        return
    random.shuffle(ENEMY_SPAWN_POINTS)
    for spx, spy in ENEMY_SPAWN_POINTS:
        if inside_bunker_area(spx, spy):
            continue
        if math.hypot(spx-px, spy-py) < 150:
            continue
        enemies.append({
            'x': float(spx), 'y': float(spy),
            'dead': False, 'dead_t': 0.0,
            'pulse': random.uniform(0, math.pi*2), 'bounce_t': 0.0
        })
        return
    
def update_enemies(dt):
    global player_hearts, invincible_t, flash_timer, game_state, gameover_reason, gameover_t
    global enemy_dmg_t, dmg_flash_type, dmg_label_t, enemy_spawn_cd, ammo

    if game_state == "PLAY":
        enemy_spawn_cd -= dt
        if enemy_spawn_cd <= 0:
            spawn_enemy()
            enemy_spawn_cd = ENEMY_SPAWN_CD

    to_del = []
    for eidx, en in enumerate(enemies):
        if en['dead']:
            en['dead_t'] += dt
            if en['dead_t'] > 1.2:
                if random.random() < 0.4:
                    ammo += 2
                to_del.append(eidx)
            continue

        if game_state != "PLAY":
            continue

        dx2 = px - en['x']
        dy2 = py - en['y']
        d   = math.sqrt(dx2*dx2 + dy2*dy2)

        if d < ENEMY_BOUNCE_DIST:
            if d > 0.5:
                en['x'] -= (dx2/d) * ENEMY_SPEED * 1.5 * dt
                en['y'] -= (dy2/d) * ENEMY_SPEED * 1.5 * dt
            en['bounce_t'] = 0.4
        else:
            if en['bounce_t'] > 0:
                en['bounce_t'] -= dt
            else:
                if d > 1:
                    nx_e = en['x'] + (dx2/d) * ENEMY_SPEED * dt
                    ny_e = en['y'] + (dy2/d) * ENEMY_SPEED * dt
                    if not enemy_blocked_by_bunker(nx_e, ny_e):
                        en['x'] = nx_e
                        en['y'] = ny_e
                    else:
                        nx_only = en['x'] + (dx2/d) * ENEMY_SPEED * dt
                        if not enemy_blocked_by_bunker(nx_only, en['y']):
                            en['x'] = nx_only
                        else:
                            ny_only = en['y'] + (dy2/d) * ENEMY_SPEED * dt
                            if not enemy_blocked_by_bunker(en['x'], ny_only):
                                en['y'] = ny_only

        if d < ENEMY_DMG_RANGE:
            if enemy_dmg_t <= 0 and invincible_t <= 0:
                player_hearts -= 1
                invincible_t   = 1.5
                enemy_dmg_t    = 1.5
                flash_timer    = 0.20
                dmg_flash_type = "enemy"
                dmg_label_t    = 2.0
                if player_hearts <= 0:
                    game_state      = "OVER"
                    gameover_reason = "Killed by mutant creatures — no hearts left."
                    gameover_t      = 0.0

    if enemy_dmg_t > 0:
        enemy_dmg_t -= dt
    for i in reversed(to_del):
        enemies.pop(i)

def draw_enemies():
    t2 = time.time() - start_time
    q  = gluNewQuadric()
    for en in enemies:
        if en['dead']:
            alpha = max(0.05, 1.0 - en['dead_t'])
            glPushMatrix()
            glTranslatef(en['x'], en['y'], 6)
            glRotatef(90, 1, 0, 0)
            glColor3f(0.25*alpha, 0.45*alpha, 0.20*alpha)
            gluSphere(q, ENEMY_RADIUS*0.8, 10, 8)
            glPopMatrix()
            continue

        pulse_s = 1.0 + 0.12*math.sin(t2*3.0 + en['pulse'])
        body_r  = ENEMY_RADIUS * pulse_s

        glPushMatrix()
        glTranslatef(en['x'], en['y'], body_r)
        glColor3f(0.22, 0.48, 0.18)
    
        gluSphere(q, body_r, 14, 10)

        glColor3f(0.90, 0.10, 0.10)
        glPushMatrix()
        glTranslatef(-body_r*0.35, body_r*0.70, body_r*0.30)
        gluSphere(q, body_r*0.18, 6, 6)
        glPopMatrix()

        glPushMatrix()
        glTranslatef(body_r*0.35, body_r*0.70, body_r*0.30)
        gluSphere(q, body_r*0.18, 6, 6)
        glPopMatrix()

        glColor3f(0.18, 0.38, 0.14)
        for lox, loy in [(-10,-8), (10,-8), (-10,8), (10,8)]:
            glPushMatrix()
            glTranslatef(lox, loy, -body_r*0.8)
            glRotatef(180, 1, 0, 0)
            gluCylinder(q, 5, 3, body_r*0.9, 7, 1)
            glPopMatrix()
        glPopMatrix()


def draw_player():
    global fall_angle
    if first_person and game_state == "PLAY":
        return
    q = gluNewQuadric()
    glPushMatrix()
    glTranslatef(px, py, pz)

    if game_state == "OVER":
        fall_angle = min(90.0, gameover_t*150)
        glTranslatef(0, 0, 10)
        glRotatef(fall_angle, 1, 0, 0)
        glTranslatef(0, 0, -10)

    glRotatef(-p_ang, 0, 0, 1)

    glColor3f(0.20, 0.18, 0.14)
    for lx in [-10, 10]:
        glPushMatrix()
        glTranslatef(lx, 0, 0)
        gluCylinder(q, 7, 5, 30, 10, 1)
        glPopMatrix()

    glColor3f(0.28, 0.32, 0.25)
    glPushMatrix()
    glTranslatef(0, 0, 30)
    gluCylinder(q, 14, 12, 32, 14, 1)
    glPopMatrix()

    glColor3f(0.35, 0.30, 0.22)
    for ax in [-16, 16]:
        glPushMatrix()
        glTranslatef(ax, 0, 45)
        glRotatef(-80, 1, 0, 0)
        gluCylinder(q, 6, 4, 26, 8, 1)
        glPopMatrix()

    glColor3f(0.72, 0.60, 0.50)
    glPushMatrix()
    glTranslatef(0, 0, 68)
    gluSphere(q, 13, 12, 10)
    glPopMatrix()

    glColor3f(0.18, 0.55, 0.28)
    glPushMatrix()
    glTranslatef(0, 13, 68)
    glRotatef(90, 1, 0, 0)

    glPushMatrix()
    glTranslatef(0, 3, 0)
    glScalef(14, 2, 8)
    glutSolidCube(1)
    glPopMatrix()

    glPushMatrix()
    glTranslatef(-5, -2, 0)
    glRotatef(-30, 0, 0, 1)
    glScalef(5, 2, 8)
    glutSolidCube(1)
    glPopMatrix()

    glPushMatrix()
    glTranslatef(5, -2, 0)
    glRotatef(30, 0, 0, 1)
    glScalef(5, 2, 8)
    glutSolidCube(1)
    glPopMatrix()

    glColor3f(0.30, 0.26, 0.20)
    glPushMatrix()
    glTranslatef(0, 0, -4)
    manual_disk(0, 4, 8)
    glPopMatrix()
    glPopMatrix()

    glPushMatrix()
    glTranslatef(16, 8, 50)
    glRotatef(-70, 1, 0, 0)
    _draw_tool(q)
    glPopMatrix()

    glPopMatrix()


def _draw_tool(q):
    if current_tool == 0:
        glColor3f(0.35, 0.25, 0.12)
        gluCylinder(q, 3, 3, 30, 8, 1)
        glPushMatrix()
        glTranslatef(0, 0, 28)
        glColor3f(0.50, 0.50, 0.50)
        glScalef(10, 8, 10)
        glutSolidCube(1)
        glPopMatrix()
    elif current_tool == 1:
        glColor3f(0.30, 0.22, 0.10)
        gluCylinder(q, 3, 3, 14, 8, 1)
        glPushMatrix()
        glTranslatef(0, 0, 14)
        glColor3f(0.70, 0.70, 0.72)
        glScalef(3, 1.5, 20)
        glutSolidCube(1)
        glPopMatrix()
    else:
        glColor3f(0.22, 0.20, 0.18)
        glPushMatrix()
        glScalef(6, 6, 10)
        glutSolidCube(1)
        glPopMatrix()
        glPushMatrix()
        glTranslatef(0, 0, 18)
        gluCylinder(q, 2.5, 2.5, 28, 8, 1)
        glPopMatrix()


def draw_bullets_3d():
    t2 = time.time() - start_time
    q  = gluNewQuadric()
    for b in bullets:
        c = 0.8 + 0.2*math.sin(t2*20)
        glColor3f(c, c*0.85, c*0.20)
        glPushMatrix()
        glTranslatef(b['x'], b['y'], b['z'])
        # glutSolidSphere -> gluSphere
        gluSphere(q, BULLET_R, 6, 6)
        glPopMatrix()
        glColor3f(1.0, 0.5, 0.1)
        glBegin(GL_LINES)
        glVertex3f(b['x'],            b['y'],            b['z'])
        glVertex3f(b['x']-b['dx']*18, b['y']-b['dy']*18, b['z'])
        glEnd()


def draw_floor():
    tile = 80
    for gx in range(-BOUNDARY, BOUNDARY, tile):
        for gy in range(-BOUNDARY, BOUNDARY, tile):
            in_bk = (BUNKER_X1 <= gx < BUNKER_X2 and BUNKER_Y1 <= gy < BUNKER_Y2)
            ch    = ((gx//tile) + (gy//tile)) % 2
            if in_bk:
                s = 0.20 if ch == 0 else 0.24
                glColor3f(s, s*0.97, s*0.93)
            else:
                glColor3f(
                    0.23 if ch == 0 else 0.19,
                    0.20 if ch == 0 else 0.17,
                    0.17 if ch == 0 else 0.14
                )
            glBegin(GL_QUADS)
            glVertex3f(gx,      gy,      0)
            glVertex3f(gx+tile, gy,      0)
            glVertex3f(gx+tile, gy+tile, 0)
            glVertex3f(gx,      gy+tile, 0)
            glEnd()
            glColor3f(0.11, 0.10, 0.08)
            draw_floor_tile_outline(gx, gy, tile)

    glColor3f(0.10, 0.09, 0.08)
    for cx2, cy2, ln, ang in CRACK_LINES:
        glBegin(GL_LINES)
        glVertex3f(cx2, cy2, 0.8)
        glVertex3f(cx2 + ln*math.cos(ang), cy2 + ln*math.sin(ang), 0.8)
        glEnd()


def draw_outside_debris():
    for dx2, dy2, sx, sy, sz in OUTSIDE_DEBRIS:
        r2 = 0.26 + (sx%7)*0.012
        glColor3f(r2, r2*0.91, r2*0.84)
        glPushMatrix()
        glTranslatef(dx2, dy2, sz/2)
        glRotatef((dx2*13+dy2*7) % 360, 0.2, 0.5, 1.0)
        glScalef(sx, sy, sz)
        glutSolidCube(1)
        glPopMatrix()


def draw_dead_trees():
    q = gluNewQuadric()
    for sx, sy, h, r in [
        (-300, 300, 55, 6), (-400, 480, 40, 5), (180, -300, 70, 7), (-350, 350, 50, 6),
        ( 500, 200, 30, 4), ( 350,-430, 45, 5), ( 30, -490, 38, 5), ( 200, 510, 42, 6)
    ]:
        glColor3f(0.14, 0.13, 0.12)
        glPushMatrix()
        glTranslatef(sx, sy, 0)
        gluCylinder(q, r, r*0.6, h, 7, 1)
        glPopMatrix()

        glColor3f(0.18, 0.16, 0.14)
        glPushMatrix()
        glTranslatef(sx, sy, h)
        manual_disk(0, r*0.6, 7)
        glPopMatrix()


def draw_boundary_walls():
    step = 55
    random.seed(42)
    for i in range(-BOUNDARY, BOUNDARY+1, step):
        for bx, by in [(i,-BOUNDARY), (i,BOUNDARY), (-BOUNDARY,i), (BOUNDARY,i)]:
            hv = random.uniform(30, 90)
            glColor3f(0.22, 0.20, 0.18)
            glPushMatrix()
            glTranslatef(bx, by, hv/2)
            glScalef(step-3, BUNKER_WALL_T, hv)
            glutSolidCube(1)
            glPopMatrix()


def draw_bunker_walls():
    SLAB = [(0.24,0.22,0.20), (0.30,0.27,0.24), (0.34,0.31,0.27)]
    h    = BUNKER_WALL_H
    seg  = 40

    def slab_row(axis, fixed, v0, v1, skip=False, seed=19):
        total = v1 - v0
        n     = max(1, int(total/seg))
        random.seed(seed)
        for i in range(n):
            vc = v0 + i*(total/n) + (total/n)/2
            if skip and abs(vc) < DOOR_W+10:
                continue
            sh = h * random.uniform(0.5, 1.0)
            glColor3f(*SLAB[i%3])
            glPushMatrix()
            if axis == 'x':
                glTranslatef(vc, fixed, sh/2)
                glScalef(total/n-2, BUNKER_WALL_T, sh)
            else:
                glTranslatef(fixed, vc, sh/2)
                glScalef(BUNKER_WALL_T, total/n-2, sh)
            glutSolidCube(1)
            glPopMatrix()

    slab_row('x', BUNKER_Y2, BUNKER_X1, BUNKER_X2, seed=19)
    slab_row('x', BUNKER_Y1, BUNKER_X1, BUNKER_X2, seed=20)
    slab_row('y', BUNKER_X1, BUNKER_Y1, BUNKER_Y2, seed=21)
    slab_row('y', BUNKER_X2, BUNKER_Y1, BUNKER_Y2, skip=True, seed=33)

    glColor3f(0.15, 0.14, 0.13)
    for dy2 in [-DOOR_W, DOOR_W]:
        glPushMatrix()
        glTranslatef(BUNKER_X2, dy2, h/2)
        glScalef(BUNKER_WALL_T+6, 10, h+6)
        glutSolidCube(1)
        glPopMatrix()

    glPushMatrix()
    glTranslatef(BUNKER_X2, 0, h+4)
    glRotatef(3, 0, 1, 0)
    glScalef(BUNKER_WALL_T+4, DOOR_W*2+20, 12)
    glutSolidCube(1)
    glPopMatrix()


def draw_bunker_props():
    t2  = time.time() - start_time
    q   = gluNewQuadric()
    cx2 = (BUNKER_X1 + BUNKER_X2) / 2

    for by in [BUNKER_Y1+35, BUNKER_Y1+75, BUNKER_Y1+115]:
        bx = BUNKER_X1 + 35
        glColor3f(0.32, 0.28, 0.24)
        glPushMatrix()
        glTranslatef(bx, by, 0)
        gluCylinder(q, 7, 7, 32, 10, 1)
        glPopMatrix()

        glColor3f(0.22, 0.19, 0.16)
        glPushMatrix()
        glTranslatef(bx, by, 32)
        gluCylinder(q, 7, 0, 14, 10, 1)
        glPopMatrix()

    tx, ty = cx2, 0.0
    tth    = 38
    glColor3f(0.22, 0.20, 0.17)
    for lx, ly in [(-25,-20), (25,-20), (-25,20), (25,20)]:
        glPushMatrix()
        glTranslatef(tx+lx, ty+ly, 0)
        gluCylinder(q, 3, 3, tth, 8, 1)
        glPopMatrix()

    glColor3f(0.28, 0.25, 0.21)
    glPushMatrix()
    glTranslatef(tx, ty, tth)
    glScalef(70, 55, 5)
    glutSolidCube(1)
    glPopMatrix()

    glColor3f(0.18, 0.16, 0.14)
    glPushMatrix()
    glTranslatef(tx+20, ty-10, tth+3)
    gluCylinder(q, 2, 2, 28, 8, 1)
    glPopMatrix()

    pulse = 0.60 + 0.15*math.sin(t2*1.8)
    glColor3f(0.75*pulse, 0.48*pulse, 0.18*pulse)
    glPushMatrix()
    glTranslatef(tx+20, ty-10, tth+32)
    # glutSolidSphere -> gluSphere
    gluSphere(q, 5, 10, 10)
    glPopMatrix()


def draw_rock_clusters():
    q = gluNewQuadric()
    random.seed(88)
    for rcx, rcy, count, base_r in ROCK_CLUSTERS:
        for _ in range(count):
            rx    = rcx + random.uniform(-base_r*1.4, base_r*1.4)
            ry    = rcy + random.uniform(-base_r*1.0, base_r*1.0)
            rr    = base_r * random.uniform(0.55, 1.0)
            rh    = rr * random.uniform(0.5, 0.85)
            shade = 0.20 + random.uniform(0, 0.10)
            glColor3f(shade, shade*0.95, shade*0.88)
            glPushMatrix()
            glTranslatef(rx, ry, rh*0.4)
            glScalef(rr, rr*random.uniform(0.7, 1.0), rh)
            gluSphere(q, 1.0, 10, 7)
            glPopMatrix()
            glColor3f(0.10, 0.09, 0.08)
            glPushMatrix()
            glTranslatef(rx, ry, 0.5)
            manual_disk(0, rr*0.85, 10)
            glPopMatrix()


def draw_water_bottle(q, ox, oy, oz):
    glColor3f(0.28, 0.32, 0.36)
    glPushMatrix()
    glTranslatef(ox, oy, oz)
    gluCylinder(q, 5, 5, 18, 10, 1)
    glPopMatrix()

    glColor3f(0.20, 0.24, 0.28)
    glPushMatrix()
    glTranslatef(ox, oy, oz+18)
    gluCylinder(q, 5, 0, 6, 10, 1)
    glPopMatrix()

    glPushMatrix()
    glTranslatef(ox, oy, oz)
    manual_disk(0, 5, 10)
    glPopMatrix()

    glColor3f(0.35, 0.30, 0.22)
    glPushMatrix()
    glTranslatef(ox, oy, oz+9)
    manual_disk(5, 7, 10)
    glPopMatrix()


def draw_first_aid(q, ox, oy, oz):
    glColor3f(0.70, 0.68, 0.65)
    glPushMatrix()
    glTranslatef(ox, oy, oz+8)
    glScalef(20, 8, 16)
    glutSolidCube(1)
    glPopMatrix()

    glColor3f(0.75, 0.12, 0.10)
    glPushMatrix()
    glTranslatef(ox+10.5, oy, oz+8)
    glScalef(1, 1, 10)
    glutSolidCube(1)
    glPopMatrix()

    glPushMatrix()
    glTranslatef(ox+10.5, oy, oz+8)
    glScalef(1, 6, 1)
    glutSolidCube(1)
    glPopMatrix()

    glColor3f(0.45, 0.40, 0.32)
    glPushMatrix()
    glTranslatef(ox, oy, oz+16)
    glScalef(10, 3, 3)
    glutSolidCube(1)
    glPopMatrix()


def draw_food_freezer(q, ox, oy, oz):
    glColor3f(0.30, 0.27, 0.24)
    glPushMatrix()
    glTranslatef(ox, oy, oz+10)
    glScalef(26, 10, 20)
    glutSolidCube(1)
    glPopMatrix()

    glColor3f(0.18, 0.16, 0.14)
    glBegin(GL_LINES)
    glVertex3f(ox-13, oy-5, oz+19)
    glVertex3f(ox+13, oy-5, oz+19)
    glEnd()

    glColor3f(0.40, 0.34, 0.22)
    glPushMatrix()
    glTranslatef(ox+13.5, oy, oz+16)
    glScalef(2, 4, 4)
    glutSolidCube(1)
    glPopMatrix()

    glColor3f(0.50, 0.52, 0.55)
    glPushMatrix()
    glTranslatef(ox-5, oy-5.5, oz+12)
    glScalef(8, 0.5, 6)
    glutSolidCube(1)
    glPopMatrix()


def draw_oxygen_tanker(q, ox, oy, oz):
    glColor3f(0.26, 0.32, 0.36)
    glPushMatrix()
    glTranslatef(ox, oy, oz)
    gluCylinder(q, 8, 8, 38, 12, 1)
    glPopMatrix()

    glColor3f(0.20, 0.26, 0.30)
    glPushMatrix()
    glTranslatef(ox, oy, oz+38)
    gluCylinder(q, 8, 0, 10, 12, 1)
    glPopMatrix()

    glPushMatrix()
    glTranslatef(ox, oy, oz)
    manual_disk(0, 8, 12)
    glPopMatrix()

    glColor3f(0.50, 0.42, 0.28)
    glPushMatrix()
    glTranslatef(ox, oy, oz+46)
    gluSphere(q, 4, 8, 6)
    glPopMatrix()

    glColor3f(0.60, 0.58, 0.52)
    glPushMatrix()
    glTranslatef(ox+8.5, oy, oz+25)
    manual_disk(0, 4, 10)
    glPopMatrix()


def draw_gun_box(q, ox, oy, oz):
    glColor3f(0.22, 0.20, 0.17)
    glPushMatrix()
    glTranslatef(ox, oy, oz+10)
    glScalef(28, 10, 20)
    glutSolidCube(1)
    glPopMatrix()

    glColor3f(0.55, 0.45, 0.10)
    for sz2 in [oz+5, oz+15]:
        glPushMatrix()
        glTranslatef(ox, oy-5.5, sz2)
        glScalef(28, 0.5, 3)
        glutSolidCube(1)
        glPopMatrix()

    glColor3f(0.38, 0.32, 0.22)
    for clx in [ox-11, ox+11]:
        glPushMatrix()
        glTranslatef(clx, oy-5.5, oz+18)
        glScalef(4, 1, 4)
        glutSolidCube(1)
        glPopMatrix()

    glColor3f(0.16, 0.14, 0.12)
    glPushMatrix()
    glTranslatef(ox, oy-5.5, oz+12)
    glScalef(18, 0.6, 3)
    glutSolidCube(1)
    glPopMatrix()


def draw_light_box(q, ox, oy, oz):
    t2    = time.time() - start_time
    pulse = 0.7 + 0.25*math.sin(t2*2.8)

    glColor3f(0.28, 0.24, 0.18)
    glPushMatrix()
    glTranslatef(ox, oy, oz+9)
    glScalef(18, 8, 18)
    glutSolidCube(1)
    glPopMatrix()

    glColor3f(0.22, 0.18, 0.14)
    glPushMatrix()
    glTranslatef(ox, oy, oz+18)
    glScalef(10, 2, 4)
    glutSolidCube(1)
    glPopMatrix()

    glColor3f(0.90*pulse, 0.65*pulse, 0.20*pulse)
    for sl in [oz+6, oz+10, oz+14]:
        glPushMatrix()
        glTranslatef(ox, oy-4.5, sl)
        glScalef(12, 0.5, 1.5)
        glutSolidCube(1)
        glPopMatrix()


OBJ_DRAW = {
    'water_bottle':  draw_water_bottle,
    'first_aid':     draw_first_aid,
    'food_freezer':  draw_food_freezer,
    'oxygen_tanker': draw_oxygen_tanker,
    'gun_box':       draw_gun_box,
    'light_box':     draw_light_box,
}


def draw_breakable_wall(b, bidx):
    t2      = time.time() - start_time
    q       = gluNewQuadric()
    cx, cy  = b['cx'], b['cy']
    hw, hd  = b['w']/2, b['d']/2
    ds      = b['door_side']
    ot      = b['obj_type']
    if ot is None:
        return
    gr, gg, gb = OBJ_GLOW[ot]
    pulse      = 0.65 + 0.30*math.sin(t2*2.2)
    wall_h     = 80

    if ds == 'S':
        wx, wy, wlen, wax = cx,         cy+hd*0.35, b['w']-30, 'x'
    elif ds == 'N':
        wx, wy, wlen, wax = cx,         cy-hd*0.35, b['w']-30, 'x'
    elif ds == 'W':
        wx, wy, wlen, wax = cx+hw*0.35, cy,         b['d']-30, 'y'
    else:
        wx, wy, wlen, wax = cx-hw*0.35, cy,         b['d']-30, 'y'

    n         = max(2, int(wlen/30))
    any_alive = False

    for i in range(n):
        hits = wall_hits.get((bidx, i), 3)
        if hits <= 0:
            continue
        any_alive = True
        off   = -wlen/2 + (i+0.5)*(wlen/n)
        sw    = wlen/n - 3
        boost = 1.3 if i == n//2 else 1.0

        if hits == 3:
            cr, cg, cb = gr*0.55*pulse*boost, gg*0.55*pulse*boost, gb*0.55*pulse*boost
        elif hits == 2:
            cr, cg, cb = min(1, 0.85*pulse), min(1, 0.40*pulse), 0.05*pulse
        else:
            cr, cg, cb = min(1, 0.65*pulse), 0.08*pulse, 0.05*pulse

        glColor3f(min(1,cr), min(1,cg), min(1,cb))
        glPushMatrix()
        if wax == 'x':
            glTranslatef(wx+off, wy, wall_h/2)
            glScalef(sw, 14, wall_h)
        else:
            glTranslatef(wx, wy+off, wall_h/2)
            glScalef(14, sw, wall_h)
        glutSolidCube(1)
        glPopMatrix()

        glColor3f(0.08, 0.07, 0.06)
        glPushMatrix()
        if wax == 'x':
            glTranslatef(wx+off, wy, wall_h/2)
            draw_wire_cube_manual(sw+1, 15, wall_h+1)
        else:
            glTranslatef(wx, wy+off, wall_h/2)
            draw_wire_cube_manual(15, sw+1, wall_h+1)
        glPopMatrix()

    if any_alive:
        glColor3f(gr*0.28*pulse, gg*0.28*pulse, gb*0.28*pulse)
        glPushMatrix()
        glTranslatef(wx, wy, wall_h/2)
        if wax == 'x':
            draw_wire_cube_manual(wlen+12, 22, wall_h+16)
        else:
            draw_wire_cube_manual(22, wlen+12, wall_h+16)
        glPopMatrix()

    if bidx not in collected:
        if ds == 'S':
            ox_off, oy_off =  0,  12
        elif ds == 'N':
            ox_off, oy_off =  0, -12
        elif ds == 'W':
            ox_off, oy_off = -12,  0
        else:
            ox_off, oy_off =  12,  0
        OBJ_DRAW[ot](q, wx+ox_off, wy+oy_off, wall_h*0.30)


SLAB_C = [
    (0.22, 0.20, 0.18),
    (0.28, 0.25, 0.22),
    (0.32, 0.29, 0.25),
    (0.26, 0.23, 0.20),
]


def _wall_slabs(axis, fixed, v0, v1, wh, skip=False, gap=55, seed=0):
    seg   = 38
    total = v1 - v0
    n     = max(2, int(total/seg))
    random.seed(seed)
    for i in range(n):
        vc = v0 + (i+0.5)*(total/n)
        if skip and abs(vc - (v0+v1)/2) < gap/2:
            continue
        sh = wh * random.uniform(0.40, 1.0)
        glColor3f(*SLAB_C[i%4])
        glPushMatrix()
        if axis == 'x':
            glTranslatef(vc, fixed, sh/2)
            glScalef(total/n-2, 16, sh)
        else:
            glTranslatef(fixed, vc, sh/2)
            glScalef(16, total/n-2, sh)
        glutSolidCube(1)
        glPopMatrix()

        glColor3f(0.10, 0.09, 0.08)
        glPushMatrix()
        if axis == 'x':
            glTranslatef(vc, fixed, sh/2)
            draw_wire_cube_manual(total/n-1, 17, sh+1)
        else:
            glTranslatef(fixed, vc, sh/2)
            draw_wire_cube_manual(17, total/n-1, sh+1)
        glPopMatrix()


def draw_building(b, bidx):
    cx, cy  = b['cx'], b['cy']
    hw, hd  = b['w']/2, b['d']/2
    h       = b['h']
    ds      = b['door_side']
    q       = gluNewQuadric()
    x0, x1  = cx-hw, cx+hw
    y0, y1  = cy-hd, cy+hd

    _wall_slabs('x', y1, x0, x1, h, skip=(ds=='N'), seed=int(cx+cy+1))
    _wall_slabs('x', y0, x0, x1, h, skip=(ds=='S'), seed=int(cx+cy+2))
    _wall_slabs('y', x1, y0, y1, h, skip=(ds=='E'), seed=int(cx+cy+3))
    _wall_slabs('y', x0, y0, y1, h, skip=(ds=='W'), seed=int(cx+cy+4))

    glColor3f(0.16, 0.14, 0.12)
    glBegin(GL_QUADS)
    glVertex3f(x0+16, y0+16, 0.2)
    glVertex3f(x1-16, y0+16, 0.2)
    glVertex3f(x1-16, y1-16, 0.2)
    glVertex3f(x0+16, y1-16, 0.2)
    glEnd()

    random.seed(int(cx*3+cy))
    for _ in range(7):
        rx = cx + random.uniform(-hw*0.65, hw*0.65)
        ry = cy + random.uniform(-hd*0.65, hd*0.65)
        rs = random.uniform(9, 25)
        rz = random.uniform(rs/2, h*0.50)
        glColor3f(0.24, 0.22, 0.19)
        glPushMatrix()
        glTranslatef(rx, ry, rz)
        glRotatef(random.uniform(0, 45), 0.3, 0.6, 1.0)
        glScalef(rs, rs*0.7, rs*0.5)
        glutSolidCube(1)
        glPopMatrix()

    rope_h = 60
    if ds == 'N':
        rx0, ry0, rx1, ry1 = cx-28, y1, cx+28, y1
    elif ds == 'S':
        rx0, ry0, rx1, ry1 = cx-28, y0, cx+28, y0
    elif ds == 'E':
        rx0, ry0, rx1, ry1 = x1, cy-28, x1, cy+28
    else:
        rx0, ry0, rx1, ry1 = x0, cy-28, x0, cy+28

    pc = (0.28, 0.20, 0.09) if not rope_cut[bidx] else (0.20, 0.15, 0.07)
    glColor3f(*pc)
    for rpx, rpy in [(rx0, ry0), (rx1, ry1)]:
        glPushMatrix()
        glTranslatef(rpx, rpy, 0)
        gluCylinder(q, 4, 3, rope_h, 7, 1)
        glPopMatrix()

        glPushMatrix()
        glTranslatef(rpx, rpy, rope_h)
        # glutSolidSphere -> gluSphere
        gluSphere(q, 5.5, 6, 6)
        glPopMatrix()

    if rope_cut[bidx]:
        glColor3f(0.22, 0.16, 0.06)
        mid_x = (rx0+rx1)/2
        mid_y = (ry0+ry1)/2
        for segs, p0x, p0y, p1x, p1y in [
            (5, rx0, ry0, mid_x, mid_y),
            (5, mid_x, mid_y, rx1, ry1)
        ]:
            for i in range(segs):
                t0 = i/segs
                t1 = (i+1)/segs
                z0 = max(2, rope_h*0.7*t0 - 20*math.sin(t0*math.pi) - 15*(1-t0))
                z1 = max(2, rope_h*0.7*t1 - 20*math.sin(t1*math.pi) - 15*(1-t1))
                glBegin(GL_LINES)
                glVertex3f(p0x + t0*(p1x-p0x), p0y + t0*(p1y-p0y), z0)
                glVertex3f(p0x + t1*(p1x-p0x), p0y + t1*(p1y-p0y), z1)
                glEnd()
    else:
        glColor3f(0.38, 0.28, 0.10)
        for i in range(8):
            t0  = i/8
            t1  = (i+1)/8
            sag = 14
            z0  = rope_h*0.7 - sag*math.sin(t0*math.pi)
            z1  = rope_h*0.7 - sag*math.sin(t1*math.pi)
            glBegin(GL_LINES)
            glVertex3f(rx0 + t0*(rx1-rx0), ry0 + t0*(ry1-ry0), z0)
            glVertex3f(rx0 + t1*(rx1-rx0), ry0 + t1*(ry1-ry0), z1)
            glEnd()

    if b['has_obj']:
        draw_breakable_wall(b, bidx)


def draw_all_buildings():
    for i, b in enumerate(BUILDINGS):
        draw_building(b, i)


def setup_camera():
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(fovY, WIN_W/WIN_H, 1.0, 5000.0)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    if first_person:
        rad = math.radians(p_ang)
        dx2 = math.sin(rad)
        dy2 = math.cos(rad)
        gluLookAt(px, py, pz+72, px+dx2*200, py+dy2*200, pz+72, 0, 0, 1)
    else:
        rh = math.radians(cam_h)
        rv = math.radians(cam_v)
        ex = px + cam_r*math.cos(rv)*math.sin(rh)
        ey = py - cam_r*math.cos(rv)*math.cos(rh)
        ez = pz + cam_r*math.sin(rv)
        gluLookAt(ex, ey, ez, px, py, pz+30, 0, 0, 1)


def draw_kit_spheres_hud():
    kit_indices = [i for i, b in enumerate(BUILDINGS) if b['has_obj']]
    cx_start    = WIN_W//2 - (TOTAL_KITS-1)*38
    cy_pos      = WIN_H - 80
    radius      = 16
    set_ortho_2d()
    for k_idx, bidx in enumerate(kit_indices):
        cx         = cx_start + k_idx*76
        b          = BUILDINGS[bidx]
        ot         = b['obj_type']
        gr, gg, gb = OBJ_GLOW[ot]

        if bidx in collected:
            glColor3f(gr, gg, gb)
        else:
            glColor3f(gr*0.25, gg*0.25, gb*0.25)
        for seg in range(32):
            a0 = 2.0*math.pi*seg/32
            a1 = 2.0*math.pi*(seg+1)/32
            glBegin(GL_QUADS)
            glVertex2f(cx, cy_pos)
            glVertex2f(cx + radius*math.cos(a0), cy_pos + radius*math.sin(a0))
            glVertex2f(cx + radius*math.cos(a1), cy_pos + radius*math.sin(a1))
            glVertex2f(cx, cy_pos)
            glEnd()

        if bidx in collected:
            glColor3f(1.0, 1.0, 1.0)
        else:
            glColor3f(gr*0.6, gg*0.6, gb*0.6)
        for seg in range(32):
            a0 = 2.0*math.pi*seg/32
            a1 = 2.0*math.pi*(seg+1)/32
            glBegin(GL_LINES)
            glVertex2f(cx + radius*math.cos(a0), cy_pos + radius*math.sin(a0))
            glVertex2f(cx + radius*math.cos(a1), cy_pos + radius*math.sin(a1))
            glEnd()

    restore_3d()
    draw_text_colored(WIN_W//2-38, WIN_H-52, f"KITS: {len(collected)}/{TOTAL_KITS}", 0.80, 0.70, 0.30)


def draw_heart_hud():
    set_ortho_2d()
    heart_size = 18
    spacing    = 48
    start_x    = 24
    base_y     = WIN_H - 44

    for i in range(10):
        cx    = start_x + i*spacing
        cy    = base_y
        alive = (i < player_hearts)
        hr, hg, hb = (0.88, 0.12, 0.12) if alive else (0.22, 0.06, 0.06)
        s = heart_size
        glColor3f(hr, hg, hb)

        for seg in range(16):
            a0 = math.pi + seg*math.pi/15
            a1 = math.pi + (seg+1)*math.pi/15
            glBegin(GL_QUADS)
            glVertex2f(cx-s*0.25, cy+s*0.25)
            glVertex2f(cx-s*0.25 + s*0.25*math.cos(a0), cy+s*0.25 + s*0.28*math.sin(a0))
            glVertex2f(cx-s*0.25 + s*0.25*math.cos(a1), cy+s*0.25 + s*0.28*math.sin(a1))
            glVertex2f(cx-s*0.25, cy+s*0.25)
            glEnd()

        for seg in range(16):
            a0 = math.pi + seg*math.pi/15
            a1 = math.pi + (seg+1)*math.pi/15
            glBegin(GL_QUADS)
            glVertex2f(cx+s*0.25, cy+s*0.25)
            glVertex2f(cx+s*0.25 + s*0.25*math.cos(a0), cy+s*0.25 + s*0.28*math.sin(a0))
            glVertex2f(cx+s*0.25 + s*0.25*math.cos(a1), cy+s*0.25 + s*0.28*math.sin(a1))
            glVertex2f(cx+s*0.25, cy+s*0.25)
            glEnd()

        glBegin(GL_QUADS)
        glVertex2f(cx-s*0.50, cy+s*0.25)
        glVertex2f(cx,         cy+s*0.25)
        glVertex2f(cx,         cy-s*0.55)
        glVertex2f(cx-s*0.10,  cy-s*0.10)
        glEnd()

        glBegin(GL_QUADS)
        glVertex2f(cx,        cy+s*0.25)
        glVertex2f(cx+s*0.50, cy+s*0.25)
        glVertex2f(cx+s*0.10, cy-s*0.10)
        glVertex2f(cx,        cy-s*0.55)
        glEnd()

    restore_3d()
    draw_text_colored(24, WIN_H-62, "HP", 0.80, 0.70, 0.45)


def draw_score_hud():
    bx = WIN_W - 220
    by = WIN_H - 52
    bw = 200
    bh = 38
    draw_rect_2d(bx, by, bw, bh, 0.08, 0.08, 0.08)
    draw_line_2d(bx,    by,    bx+bw, by,    0.40, 0.80, 0.40)
    draw_line_2d(bx,    by+bh, bx+bw, by+bh, 0.40, 0.80, 0.40)
    draw_text_colored(bx+12, by+12, f"SCORE: {score}", 0.30, 1.00, 0.30, font=GLUT_BITMAP_HELVETICA_18)
    kit_portion = len(collected) * SCORE_KIT
    kills       = (score-kit_portion) // SCORE_ENEMY if SCORE_ENEMY else 0
    draw_text_colored(bx+12, WIN_H-78, f"Kits:{len(collected)}x{SCORE_KIT}  Kills:{kills}x{SCORE_ENEMY}", 0.50, 0.75, 0.50)


def draw_damage_label():
    if dmg_label_t <= 0:
        return
    alpha = min(1.0, dmg_label_t)
    if dmg_flash_type == "rock":
        label = "! ROCK DAMAGE !"
        r, g, b = 1.0, 0.55, 0.10
    elif dmg_flash_type == "rope":
        label = "! ROPE DAMAGE !"
        r, g, b = 1.0, 0.80, 0.10
    elif dmg_flash_type == "enemy":
        label = "! MUTANT ATTACK !"
        r, g, b = 1.0, 0.15, 0.15
    elif dmg_flash_type == "ammo":
        label = "+5 AMMO!"
        r, g, b = 0.30, 0.90, 0.30
    else:
        return
    draw_text_colored(WIN_W//2-130, WIN_H//2-30, label, r*alpha, g*alpha, b*alpha, font=GLUT_BITMAP_HELVETICA_18)


def draw_enemy_hud():
    alive = len([e for e in enemies if not e.get('dead', False)])
    draw_text_colored(WIN_W-220, WIN_H-100, f"Mutants: {alive}/{MAX_ENEMIES}", 0.70, 0.30, 0.10)
    if enemy_spawn_cd > 0 and alive < MAX_ENEMIES and game_state == "PLAY":
        draw_text_colored(WIN_W-220, WIN_H-122, f"Next spawn: {max(0,int(enemy_spawn_cd))}s", 0.55, 0.25, 0.08)


def draw_hud():
    if game_state == "INTRO":
        return
    t2   = time.time() - start_time
    mins = int(t2) // 60
    secs = int(t2) % 60

    draw_heart_hud()
    draw_kit_spheres_hud()
    draw_score_hud()
    draw_enemy_hud()

    draw_text_colored(WIN_W//2-50, WIN_H-105, f"Time: {mins:02d}:{secs:02d}", 0.65, 0.55, 0.35)
    draw_text_colored(WIN_W//2-70, 38,        f"Tool: {TOOL_NAMES[current_tool]}", 0.80, 0.70, 0.45)
    draw_text_colored(WIN_W-200,   66,        f"Ammo: {ammo}", 0.80, 0.70, 0.45)

    mc_r = 0.80 if miss_count < 8 else 1.0
    mc_g = 0.70 if miss_count < 8 else (0.30 if miss_count < 10 else 0.10)
    mc_b = 0.45 if miss_count < 8 else 0.10
    draw_text_colored(WIN_W-200, 38, f"Miss: {miss_count}/10", mc_r, mc_g, mc_b)

    bar_w = WIN_W - 40
    bar_h = 20
    bx2   = 20
    by2   = 90
    draw_rect_2d(bx2, by2, bar_w, bar_h, 0.15, 0.15, 0.15)
    fill = int(bar_w * pollution)
    if pollution < 0.4:
        pr, pg, pb = 0.20, 0.80, 0.20
    elif pollution < 0.7:
        pr, pg, pb = 0.90, 0.65, 0.08
    else:
        pr, pg, pb = 0.90, 0.10, 0.10
    if fill > 0:
        draw_rect_2d(bx2, by2, fill, bar_h, pr, pg, pb)

    draw_line_2d(bx2,       by2,       bx2+bar_w, by2,       0.50, 0.50, 0.50)
    draw_line_2d(bx2+bar_w, by2,       bx2+bar_w, by2+bar_h, 0.50, 0.50, 0.50)
    draw_line_2d(bx2+bar_w, by2+bar_h, bx2,       by2+bar_h, 0.50, 0.50, 0.50)
    draw_line_2d(bx2,       by2+bar_h, bx2,       by2,       0.50, 0.50, 0.50)

    in_safe = inside_bunker_area(px, py)
    label   = f"AIR POLLUTION: {int(pollution*100)}%  {'[SAFE]' if in_safe else '[OUTSIDE - polluting!]'}"
    draw_text_colored(bx2, by2+bar_h+5, label, 0.80, 0.70, 0.45)

    draw_damage_label()

    if first_person:
        set_ortho_2d()
        cx3 = WIN_W // 2
        cy3 = WIN_H // 2
        sz  = 14
        gap = 3
        glColor3f(0.95, 0.90, 0.30)
        glBegin(GL_LINES)
        glVertex2f(cx3-sz, cy3)
        glVertex2f(cx3-gap, cy3)
        glVertex2f(cx3+gap, cy3)
        glVertex2f(cx3+sz, cy3)
        glVertex2f(cx3, cy3-sz)
        glVertex2f(cx3, cy3-gap)
        glVertex2f(cx3, cy3+gap)
        glVertex2f(cx3, cy3+sz)
        glEnd()
        restore_3d()

    if len(collected) >= TOTAL_KITS and game_state == "PLAY":
        draw_text_colored(WIN_W//2-200, WIN_H//2, "All kits collected!  Return to BUNKER to WIN!", 0.20, 1.00, 0.30)

    ri = player_in_rope_zone()
    if ri >= 0 and not inside_bunker_area(px, py):
        draw_text_colored(WIN_W//2-180, WIN_H//2-60, "WARNING: Rope nearby! Press 2+E to cut rope", 1.0, 0.30, 0.10)


def draw_intro():
    t2    = time.time() - start_time
    pulse = 0.7 + 0.3*math.sin(t2*2.0)
    draw_rect_2d(0, 0, WIN_W, WIN_H, 0.0, 0.0, 0.0)
    draw_text_large(WIN_W//2-220,  WIN_H//2+160, "INTO THE RUINS: LAST BREATH",        0.85*pulse, 0.20*pulse, 0.10*pulse)
    draw_text_colored(WIN_W//2-150, WIN_H//2+110, '"Can you escape the ruins?"',        0.65*pulse, 0.55*pulse, 0.35*pulse)
    draw_text_large(WIN_W//2-170,  WIN_H//2+50,  "2000 DAYS AFTER EXPLOSION",           0.70, 0.65, 0.50)
    draw_line_2d(WIN_W//2-280, WIN_H//2+30, WIN_W//2+280, WIN_H//2+30, 0.40, 0.35, 0.25)
    draw_text_colored(WIN_W//2-230, WIN_H//2-10,  "Collect 6 Survival Kits before the air kills you.", 0.55, 0.50, 0.40)
    draw_text_colored(WIN_W//2-200, WIN_H//2-40,  "Return to the Bunker with all kits to WIN.",        0.55, 0.50, 0.40)
    draw_text_colored(WIN_W//2-200, WIN_H//2-70,  "Avoid mutant enemies — shoot them with GUN (3).",   0.55, 0.50, 0.40)
    draw_text_colored(WIN_W//2-160, WIN_H//2-100, "Controls:  WASD=Move   A/D=Rotate",                 0.55, 0.50, 0.40)
    draw_text_colored(WIN_W//2-160, WIN_H//2-125, "Space=Jump   E=Interact   1/2/3=Tool",               0.55, 0.50, 0.40)
    draw_text_colored(WIN_W//2-160, WIN_H//2-150, "LMB=Fire Gun   RMB / F=Camera Toggle",               0.55, 0.50, 0.40)
    draw_text_colored(WIN_W//2-160, WIN_H//2-175, "Arrow Keys=Orbit Camera   +/-=Zoom",                 0.55, 0.50, 0.40)
    draw_text_large(WIN_W//2-130,   WIN_H//2-215, "Press ENTER to Start",               0.80*pulse, 0.70*pulse, 0.20*pulse)


def draw_win_screen():
    draw_dark_overlay(0.0, 0.04, 0.0)
    t2    = time.time() - start_time
    pulse = 0.7 + 0.3*math.sin(t2*3)
    draw_text_large(WIN_W//2-200,   WIN_H//2+80,  "YOU WIN!  SURVIVED!",                0.20*pulse, 0.90*pulse, 0.25*pulse)
    draw_text_large(WIN_W//2-160,   WIN_H//2+40,  "ESCAPED THE RUINS!",                 0.25*pulse, 0.85*pulse, 0.20*pulse)
    draw_text_colored(WIN_W//2-160, WIN_H//2-10,  "The air is clean inside the bunker.", 0.75, 0.65, 0.45)
    draw_text_colored(WIN_W//2-80,  WIN_H//2-50,  f"Final Score: {score}",               0.80, 0.75, 0.30)
    draw_text_colored(WIN_W//2-90,  WIN_H//2-90,  "Press R to play again",               0.75, 0.65, 0.45)


def draw_gameover_screen(reason):
    draw_dark_overlay(0.04, 0.0, 0.0)
    t2    = time.time() - start_time
    pulse = 0.7 + 0.3*math.sin(t2*2.5)
    draw_text_large(WIN_W//2-120,   WIN_H//2+80,  "GAME  OVER",           0.90*pulse, 0.12*pulse, 0.10*pulse)
    draw_text_colored(WIN_W//2-160, WIN_H//2+20,  reason,                 0.75, 0.55, 0.35)
    draw_text_colored(WIN_W//2-90,  WIN_H//2-30,  f"Score: {score}",      0.70, 0.60, 0.40)
    draw_text_colored(WIN_W//2-80,  WIN_H//2-70,  "Press R to try again", 0.70, 0.60, 0.40)


def get_sky_color():
    r = 0.06 - pollution*0.04
    g = 0.055 + pollution*0.08
    b = 0.05  - pollution*0.04
    if flash_timer > 0:
        r = max(r, 0.50)
        g = max(g, 0.30)
        b = max(b, 0.08)
    return max(0, r), max(0, g), max(0, b)


def keyboardListener(key, x, y):
    global current_tool, is_jumping, jump_vel, first_person
    global game_state, gameover_reason, cam_r
    global key_w, key_s, key_a, key_d

    if key in (b'w', b'W'): key_w = True
    if key in (b's', b'S'): key_s = True
    if key in (b'a', b'A'): key_a = True
    if key in (b'd', b'D'): key_d = True

    if key == b'\r' and game_state == "INTRO":
        reset_game()
        return
    if key in (b'r', b'R') and game_state in ("WIN", "OVER"):
        reset_game()
        return
    if game_state != "PLAY":
        return

    if key == b'1': current_tool = 0
    if key == b'2': current_tool = 1
    if key == b'3': current_tool = 2
    if key == b' ' and not is_jumping and pz == 0:
        is_jumping = True
        jump_vel   = JUMP_INIT
    if key in (b'e', b'E'): interact()
    if key in (b'f', b'F'): first_person = not first_person
    if key in (b'+', b'='): cam_r = max(CAM_R_MIN, cam_r-30)
    if key in (b'-', b'_'): cam_r = min(CAM_R_MAX, cam_r+30)


def specialKeyListener(key, x, y):
    global cam_h, cam_v
    if key == GLUT_KEY_LEFT:  cam_h -= 4
    if key == GLUT_KEY_RIGHT: cam_h += 4
    if key == GLUT_KEY_UP:    cam_v  = min(85, cam_v+3)
    if key == GLUT_KEY_DOWN:  cam_v  = max(8,  cam_v-3)


def mouseListener(button, state, x, y):
    global first_person
    if button == GLUT_RIGHT_BUTTON and state == GLUT_DOWN:
        first_person = not first_person
    if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN and game_state == "PLAY":
        fire_bullet()


def process_movement(dt):
    global px, py, pz, p_ang, is_jumping, jump_vel, flash_timer, shoot_cd
    global player_hearts, invincible_t, rope_dmg_t, rock_dmg_t
    global pollution, game_state, gameover_reason, gameover_t
    global dmg_flash_type, dmg_label_t
    global key_w, key_s, key_a, key_d

    if game_state != "PLAY":
        return

    if is_jumping or pz > 0:
        pz       += jump_vel * dt
        jump_vel -= GRAVITY * dt
        if pz <= 0:
            pz         = 0
            jump_vel   = 0
            is_jumping = False

    if key_a: p_ang = (p_ang - P_ROT) % 360
    if key_d: p_ang = (p_ang + P_ROT) % 360

    rad   = math.radians(p_ang)
    dx2   = math.sin(rad)
    dy2   = math.cos(rad)
    moved = False
    move  = P_SPEED * dt * 60

    if key_w:
        nx = px + dx2*move
        ny = py + dy2*move
        if check_collision(nx, ny):
            if check_rock_collision(nx, ny):
                if rock_dmg_t <= 0 and invincible_t <= 0:
                    player_hearts -= 1
                    invincible_t   = 1.2
                    rock_dmg_t     = 0.5
                    flash_timer    = 0.15
                    dmg_flash_type = "rock"
                    dmg_label_t    = 2.0
            else:
                px, py = nx, ny
                moved  = True

    if key_s:
        nx = px - dx2*move
        ny = py - dy2*move
        if check_collision(nx, ny):
            if check_rock_collision(nx, ny):
                if rock_dmg_t <= 0 and invincible_t <= 0:
                    player_hearts -= 1
                    invincible_t   = 1.2
                    rock_dmg_t     = 0.5
                    flash_timer    = 0.15
                    dmg_flash_type = "rock"
                    dmg_label_t    = 2.0
            else:
                px, py = nx, ny
                moved  = True

    key_w = False
    key_s = False
    key_a = False
    key_d = False

    if rock_dmg_t  > 0: rock_dmg_t  -= dt
    if dmg_label_t > 0: dmg_label_t -= dt

    in_safe = inside_bunker_area(px, py)
    if not in_safe:
        pollution += dt / POLLUTION_MAX_TIME
        if moved:
            pollution += POLL_MOVE_DRAIN
        pollution = min(1.0, pollution)

    if not in_safe:
        ri = player_in_rope_zone()
        if ri >= 0:
            rope_dmg_t += dt
            if rope_dmg_t >= 1.0:
                rope_dmg_t = 0.0
                if invincible_t <= 0:
                    player_hearts -= 1
                    invincible_t   = 0.8
                    flash_timer    = 0.20
                    dmg_flash_type = "rope"
                    dmg_label_t    = 2.0
        else:
            rope_dmg_t = 0.0
    else:
        rope_dmg_t = 0.0

    if invincible_t > 0: invincible_t -= dt
    if shoot_cd    > 0: shoot_cd     -= dt
    if flash_timer > 0: flash_timer  -= dt

    if pollution >= 1.0:
        game_state      = "OVER"
        gameover_reason = "The toxic air claimed your last breath."
        gameover_t      = 0.0
        return
    if player_hearts <= 0:
        game_state      = "OVER"
        gameover_reason = "Killed by the ruins — no hearts left."
        gameover_t      = 0.0
        return
    check_win()


def idle():
    global last_frame, win_bounce_t, gameover_t, pz, jump_vel, is_jumping
    now        = time.time()
    dt         = min(now - last_frame, 0.05)
    last_frame = now
    process_movement(dt)
    update_bullets(dt)
    update_enemies(dt)
    if game_state == "WIN":
        win_bounce_t += dt
        pz = max(0, 50*abs(math.sin(win_bounce_t*math.pi*1.8)))
    if game_state == "OVER":
        gameover_t += dt
    glutPostRedisplay()


def showScreen():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    if game_state == "INTRO":
        draw_background_color(0.0, 0.0, 0.0)
        glEnable(GL_DEPTH_TEST)
        glLoadIdentity()
        glViewport(0, 0, WIN_W, WIN_H)
        draw_intro()
        glutSwapBuffers()
        return

    r2, g2, b2 = get_sky_color()
    draw_background_color(r2, g2, b2)

    glEnable(GL_DEPTH_TEST)
    glLoadIdentity()
    glViewport(0, 0, WIN_W, WIN_H)

    setup_camera()
    draw_floor()
    draw_outside_debris()
    draw_dead_trees()
    draw_boundary_walls()
    draw_bunker_walls()
    draw_bunker_props()
    draw_rock_clusters()
    draw_all_buildings()
    draw_enemies()
    draw_player()
    if game_state == "PLAY":
        draw_bullets_3d()
    draw_hud()
    if game_state == "WIN":
        draw_win_screen()
    elif game_state == "OVER":
        draw_gameover_screen(gameover_reason)
    glutSwapBuffers()


def main():
    global game_state
    game_state = "INTRO"
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(WIN_W, WIN_H)
    glutInitWindowPosition(90,90)
    glutCreateWindow(b"Into the Ruins: Last Breath")
    glutDisplayFunc(showScreen)
    glutKeyboardFunc(keyboardListener)
    glutSpecialFunc(specialKeyListener)
    glutMouseFunc(mouseListener)
    glutIdleFunc(idle)
    glutMainLoop()


if __name__ == "__main__":
    main()