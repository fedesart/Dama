#%% Dama game
 
from copy import deepcopy
# test
# 0 = empty cell
# 9 = grid limits
# 1 = player 1 - std pawn
# 2 = player 2 - std pawn
# 3 = player 1 - dama
# 4 = player 2 - dama

grid = [
    [9, 9, 9, 9, 9, 9, 9, 9, 9, 9],
    [9, 2, 0, 2, 0, 2, 0, 2, 0, 9],
    [9, 0, 2, 0, 2, 0, 2, 0, 2, 9],
    [9, 2, 0, 2, 0, 2, 0, 2, 0, 9],
    [9, 0, 0, 0, 0, 0, 0, 0, 0, 9],
    [9, 0, 0, 0, 0, 0, 0, 0, 0, 9],
    [9, 0, 1, 0, 1, 0, 1, 0, 1, 9],
    [9, 1, 0, 1, 0, 1, 0, 1, 0, 9],
    [9, 0, 1, 0, 1, 0, 1, 0, 1, 9],
    [9, 9, 9, 9, 9, 9, 9, 9, 9, 9]
    ]

available_rows = range(1, len(grid)-1)
odds = range(1, len(grid), 2)
evens = range(2, len(grid), 2)
black_cells = (evens, odds, evens, odds, evens, odds, evens, odds, evens, odds, evens, odds, evens)
dirs = {1: -1, 2: +1}
human = 1

class Node:
    # Node of a tree
    def __init__(self, parent=None):
        self.parent = parent
        if parent:
            parent.children.append(self)
        self.children = []
        self.data = None
        self.score = {}
        self.player = 0


def opponent(player):
    if player == 2:
        return 1
    elif player == 1:
        return 2

def dama(player):
    return player + 2


def assign_dama(grid, player):
    # Chech if a pawn reached the end of the grid
    # and convert it to dama
    for i in available_rows:
        for j in black_cells[i]:
            if grid[i][j] == player and grid[i + dirs[player]][j] == 9:
                grid[i][j] = dama(player)    

                
def calculate_score(grid):
    # Calculate the scores associated to each player
    # for a given grid configuration
    # Score is needed in order for the AI to evaluate the best next move
    scores = {1:0, 2:0}
    mult = 3 # dama is considered n times as valuable
    for row in grid:
        scores[1] = scores[1] + row.count(1) + row.count(dama(1)) * mult
        scores[2] = scores[2] + row.count(2) + row.count(dama(2)) * mult

    return scores


def calculate_capture_score(grid, player):
    # capture_score is used in order to decide which move is mandatory
    # The obligatory move is the one with the lowest capture_score value
    # This function should be used when the grid is frozen for the current player
    # with only the pawn that is moving being active (equal to 1-2-3-4)
    score = 0
    for row in grid:
        score = score + row.count(opponent(player)) + \
            10000 * row.count(dama(opponent(player))) - \
            100 * row.count(dama(player))

    return score


def freeze_player(grid, player):
    # Set negative value for all the pawns of the current player
    for i in available_rows:
        for j in black_cells[i]:
            if grid[i][j] == player:
                grid[i][j] = - grid[i][j]
    return grid


def unfreeze_all(grid):
    # Remove "-" from all the freezed pawns
    for i in available_rows:
        for j in black_cells[i]:
            grid[i][j] = abs(grid[i][j])
    return grid


def free_moves(grid, player=1):
    # Return the available free moves
    # for a given grid state and player turn
    # Free moves do not include obligatory moves
    states = []
    v = dirs[player]

    for i in available_rows:
        for j in black_cells[i]:

            # pedina
            if grid[i][j] == player:
                for k in (-1, +1):
                    if grid[i + v][j + k] == 0:
                        copy = deepcopy(grid)
                        copy[i][j] = 0
                        copy[i + v][j + k] = grid[i][j]
                        states.append(copy)

            # dama
            elif grid[i][j] == player + 2:
                for k in (-1, +1):
                    for h in (-1, +1):
                        if grid[i + h][j + k] == 0:
                            copy = deepcopy(grid)
                            copy[i][j] = 0
                            copy[i + h][j + k] = grid[i][j]
                            states.append(copy)

    return states


def get_next_captures(grid, player=1):
    # Return the obligatory moves 
    # for  a given grid state and player
    states = []
    v = dirs[player]

    for i in available_rows:
        for j in black_cells[i]:
            # Standard pawn
            if grid[i][j] == player:
                for k in (-1, +1):
                    if grid[i + v][j + k] == opponent(player): # Potential enemy position
                        if grid[i + 2 * v][j + 2 * k] == 0: # Potential free slot
                            copy = deepcopy(grid)
                            copy[i][j] = 0 # Free slot in the original position of the player's pawn
                            copy[i + v][j + k] = 0 # Delete the opponent's pawn
                            freeze_player(copy, player)
                            copy[i + 2 * v][j + 2 * k] = grid[i][j] # New position
                            states.append(copy)

            # Dama only
            elif grid[i][j] == dama(player):
                for k in (-1, +1): # check left and right
                    for h in (-1, +1): # check fwd and rwd
                        if (grid[i + h][j + k] == opponent(player)) or (grid[i + h][j + k] == dama(opponent(player))): # check for potential enemy
                            if grid[i + 2 * h][j + 2 * k] == 0: # Potential free slot after the enemy
                                copy = deepcopy(grid)
                                copy[i][j] = 0 # Free slot in the original position of the player's pawn
                                copy[i + h][j + k] = 0 # Delete the opponent's pawn
                                freeze_player(copy, player)
                                copy[i + 2 * h][j + 2 * k] = grid[i][j] # New position
                                states.append(copy)

    return states



def get_captures(grid, player=1):

    captures = []
    capture_scores = []

    tree = [Node()]
    tree[0].data = grid
    tree[0].player = player

    def build_captures_tree(parent, player, captures, capture_scores):

        for grid in get_next_captures(parent.data, player):

            node = Node(parent)
            node.data = grid
            node.player = player

            capture_score = calculate_capture_score(grid, player)
            copy = deepcopy(grid)
            unfreeze_all(copy)

            # Check if the current capture has a lower score 
            # compared to the others in the list
            # if yes -> clear the list and append this capture
            # if it has the same score -> append this capture
            # if it has higher score -> do nothing
            if not(captures):
                captures.append(copy)
                capture_scores.append(capture_score)
            elif capture_score < capture_scores[0]:
                captures.clear()
                capture_scores.clear()
                captures.append(copy)
                capture_scores.append(capture_score)
            elif capture_score == capture_scores[0]:
                captures.append(copy)
                capture_scores.append(capture_score)
            
            build_captures_tree(node, player, captures, capture_scores)

    build_captures_tree(tree[0], player, captures, capture_scores)

    return captures


def expand_node(parent, depth=5):
    # player = player that will do the next move
    # depth = number of consecutive moves that are simulated
    if depth >= 1:
        captures = get_captures(parent.data, parent.player)
                
        if captures:
            moves = captures
        else:
            moves = free_moves(parent.data, parent.player)

        for grid in moves:
            node = Node(parent)
            node.player = opponent(parent.player)
            node.data = grid
            node.score = calculate_score(grid)
            expand_node(node, depth=depth-1)



def get_final_scores(tree, output=[], search_depth=0):
    # Get the final scores associated with each one of the next moves in the tree
    # Scores are used in order to evaluate the best next move for the AI

    if tree.children:
        for ch in tree.children:
            output = get_final_scores(ch, output, search_depth+1)

    else:
        parent = tree
        for _ in range(search_depth - 1):
            parent = parent.parent
        output.append({'g':parent.data, 's':tree.score})

    return output


# testing

sc = calculate_score(grid)
print(sc)

s = free_moves(grid, 1)
for row in s[0]:
    print(row)

tree = [Node()]
tree[0].player = 2
tree[0].data = grid

d = 6
expand_node(tree[0], depth=d)

ch = tree[0]
while ch.children:
    print('--')
    print(calculate_score(ch.data))
    for row in ch.data:
        print(row)
    ch = ch.children[-1]

out = get_final_scores(tree[0])
