# -*- coding: utf-8 -*-
# handy_games.py -- Tetris & Snake furs Handy-System
# Spiele nur spielbar wenn Handy eingeschaltet (HANDY_AN_ROLE_ID)

import random
from config import *

# \u2500\u2500 Shared State \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
_states: dict[int, dict] = {}   # user_id -> game state

# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550
#  TETRIS
# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550

_TW, _TH = 10, 18   # board width, height

# Piece-Shapes: Liste von Rotationen, jede Rotation: Liste (row, col) Offsets
_T_PIECES: dict[str, list[list[tuple[int, int]]]] = {
    "I": [
        [(0,0),(0,1),(0,2),(0,3)],
        [(0,0),(1,0),(2,0),(3,0)],
    ],
    "O": [
        [(0,0),(0,1),(1,0),(1,1)],
    ],
    "T": [
        [(0,0),(0,1),(0,2),(1,1)],
        [(0,0),(1,0),(1,1),(2,0)],
        [(0,1),(1,0),(1,1),(1,2)],
        [(0,1),(1,0),(1,1),(2,1)],
    ],
    "S": [
        [(0,1),(0,2),(1,0),(1,1)],
        [(0,0),(1,0),(1,1),(2,1)],
    ],
    "Z": [
        [(0,0),(0,1),(1,1),(1,2)],
        [(0,1),(1,0),(1,1),(2,0)],
    ],
    "J": [
        [(0,0),(1,0),(1,1),(1,2)],
        [(0,0),(0,1),(1,0),(2,0)],
        [(0,0),(0,1),(0,2),(1,2)],
        [(0,1),(1,1),(2,0),(2,1)],
    ],
    "L": [
        [(0,2),(1,0),(1,1),(1,2)],
        [(0,0),(1,0),(2,0),(2,1)],
        [(0,0),(0,1),(0,2),(1,0)],
        [(0,0),(0,1),(1,1),(2,1)],
    ],
}
_T_NAMES = list(_T_PIECES.keys())
_T_COLOR = {"I": 1, "O": 2, "T": 3, "S": 4, "Z": 5, "J": 6, "L": 7}

# Leeres Feld + Farben je Piece (als Unicode-Escapes)
_T_EMOJI = [
    "\u2b1b",       # 0 leer   (\u2b1b)
    "\U0001f7e6",   # 1 I      ()
    "\U0001f7e8",   # 2 O      ()
    "\U0001f7ea",   # 3 T      ()
    "\U0001f7e9",   # 4 S      ()
    "\U0001f7e5",   # 5 Z      ()
    "\U0001f7eb",   # 6 J      ()
    "\U0001f7e7",   # 7 L      ()
]


def _t_cells(state) -> list[tuple[int, int]]:
    shape = _T_PIECES[state["piece"]][state["rot"]]
    return [(state["pr"] + dr, state["pc"] + dc) for dr, dc in shape]


def _t_valid(board, cells) -> bool:
    for r, c in cells:
        if r < 0 or r >= _TH or c < 0 or c >= _TW:
            return False
        if r >= 0 and board[r][c] != 0:
            return False
    return True


def tetris_new(uid: int):
    p, n = random.choice(_T_NAMES), random.choice(_T_NAMES)
    _states[uid] = {
        "kind":  "tetris",
        "board": [[0] * _TW for _ in range(_TH)],
        "piece": p, "rot": 0, "pr": 0, "pc": 3,
        "next":  n,
        "score": 0, "lines": 0,
        "over":  False,
    }


def _t_lock(state):
    board = state["board"]
    color = _T_COLOR[state["piece"]]
    for r, c in _t_cells(state):
        if 0 <= r < _TH and 0 <= c < _TW:
            board[r][c] = color
    full = [i for i in range(_TH) if all(board[i][j] for j in range(_TW))]
    for i in sorted(full, reverse=True):
        board.pop(i)
        board.insert(0, [0] * _TW)
    pts = [0, 100, 300, 500, 800]
    state["score"] += pts[min(len(full), 4)]
    state["lines"] += len(full)
    state["piece"], state["rot"], state["pr"], state["pc"] = state["next"], 0, 0, 3
    state["next"] = random.choice(_T_NAMES)
    if not _t_valid(board, _t_cells(state)):
        state["over"] = True


def tetris_move(state, dc: int):
    if state["over"]: return
    cells = [(r, c + dc) for r, c in _t_cells(state)]
    if _t_valid(state["board"], cells):
        state["pc"] += dc


def tetris_rotate(state):
    if state["over"]: return
    rots = _T_PIECES[state["piece"]]
    new_rot = (state["rot"] + 1) % len(rots)
    cells = [(state["pr"] + dr, state["pc"] + dc) for dr, dc in rots[new_rot]]
    if _t_valid(state["board"], cells):
        state["rot"] = new_rot


def tetris_drop(state):
    if state["over"]: return
    cells = [(r + 1, c) for r, c in _t_cells(state)]
    if _t_valid(state["board"], cells):
        state["pr"] += 1
    else:
        _t_lock(state)


def tetris_hard_drop(state):
    if state["over"]: return
    while True:
        cells = [(r + 1, c) for r, c in _t_cells(state)]
        if _t_valid(state["board"], cells):
            state["pr"] += 1
        else:
            break
    _t_lock(state)


def tetris_render(state) -> str:
    board = [row[:] for row in state["board"]]
    if not state["over"]:
        color = _T_COLOR[state["piece"]]
        for r, c in _t_cells(state):
            if 0 <= r < _TH and 0 <= c < _TW:
                board[r][c] = color
    rows = ["".join(_T_EMOJI[cell] for cell in row) for row in board]

    next_grid = [[0] * 4 for _ in range(2)]
    for dr, dc in _T_PIECES[state["next"]][0]:
        if 0 <= dr < 2 and 0 <= dc < 4:
            next_grid[dr][dc] = _T_COLOR[state["next"]]
    next_rows = ["".join(_T_EMOJI[c] for c in r) for r in next_grid]

    header = "\U0001f3ae **TETRIS**\n"
    info   = f"\U0001f4ca Score: **{state['score']}**  |  Linien: **{state['lines']}**\n"
    if state["over"]:
        info += "\U0001f480 **GAME OVER**\n"
    board_txt = "\n".join(rows)
    next_txt  = "**Nachstes:**\n" + "\n".join(next_rows)
    return f"{header}{info}{board_txt}\n{next_txt}"


class TetrisView(discord.ui.View):
    def __init__(self, uid: int):
        super().__init__(timeout=300)
        self.uid = uid

    def _check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.uid

    async def _refresh(self, interaction: discord.Interaction):
        state = _states.get(self.uid)
        if not state:
            await interaction.response.edit_message(content="\U0001f4f1 Spiel nicht gefunden.", view=None)
            return
        txt  = tetris_render(state)
        view = self if not state["over"] else _GameOverView(self.uid, "tetris")
        await interaction.response.edit_message(content=txt, view=view)

    @discord.ui.button(label="\u21ba Drehen", style=discord.ButtonStyle.secondary, row=0)
    async def btn_rotate(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self._check(interaction): await interaction.response.defer(); return
        tetris_rotate(_states[self.uid])
        await self._refresh(interaction)

    @discord.ui.button(label="\u25c0 Links", style=discord.ButtonStyle.primary, row=0)
    async def btn_left(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self._check(interaction): await interaction.response.defer(); return
        tetris_move(_states[self.uid], -1)
        await self._refresh(interaction)

    @discord.ui.button(label="\u25bc Unten", style=discord.ButtonStyle.primary, row=0)
    async def btn_down(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self._check(interaction): await interaction.response.defer(); return
        tetris_drop(_states[self.uid])
        await self._refresh(interaction)

    @discord.ui.button(label="\u25b6 Rechts", style=discord.ButtonStyle.primary, row=0)
    async def btn_right(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self._check(interaction): await interaction.response.defer(); return
        tetris_move(_states[self.uid], 1)
        await self._refresh(interaction)

    @discord.ui.button(label="\u2b07 Fallen", style=discord.ButtonStyle.danger, row=0)
    async def btn_hard(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self._check(interaction): await interaction.response.defer(); return
        tetris_hard_drop(_states[self.uid])
        await self._refresh(interaction)

    @discord.ui.button(label="\U0001f504 Neu starten", style=discord.ButtonStyle.success, row=1)
    async def btn_new(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self._check(interaction): await interaction.response.defer(); return
        tetris_new(self.uid)
        await self._refresh(interaction)

    @discord.ui.button(label="\u2716 Beenden", style=discord.ButtonStyle.danger, row=1)
    async def btn_quit(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self._check(interaction): await interaction.response.defer(); return
        _states.pop(self.uid, None)
        await interaction.response.edit_message(content="\U0001f4f1 Tetris beendet.", view=None)


async def start_tetris(interaction: discord.Interaction):
    tetris_new(interaction.user.id)
    txt = tetris_render(_states[interaction.user.id])
    await interaction.response.send_message(
        content=txt,
        view=TetrisView(interaction.user.id),
        ephemeral=True,
    )


# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550
#  SNAKE
# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550

_SW = 12   # Spielfeld-Breite und Hoehe (inkl. 1-Zellen-Rand)

_S_EMPTY = "\u2b1b"        # \u2b1b
_S_WALL  = "\U0001f7eb"    # 
_S_HEAD  = "\U0001f40d"    # 
_S_BODY  = "\U0001f7e9"    # 
_S_FOOD  = "\U0001f34e"    # 


def _s_free(state) -> list[tuple[int, int]]:
    snake_set = set(state["snake"])
    return [
        (r, c)
        for r in range(1, _SW - 1)
        for c in range(1, _SW - 1)
        if (r, c) not in snake_set
    ]


def snake_new(uid: int):
    mid = _SW // 2
    snake = [(mid, mid), (mid, mid - 1), (mid, mid - 2)]
    food  = random.choice([
        (r, c)
        for r in range(1, _SW - 1)
        for c in range(1, _SW - 1)
        if (r, c) not in snake
    ])
    _states[uid] = {
        "kind":  "snake",
        "snake": snake,
        "dir":   (0, 1),
        "food":  food,
        "score": 0,
        "over":  False,
    }


def snake_turn(state, dr: int, dc: int):
    if state["over"]: return
    old_dr, old_dc = state["dir"]
    if (dr, dc) == (-old_dr, -old_dc):
        return
    state["dir"] = (dr, dc)
    _snake_step(state)


def _snake_step(state):
    head_r, head_c = state["snake"][0]
    dr, dc = state["dir"]
    new_head = (head_r + dr, head_c + dc)
    r, c = new_head
    if not (1 <= r < _SW - 1 and 1 <= c < _SW - 1):
        state["over"] = True
        return
    if new_head in state["snake"]:
        state["over"] = True
        return
    state["snake"].insert(0, new_head)
    if new_head == state["food"]:
        state["score"] += 10
        free = _s_free(state)
        state["food"] = random.choice(free) if free else None
    else:
        state["snake"].pop()


def snake_render(state) -> str:
    grid = [[_S_EMPTY] * _SW for _ in range(_SW)]
    for r in range(_SW):
        grid[r][0] = grid[r][_SW - 1] = _S_WALL
    for c in range(_SW):
        grid[0][c] = grid[_SW - 1][c] = _S_WALL

    for i, (r, c) in enumerate(state["snake"]):
        grid[r][c] = _S_HEAD if i == 0 else _S_BODY

    if state["food"]:
        fr, fc = state["food"]
        grid[fr][fc] = _S_FOOD

    rows = ["".join(row) for row in grid]
    header = "\U0001f40d **SNAKE**\n"
    info   = f"\U0001f4ca Score: **{state['score']}**  |  Lange: **{len(state['snake'])}**\n"
    if state["over"]:
        info += "\U0001f480 **GAME OVER**\n"
    return header + info + "\n".join(rows)


class SnakeView(discord.ui.View):
    def __init__(self, uid: int):
        super().__init__(timeout=300)
        self.uid = uid

    def _check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.uid

    async def _refresh(self, interaction: discord.Interaction):
        state = _states.get(self.uid)
        if not state:
            await interaction.response.edit_message(content="\U0001f4f1 Spiel nicht gefunden.", view=None)
            return
        txt  = snake_render(state)
        view = self if not state["over"] else _GameOverView(self.uid, "snake")
        await interaction.response.edit_message(content=txt, view=view)

    @discord.ui.button(label="\u2b06 Hoch", style=discord.ButtonStyle.primary, row=0)
    async def btn_up(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self._check(interaction): await interaction.response.defer(); return
        snake_turn(_states[self.uid], -1, 0)
        await self._refresh(interaction)

    @discord.ui.button(label="\U0001f504 Neu starten", style=discord.ButtonStyle.success, row=0)
    async def btn_new(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self._check(interaction): await interaction.response.defer(); return
        snake_new(self.uid)
        await self._refresh(interaction)

    @discord.ui.button(label="\u2716 Beenden", style=discord.ButtonStyle.danger, row=0)
    async def btn_quit(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self._check(interaction): await interaction.response.defer(); return
        _states.pop(self.uid, None)
        await interaction.response.edit_message(content="\U0001f4f1 Snake beendet.", view=None)

    @discord.ui.button(label="\u2b05 Links", style=discord.ButtonStyle.primary, row=1)
    async def btn_left(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self._check(interaction): await interaction.response.defer(); return
        snake_turn(_states[self.uid], 0, -1)
        await self._refresh(interaction)

    @discord.ui.button(label="\u2b07 Runter", style=discord.ButtonStyle.primary, row=1)
    async def btn_down(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self._check(interaction): await interaction.response.defer(); return
        snake_turn(_states[self.uid], 1, 0)
        await self._refresh(interaction)

    @discord.ui.button(label="\u27a1 Rechts", style=discord.ButtonStyle.primary, row=1)
    async def btn_right(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self._check(interaction): await interaction.response.defer(); return
        snake_turn(_states[self.uid], 0, 1)
        await self._refresh(interaction)


async def start_snake(interaction: discord.Interaction):
    snake_new(interaction.user.id)
    txt = snake_render(_states[interaction.user.id])
    await interaction.response.send_message(
        content=txt,
        view=SnakeView(interaction.user.id),
        ephemeral=True,
    )


# \u2500\u2500 Game Over View \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

class _GameOverView(discord.ui.View):
    def __init__(self, uid: int, kind: str):
        super().__init__(timeout=120)
        self.uid  = uid
        self.kind = kind

    @discord.ui.button(label="\U0001f504 Nochmal spielen", style=discord.ButtonStyle.success)
    async def btn_retry(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.uid: await interaction.response.defer(); return
        if self.kind == "tetris":
            tetris_new(self.uid)
            txt  = tetris_render(_states[self.uid])
            view = TetrisView(self.uid)
        else:
            snake_new(self.uid)
            txt  = snake_render(_states[self.uid])
            view = SnakeView(self.uid)
        await interaction.response.edit_message(content=txt, view=view)

    @discord.ui.button(label="\u2716 Schliessen", style=discord.ButtonStyle.danger)
    async def btn_close(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.uid: await interaction.response.defer(); return
        _states.pop(self.uid, None)
        await interaction.response.edit_message(content="\U0001f4f1 Spiel beendet.", view=None)
