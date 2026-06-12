import re

SGF_COLS = 'abcdefghijklmnopqrs'
GTP_COLS = 'ABCDEFGHJKLMNOPQRST'
_S2G_COL = {SGF_COLS[i]: GTP_COLS[i] for i in range(19)}
_S2G_ROW = {SGF_COLS[i]: 19 - i for i in range(19)}


def sgf_to_gtp(s):
    if s in ('', 'tt'):
        return 'pass'
    return '{}{}'.format(_S2G_COL[s[0]], _S2G_ROW[s[1]])


def parse_moves(sgf_text):
    moves = []
    for m in re.finditer(r';(B|W)\[([a-z]{2}|tt|)\]', sgf_text):
        moves.append((m.group(1), sgf_to_gtp(m.group(2))))
    return moves
