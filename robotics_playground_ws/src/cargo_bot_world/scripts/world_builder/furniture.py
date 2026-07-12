from .sdf_helpers import solid_link
from .constants import C_OUTER

# ─── Shelf dimensions ─────────────────────────────────────────────────────────
SHELF_W  = 1.50
SHELF_D  = 0.60
SHELF_H  = 2.70
SIDE_T   = 0.06
BOARD_T  = 0.06
N_LEVELS = 3
BOX_S    = 0.39
BOX_GAP  = 0.045

# ─── Desk dimensions ──────────────────────────────────────────────────────────
DESK_W   = 2.10
DESK_D   = 1.05
DESK_H   = 1.10
DESK_TOP = 0.09
LEG_S    = 0.09

# ─── Chair dimensions ─────────────────────────────────────────────────────────
SEAT_H   = 0.68
SEAT_W   = 0.63
BACK_H   = 0.75
CHAIR_T  = 0.06
CHAIR_LEG = 0.06

# ─── Plant dimensions ─────────────────────────────────────────────────────────
POT_W    = 0.33
POT_H    = 0.45
LEAF_W   = 0.69
LEAF_H   = 0.66

# ─── Colors ───────────────────────────────────────────────────────────────────
C_SHELF = (0.55, 0.52, 0.48)
C_BOX   = (0.80, 0.65, 0.38)
C_DESK  = (0.68, 0.54, 0.36)
C_CHAIR = (0.58, 0.44, 0.28)
C_POT   = (0.72, 0.35, 0.20)
C_PLANT = (0.22, 0.55, 0.18)


def _box_row(center, count):
    step = BOX_S + BOX_GAP
    start = center - (count - 1) * step / 2
    return [start + i * step for i in range(count)]


# ─── Shelf ────────────────────────────────────────────────────────────────────

def shelf_y(name, cy, x_wall, sign, n_boxes=3, c_shelf=C_SHELF, c_box=C_BOX):
    """Shelf width along Y, against a Y-axis wall.
    sign: +1 west wall, -1 east wall."""
    cx   = x_wall + sign * SHELF_D / 2
    bx   = x_wall + sign * SIDE_T / 2
    step = (SHELF_H - BOARD_T) / (N_LEVELS + 1)
    links = []
    links.append(solid_link(f'{name}_back', (bx, cy, SHELF_H / 2), (SIDE_T, SHELF_W, SHELF_H), c_shelf))
    for sfx, dy in (('l', -(SHELF_W / 2 - SIDE_T / 2)), ('r', SHELF_W / 2 - SIDE_T / 2)):
        links.append(solid_link(f'{name}_s{sfx}', (cx, cy + dy, SHELF_H / 2), (SHELF_D - SIDE_T, SIDE_T, SHELF_H), c_shelf))
    board_zs = [i * step for i in range(N_LEVELS + 1)] + [SHELF_H - BOARD_T]
    for i, bz in enumerate(board_zs):
        links.append(solid_link(f'{name}_brd{i}', (cx, cy, bz + BOARD_T / 2), (SHELF_D - SIDE_T, SHELF_W - 2 * SIDE_T, BOARD_T), c_shelf))
    box_cx = bx + sign * (SIDE_T / 2 + BOX_S / 2)
    for level in range(1, N_LEVELS + 1):
        bz = board_zs[level] + BOARD_T + BOX_S / 2
        for j, by in enumerate(_box_row(cy, n_boxes)):
            links.append(solid_link(f'{name}_bx{level}{j}', (box_cx, by, bz), (BOX_S, BOX_S, BOX_S), c_box))
    return links


def shelf_x(name, cx, y_wall, sign, n_boxes=3, c_shelf=C_SHELF, c_box=C_BOX):
    """Shelf width along X, against an X-axis wall.
    sign: +1 south wall, -1 north wall."""
    cy  = y_wall + sign * SHELF_D / 2
    by_ = y_wall + sign * SIDE_T / 2
    step = (SHELF_H - BOARD_T) / (N_LEVELS + 1)
    links = []
    links.append(solid_link(f'{name}_back', (cx, by_, SHELF_H / 2), (SHELF_W, SIDE_T, SHELF_H), c_shelf))
    for sfx, dx in (('l', -(SHELF_W / 2 - SIDE_T / 2)), ('r', SHELF_W / 2 - SIDE_T / 2)):
        links.append(solid_link(f'{name}_s{sfx}', (cx + dx, cy, SHELF_H / 2), (SIDE_T, SHELF_D - SIDE_T, SHELF_H), c_shelf))
    board_zs = [i * step for i in range(N_LEVELS + 1)] + [SHELF_H - BOARD_T]
    for i, bz in enumerate(board_zs):
        links.append(solid_link(f'{name}_brd{i}', (cx, cy, bz + BOARD_T / 2), (SHELF_W - 2 * SIDE_T, SHELF_D - SIDE_T, BOARD_T), c_shelf))
    box_cy = by_ + sign * (SIDE_T / 2 + BOX_S / 2)
    for level in range(1, N_LEVELS + 1):
        bz = board_zs[level] + BOARD_T + BOX_S / 2
        for j, bx in enumerate(_box_row(cx, n_boxes)):
            links.append(solid_link(f'{name}_bx{level}{j}', (bx, box_cy, bz), (BOX_S, BOX_S, BOX_S), c_box))
    return links


# ─── Desk ─────────────────────────────────────────────────────────────────────

def desk(name, cx, cy, facing='x', c_desk=C_DESK):
    """Desk with 4 legs and table top. facing: 'x' width along X, 'y' along Y."""
    dw, dd = (DESK_W, DESK_D) if facing == 'x' else (DESK_D, DESK_W)
    leg_h  = DESK_H - DESK_TOP
    links  = []
    links.append(solid_link(f'{name}_top', (cx, cy, DESK_H - DESK_TOP / 2), (dw, dd, DESK_TOP), c_desk))
    for i, (sx, sy) in enumerate([(-1, -1), (-1, 1), (1, -1), (1, 1)]):
        lx = cx + sx * (dw / 2 - LEG_S / 2 - 0.04)
        ly = cy + sy * (dd / 2 - LEG_S / 2 - 0.04)
        links.append(solid_link(f'{name}_leg{i}', (lx, ly, leg_h / 2), (LEG_S, LEG_S, leg_h), c_desk))
    return links


# ─── Chair ────────────────────────────────────────────────────────────────────

def chair(name, cx, cy, back_dir='+y', c_chair=C_CHAIR):
    """Simple chair. back_dir: which side the backrest is on ('+x','-x','+y','-y')."""
    _dirs = {'+x': (1, 0), '-x': (-1, 0), '+y': (0, 1), '-y': (0, -1)}
    dx, dy = _dirs[back_dir]
    off    = SEAT_W / 2 - CHAIR_T / 2
    leg_h  = SEAT_H - CHAIR_T

    links = []
    # seat
    links.append(solid_link(f'{name}_seat', (cx, cy, SEAT_H - CHAIR_T / 2), (SEAT_W, SEAT_W, CHAIR_T), c_chair))
    # backrest
    bx = cx + dx * off
    by = cy + dy * off
    bsz = (CHAIR_T, SEAT_W, BACK_H) if dx != 0 else (SEAT_W, CHAIR_T, BACK_H)
    links.append(solid_link(f'{name}_bk', (bx, by, SEAT_H + BACK_H / 2), bsz, c_chair))
    # 4 legs
    lo = SEAT_W / 2 - CHAIR_LEG / 2 - 0.02
    for i, (sx, sy) in enumerate([(-1, -1), (-1, 1), (1, -1), (1, 1)]):
        links.append(solid_link(f'{name}_leg{i}', (cx + sx * lo, cy + sy * lo, leg_h / 2), (CHAIR_LEG, CHAIR_LEG, leg_h), c_chair))
    return links


# ─── Plant ────────────────────────────────────────────────────────────────────

def plant(name, cx, cy, c_pot=C_POT, c_plant=C_PLANT):
    """Decorative potted plant."""
    links = []
    links.append(solid_link(f'{name}_pot',    (cx, cy, POT_H / 2),            (POT_W,  POT_W,  POT_H),  c_pot))
    links.append(solid_link(f'{name}_leaves', (cx, cy, POT_H + LEAF_H / 2),   (LEAF_W, LEAF_W, LEAF_H), c_plant))
    return links


# ─── Floor box ────────────────────────────────────────────────────────────────

def floor_box(name, cx, cy, size=0.40, c=C_BOX):
    """Standalone cardboard box sitting on the floor."""
    return [solid_link(name, (cx, cy, size / 2), (size, size, size), c)]


# ─── Furniture dimensions ─────────────────────────────────────────────────────
SHELF_W  = 1.00   # shelf unit width (along wall face)
SHELF_D  = 0.40   # shelf unit depth (into room)
SHELF_H  = 1.80   # shelf unit height
SIDE_T   = 0.04   # side/back panel thickness
BOARD_T  = 0.04   # shelf board thickness
N_LEVELS = 3      # usable shelf levels
BOX_S    = 0.26   # cardboard box side length
BOX_GAP  = 0.03   # gap between boxes on a level

DESK_W   = 1.40   # desk width
DESK_D   = 0.70   # desk depth
DESK_H   = 0.75   # desk surface height
DESK_TOP = 0.06   # desk top slab thickness
LEG_S    = 0.06   # leg cross-section

# ─── Colors ───────────────────────────────────────────────────────────────────
C_SHELF = (0.55, 0.52, 0.48)   # metal shelf frame (dark grey)
C_BOX   = (0.80, 0.65, 0.38)   # cardboard box (warm tan)
C_DESK  = (0.68, 0.54, 0.36)   # wooden desk (warm brown)


def _box_row(center, count):
    """Return `count` evenly-spaced positions centred at `center`."""
    step = BOX_S + BOX_GAP
    start = center - (count - 1) * step / 2
    return [start + i * step for i in range(count)]


def shelf_y(name, cy, x_wall, sign, n_boxes=3, c_shelf=C_SHELF, c_box=C_BOX):
    """Shelf with width along Y, leaning against a Y-axis wall.

    Args:
        name:    unique prefix for all generated links
        cy:      shelf centre along Y (world coords)
        x_wall:  inner face x of the wall the shelf leans against
        sign:    +1 = west wall (shelf extends toward +x)
                 -1 = east wall (shelf extends toward -x)
        n_boxes: boxes per shelf level
    """
    cx = x_wall + sign * SHELF_D / 2       # shelf footprint centre x
    bx = x_wall + sign * SIDE_T / 2        # back panel centre x
    step = (SHELF_H - BOARD_T) / (N_LEVELS + 1)

    links = []

    # ─ Frame ─────────────────────────────────────────────────────────────────
    links.append(solid_link(
        f'{name}_back', (bx, cy, SHELF_H / 2),
        (SIDE_T, SHELF_W, SHELF_H), c_shelf))
    for sfx, dy in (('l', -(SHELF_W / 2 - SIDE_T / 2)),
                    ('r',   SHELF_W / 2 - SIDE_T / 2)):
        links.append(solid_link(
            f'{name}_s{sfx}', (cx, cy + dy, SHELF_H / 2),
            (SHELF_D - SIDE_T, SIDE_T, SHELF_H), c_shelf))

    # ─ Boards ─────────────────────────────────────────────────────────────────
    board_zs = [i * step for i in range(N_LEVELS + 1)] + [SHELF_H - BOARD_T]
    for i, bz in enumerate(board_zs):
        links.append(solid_link(
            f'{name}_brd{i}', (cx, cy, bz + BOARD_T / 2),
            (SHELF_D - SIDE_T, SHELF_W - 2 * SIDE_T, BOARD_T), c_shelf))

    # ─ Boxes on levels 1..N_LEVELS ────────────────────────────────────────────
    box_cx = bx + sign * (SIDE_T / 2 + BOX_S / 2)
    for level in range(1, N_LEVELS + 1):
        bz = board_zs[level] + BOARD_T + BOX_S / 2
        for j, by in enumerate(_box_row(cy, n_boxes)):
            links.append(solid_link(
                f'{name}_bx{level}{j}', (box_cx, by, bz),
                (BOX_S, BOX_S, BOX_S), c_box))

    return links


def shelf_x(name, cx, y_wall, sign, n_boxes=3, c_shelf=C_SHELF, c_box=C_BOX):
    """Shelf with width along X, leaning against an X-axis wall.

    Args:
        cx:     shelf centre along X (world coords)
        y_wall: inner face y of the wall
        sign:   +1 = south wall (shelf extends toward +y)
                -1 = north wall (shelf extends toward -y)
    """
    cy  = y_wall + sign * SHELF_D / 2
    by_ = y_wall + sign * SIDE_T / 2
    step = (SHELF_H - BOARD_T) / (N_LEVELS + 1)

    links = []

    links.append(solid_link(
        f'{name}_back', (cx, by_, SHELF_H / 2),
        (SHELF_W, SIDE_T, SHELF_H), c_shelf))
    for sfx, dx in (('l', -(SHELF_W / 2 - SIDE_T / 2)),
                    ('r',   SHELF_W / 2 - SIDE_T / 2)):
        links.append(solid_link(
            f'{name}_s{sfx}', (cx + dx, cy, SHELF_H / 2),
            (SIDE_T, SHELF_D - SIDE_T, SHELF_H), c_shelf))

    board_zs = [i * step for i in range(N_LEVELS + 1)] + [SHELF_H - BOARD_T]
    for i, bz in enumerate(board_zs):
        links.append(solid_link(
            f'{name}_brd{i}', (cx, cy, bz + BOARD_T / 2),
            (SHELF_W - 2 * SIDE_T, SHELF_D - SIDE_T, BOARD_T), c_shelf))

    box_cy = by_ + sign * (SIDE_T / 2 + BOX_S / 2)
    for level in range(1, N_LEVELS + 1):
        bz = board_zs[level] + BOARD_T + BOX_S / 2
        for j, bx in enumerate(_box_row(cx, n_boxes)):
            links.append(solid_link(
                f'{name}_bx{level}{j}', (bx, box_cy, bz),
                (BOX_S, BOX_S, BOX_S), c_box))

    return links


def desk(name, cx, cy, facing='x', c_desk=C_DESK):
    """Desk with 4 legs and a table top.

    Args:
        facing: 'x' → width along X, 'y' → width along Y
    """
    dw, dd = (DESK_W, DESK_D) if facing == 'x' else (DESK_D, DESK_W)
    leg_h = DESK_H - DESK_TOP

    links = []
    links.append(solid_link(
        f'{name}_top', (cx, cy, DESK_H - DESK_TOP / 2),
        (dw, dd, DESK_TOP), c_desk))
    for i, (sx, sy) in enumerate([(-1, -1), (-1, 1), (1, -1), (1, 1)]):
        lx = cx + sx * (dw / 2 - LEG_S / 2 - 0.04)
        ly = cy + sy * (dd / 2 - LEG_S / 2 - 0.04)
        links.append(solid_link(
            f'{name}_leg{i}', (lx, ly, leg_h / 2),
            (LEG_S, LEG_S, leg_h), c_desk))

    return links
