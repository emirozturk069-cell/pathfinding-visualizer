import tkinter as tk
import time
import heapq
from collections import deque
import math


ROWS = 20
COLS = 20
CELL = 30

COLOR_EMPTY   = "white"
COLOR_WALL    = "black"
COLOR_START   = "green"
COLOR_GOAL    = "red"
COLOR_VISITED = "light green"
COLOR_PATH    = "yellow"
COLOR_WATER   = "#9fd2ff"   

TERRAIN_COST = {
    ".": 1.0,
    "w": 6.0,   
}


MAPS = {
    "MAP1": {
        "name": "Map 1",
        "grid": [
            "....#########...#...",
            "..............#.#.#.",
            "....###########...#.",
            "....wwwwwwwww######.",
            "....wwwwwwwww##...#.",
            "....wwwwwwwww##.#.#.",
            "....wwwwwwwww#..#...",
            "....wwwwwwwww#.#####",
            "....wwwwwwwww.......",
            "....wwwwwwwww.......",
            "S...wwwwwwwww......G",
            "....wwwwwww######.##",
            "....wwwwwww#...##..#",
            "....wwwwwww#.#.###..",
            "....wwwwwww#.#.####.",
            "....wwwwwww#.#.###..",
            "....wwwwwww#.#.###.#",
            "....wwwwwww#.#.###..",
            "....########.#.####.",
            ".............#......",
        ],
    },

    "MAP2": {
        "name": "Map 2",
        "grid": [
            "#####....G..........",
            "#...#..#.###..#.....",
            "#.#....#...##..#....",
            "#.####.###.###..#...",
            "#.#.##.#...###..##..",
            "#.#.##.#.####...##..",
            "#.#....#...#...###..",
            "#.#######.##..#####.",
            "....................",
            ".########.########..",
            "....................",
            ".#.#############.#..",
            ".#...............#..",
            ".#.#.#########.#.#..",
            ".#.#...........#.#..",
            ".#.#.#.#####.#.#.#..",
            ".#.#.#.......#.#.#..",
            ".#.#.#.#.S.#.#.#.#..",
            "....................",
            "####################",
        ],
    },
}

grid = [["." for _ in range(COLS)] for _ in range(ROWS)]
start = (0, 0)
goal  = (ROWS-1, COLS-1)
grid[start[0]][start[1]] = "S"
grid[goal[0]][goal[1]] = "G"

root = tk.Tk()
root.title("Pathfinding Visualizer")

canvas = tk.Canvas(root, width=COLS*CELL, height=ROWS*CELL, bg="white")
canvas.grid(row=0, column=0, rowspan=20, padx=5, pady=5)

side = tk.Frame(root)
side.grid(row=0, column=1, sticky="n", padx=5, pady=5)

info_frame = tk.Frame(root, bd=2, relief="groove")
info_frame.grid(row=19, column=1, sticky="se", padx=5, pady=5)

info_label = tk.Label(
    info_frame,
    text="Algorithm Information\n\n—\n—\n—\n—",
    justify="left",
    font=("Consolas", 10)
)
info_label.pack(padx=6, pady=6)

rect_id = [[None]*COLS for _ in range(ROWS)]

def init_grid_once():
    for r in range(ROWS):
        for c in range(COLS):
            x1, y1 = c*CELL, r*CELL
            x2, y2 = x1+CELL, y1+CELL
            rid = canvas.create_rectangle(x1, y1, x2, y2, fill=COLOR_EMPTY, outline="gray")
            rect_id[r][c] = rid

def paint_cell(r, c, color):
    canvas.itemconfig(rect_id[r][c], fill=color)

def redraw_grid():
    for r in range(ROWS):
        for c in range(COLS):
            if (r, c) == start:
                paint_cell(r, c, COLOR_START)
            elif (r, c) == goal:
                paint_cell(r, c, COLOR_GOAL)
            elif grid[r][c] == "#":
                paint_cell(r, c, COLOR_WALL)
            elif grid[r][c] == "w":
                paint_cell(r, c, COLOR_WATER)
            else:
                paint_cell(r, c, COLOR_EMPTY)

animating = False
anim_jobs = []

drag_mode = None

def start_drag(event):
    global drag_mode
    if animating:
        return

    c = event.x // CELL
    r = event.y // CELL
    if not (0 <= r < ROWS and 0 <= c < COLS):
        return
    if (r, c) in [start, goal]:
        return

    drag_mode = "draw" if grid[r][c] != "#" else "erase"
    apply_drag(event)

def apply_drag(event):
    if animating:
        return

    c = event.x // CELL
    r = event.y // CELL
    if not (0 <= r < ROWS and 0 <= c < COLS):
        return
    if (r, c) in [start, goal]:
        return

    if drag_mode == "draw":
        if grid[r][c] != "#":
            grid[r][c] = "#"
            paint_cell(r, c, COLOR_WALL)
    elif drag_mode == "erase":
        if grid[r][c] == "#":
            grid[r][c] = "."
            paint_cell(r, c, COLOR_EMPTY)

def end_drag(event):
    global drag_mode
    drag_mode = None

def right_erase(event):
    global drag_mode
    drag_mode = "erase"
    apply_drag(event)

canvas.bind("<Button-1>", start_drag)
canvas.bind("<B1-Motion>", apply_drag)
canvas.bind("<ButtonRelease-1>", end_drag)

canvas.bind("<Button-3>", right_erase)
canvas.bind("<B3-Motion>", right_erase)
canvas.bind("<ButtonRelease-3>", end_drag)


def cell_traversal_cost(r, c) -> float:
    """Cell entry cost for Dijkstra/A*."""
    t = grid[r][c]
    return TERRAIN_COST.get(t, 1.0)

def neighbors4(node):
    r, c = node
    for dr, dc in [(1,0),(-1,0),(0,1),(0,-1)]:
        nr, nc = r+dr, c+dc
        if 0 <= nr < ROWS and 0 <= nc < COLS and grid[nr][nc] != "#":
            yield (nr, nc)

def reconstruct_path(parent):
    if goal not in parent:
        return []
    path = []
    cur = goal
    while cur is not None:
        path.append(cur)
        cur = parent.get(cur)
    return path[::-1]

def update_info(name, visited, path_len, runtime_ms):
    algo_names = {
        "BFS": "BFS",
        "Dijkstra": "Dijkstra",
        "A*_M": "A* Manhattan",
        "A*_E": "A* Euclidean"
    }
    info_label.config(
        text=
        f"{algo_names.get(name, name)}\n"
        f"Visited Nodes: {visited}\n"
        f"Path Length : {path_len}\n"
        f"Runtime     : {runtime_ms:.2f} ms"
    )


def animate(order, path, step_ms=1, path_ms=5, on_done=None):
    global animating, anim_jobs
    animating = True
    anim_jobs = []

    i = 0
    def step_visited():
        nonlocal i
        if i < len(order):
            r, c = order[i]
            if (r, c) != start and (r, c) != goal:
                paint_cell(r, c, COLOR_VISITED)
            i += 1
            job = root.after(step_ms, step_visited)
            anim_jobs.append(job)
        else:
            step_path()

    j = 0
    def step_path():
        nonlocal j
        if j < len(path):
            r, c = path[j]
            if (r, c) != start and (r, c) != goal:
                paint_cell(r, c, COLOR_PATH)
            j += 1
            job = root.after(path_ms, step_path)
            anim_jobs.append(job)
        else:
            animating = False
            anim_jobs.clear()
            if on_done:
                on_done()

    step_visited()


def bfs_compute():
    q = deque([start])
    parent = {start: None}
    visited = set([start])
    expanded = 0
    order = []

    while q:
        cur = q.popleft()
        expanded += 1
        order.append(cur)
        if cur == goal:
            break
        for nb in neighbors4(cur):
            if nb not in visited:
                visited.add(nb)
                parent[nb] = cur
                q.append(nb)

    path = reconstruct_path(parent)
    return expanded, order, path

def dijkstra_compute():
    parent = {start: None}
    dist = {start: 0.0}
    pq = [(0.0, start)]
    visited = set()
    expanded = 0
    order = []

    while pq:
        cost, cur = heapq.heappop(pq)
        if cur in visited:
            continue
        visited.add(cur)
        expanded += 1
        order.append(cur)

        if cur == goal:
            break

        for nb in neighbors4(cur):
            nr, nc = nb
            new_cost = cost + cell_traversal_cost(nr, nc) 
            if new_cost < dist.get(nb, 1e18):
                dist[nb] = new_cost
                parent[nb] = cur
                heapq.heappush(pq, (new_cost, nb))

    path = reconstruct_path(parent)
    return expanded, order, path

def astar_compute(mode="manhattan"):
    def h(n):
        r, c = n
        gr, gc = goal
        if mode == "euclidean":
            return math.hypot(r - gr, c - gc)
        return abs(r - gr) + abs(c - gc)

    parent = {start: None}
    g = {start: 0.0}
    pq = [(h(start), start)]
    closed = set()
    expanded = 0
    order = []

    while pq:
        _, cur = heapq.heappop(pq)
        if cur in closed:
            continue
        closed.add(cur)
        expanded += 1
        order.append(cur)

        if cur == goal:
            break

        for nb in neighbors4(cur):
            nr, nc = nb
            new_g = g[cur] + cell_traversal_cost(nr, nc)  
            if new_g < g.get(nb, 1e18):
                g[nb] = new_g
                f = new_g + h(nb)
                parent[nb] = cur
                heapq.heappush(pq, (f, nb))

    path = reconstruct_path(parent)
    return expanded, order, path


def set_buttons(state):
    for b in buttons:
        b.config(state=state)

def run_algo(name):
    global animating
    if animating:
        return

    redraw_grid()
    set_buttons("disabled")

    t0 = time.time()
    if name == "BFS":
        expanded, order, path = bfs_compute()
    elif name == "Dijkstra":
        expanded, order, path = dijkstra_compute()
    elif name == "A*_M":
        expanded, order, path = astar_compute("manhattan")
    else:
        expanded, order, path = astar_compute("euclidean")
    t1 = time.time()

    runtime_ms = (t1 - t0) * 1000
    update_info(name, expanded, len(path), runtime_ms)

    animate(order, path, step_ms=1, path_ms=5, on_done=lambda: set_buttons("normal"))

def stop_animation():
    global animating, anim_jobs, drag_mode
    for job in anim_jobs:
        try:
            root.after_cancel(job)
        except:
            pass
    anim_jobs.clear()
    animating = False
    drag_mode = None
    set_buttons("normal")

def reset_map():
    global grid, start, goal, drag_mode
    stop_animation()

    for r in range(ROWS):
        for c in range(COLS):
            grid[r][c] = "."

    start = (0, 0)
    goal  = (ROWS-1, COLS-1)
    grid[start[0]][start[1]] = "S"
    grid[goal[0]][goal[1]] = "G"

    redraw_grid()
    info_label.config(text="Algorithm Information\n\n—\n—\n—\n—")

def load_preset_map(map_key):
    global grid, start, goal, drag_mode
    stop_animation()

    preset = MAPS[map_key]["grid"]

    for r in range(ROWS):
        row = preset[r]
        for c in range(COLS):
            ch = row[c]
            if ch == "S":
                start = (r, c)
                grid[r][c] = "S"
            elif ch == "G":
                goal = (r, c)
                grid[r][c] = "G"
            elif ch == "#":
                grid[r][c] = "#"
            elif ch == "w":
                grid[r][c] = "w"
            else:
                grid[r][c] = "."

    redraw_grid()
    info_label.config(text="Algorithm Information\n\n—\n—\n—\n—")


buttons = []

b_bfs = tk.Button(side, text="Run BFS", width=14, command=lambda: run_algo("BFS"))
b_dij = tk.Button(side, text="Dijkstra", width=14, command=lambda: run_algo("Dijkstra"))
b_m   = tk.Button(side, text="A* Manhattan", width=14, command=lambda: run_algo("A*_M"))
b_e   = tk.Button(side, text="A* Euclidean", width=14, command=lambda: run_algo("A*_E"))
b_rst = tk.Button(side, text="Reset Map", width=14, command=reset_map)


b_map1 = tk.Button(side, text="Map 1", width=14, command=lambda: load_preset_map("MAP1"))
b_map2 = tk.Button(side, text="Map 2", width=14, command=lambda: load_preset_map("MAP2"))

b_bfs.grid(row=0, column=0, pady=8, sticky="ew")
b_dij.grid(row=1, column=0, pady=8, sticky="ew")
b_m.grid(row=2, column=0, pady=8, sticky="ew")
b_e.grid(row=3, column=0, pady=8, sticky="ew")
b_rst.grid(row=4, column=0, pady=8, sticky="ew")


b_map1.grid(row=5, column=0, pady=8, sticky="ew")
b_map2.grid(row=6, column=0, pady=8, sticky="ew")


buttons = [b_bfs, b_dij, b_m, b_e, b_rst, b_map1, b_map2]

root.resizable(False, False)


init_grid_once()
redraw_grid()
root.mainloop()
