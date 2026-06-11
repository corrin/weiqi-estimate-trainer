import re
import os

SGF_COLS = 'abcdefghijklmnopqrs'
GTP_COLS = 'ABCDEFGHJKLMNOPQRST'


def sgf_to_gtp(s):
    if s in ('', 'tt'):
        return 'pass'
    col = SGF_COLS.index(s[0])
    row = 19 - SGF_COLS.index(s[1])
    return '{}{}'.format(GTP_COLS[col], row)


def parse_moves(sgf_text):
    moves = []
    for m in re.finditer(r';(B|W)\[([a-z]{2}|tt|)\]', sgf_text):
        moves.append((m.group(1), sgf_to_gtp(m.group(2))))
    return moves


def gtp_to_index(gtp_pos):
    if gtp_pos == 'pass':
        return None
    col = GTP_COLS.index(gtp_pos[0])
    row = 19 - int(gtp_pos[1:])
    return row, col


def replay_moves(moves, board_size=19):
    board = Board(board_size)
    for color, gtp_pos in moves:
        if gtp_pos == 'pass':
            continue
        row, col = gtp_to_index(gtp_pos)
        board.play(row, col, color)
    return board


class Board:
    def __init__(self, size=19):
        self.size = size
        self.grid = [[0] * size for _ in range(size)]

    def in_bounds(self, r, c):
        return 0 <= r < self.size and 0 <= c < self.size

    def neighbors(self, r, c):
        return [(r + dr, c + dc) for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]
                if self.in_bounds(r + dr, c + dc)]

    def play(self, row, col, color):
        stone = 1 if color == 'B' else 2
        self.grid[row][col] = stone
        opponent = 3 - stone
        visited = set()
        for nr, nc in self.neighbors(row, col):
            if (nr, nc) not in visited and self.grid[nr][nc] == opponent:
                group = self._find_group(nr, nc)
                visited.update(group)
                if not self._has_liberties(group):
                    for r, c in group:
                        self.grid[r][c] = 0

    def _find_group(self, r, c):
        color = self.grid[r][c]
        if color == 0:
            return set()
        group = set()
        stack = [(r, c)]
        while stack:
            cr, cc = stack.pop()
            if (cr, cc) in group:
                continue
            group.add((cr, cc))
            for nr, nc in self.neighbors(cr, cc):
                if (nr, nc) not in group and self.grid[nr][nc] == color:
                    stack.append((nr, nc))
        return group

    def _has_liberties(self, group):
        visited = set()
        for r, c in group:
            for nr, nc in self.neighbors(r, c):
                if (nr, nc) not in visited and (nr, nc) not in group:
                    visited.add((nr, nc))
                    if self.grid[nr][nc] == 0:
                        return True
        return False

    def to_coordinates(self):
        black = []
        white = []
        for r in range(self.size):
            for c in range(self.size):
                if self.grid[r][c] == 1:
                    black.append(grid_to_jgo(r, c, self.size))
                elif self.grid[r][c] == 2:
                    white.append(grid_to_jgo(r, c, self.size))
        return {'black': black, 'white': white}

    def to_grid(self):
        return [row[:] for row in self.grid]


def grid_to_jgo(row, col, board_size):
    col_letter = GTP_COLS[col]
    row_num = board_size - row
    return '{}{}'.format(col_letter, row_num)


def get_position(game_id, filepath, turn_analyzed, komi):
    sgf_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'games', filepath)
    with open(sgf_path, 'rb') as f:
        text = f.read().decode('utf-8', errors='replace')

    moves = parse_moves(text)
    if not moves:
        return None

    target_moves = moves[:min(turn_analyzed, len(moves))]
    board = replay_moves(target_moves)

    last_turn = None
    if target_moves:
        last_turn = target_moves[-1][0]

    return {
        'stones': board.to_coordinates(),
        'size': board.size,
        'komi': komi,
        'turn': turn_analyzed,
        'total_moves': len(moves),
        'last_move': target_moves[-1][1] if target_moves else None,
        'next_to_play': 'W' if last_turn == 'B' else 'B',
    }
