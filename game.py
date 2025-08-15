import random

def init_board(size):
    """Initialize the game board"""
    board = [[0] * size for _ in range(size)]
    add_random_tile(board)
    add_random_tile(board)
    return board

def add_random_tile(board):
    """Add a new random tile (2 or 4)"""
    empty = [(i, j) for i in range(len(board)) for j in range(len(board)) if board[i][j] == 0]
    if empty:
        i, j = random.choice(empty)
        board[i][j] = random.choice([2, 4])

def get_score(board):
    """Return the highest tile value"""
    return max(max(row) for row in board)

def move_left(board):
    """Move tiles left"""
    moved = False
    size = len(board)
    for i in range(size):
        row = [x for x in board[i] if x != 0]
        for j in range(len(row) - 1):
            if row[j] == row[j + 1]:
                row[j] *= 2
                row[j + 1] = 0
                moved = True
        row = [x for x in row if x != 0]
        row += [0] * (size - len(row))
        if row != board[i]:
            moved = True
        board[i] = row
    return moved

def move_right(board):
    """Move tiles right"""
    moved = False
    size = len(board)
    for i in range(size):
        row = [x for x in board[i] if x != 0]
        for j in range(len(row) - 1, 0, -1):
            if row[j] == row[j - 1]:
                row[j] *= 2
                row[j - 1] = 0
                moved = True
        row = [x for x in row if x != 0]
        row = [0] * (size - len(row)) + row
        if row != board[i]:
            moved = True
        board[i] = row
    return moved

def move_up(board):
    """Move tiles up"""
    size = len(board)
    transposed = [[board[j][i] for j in range(size)] for i in range(size)]
    moved = move_left(transposed)
    board[:] = [[transposed[j][i] for j in range(size)] for i in range(size)]
    return moved

def move_down(board):
    """Move tiles down"""
    size = len(board)
    transposed = [[board[j][i] for j in range(size)] for i in range(size)]
    moved = move_right(transposed)
    board[:] = [[transposed[j][i] for j in range(size)] for i in range(size)]
    return moved

def is_game_over(board):
    """Check if no moves are left"""
    size = len(board)
    for i in range(size):
        for j in range(size):
            if board[i][j] == 0:
                return False
    for i in range(size):
        for j in range(size - 1):
            if board[i][j] == board[i][j + 1]:
                return False
    for i in range(size - 1):
        for j in range(size):
            if board[i][j] == board[i + 1][j]:
                return False
    return True
