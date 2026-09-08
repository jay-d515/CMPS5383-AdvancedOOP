import random

ship_xcoord = random.randint(1, 5)
ship_ycoord = random.randint(1, 5)

board = []

# initialize the board
for row in range(5):
    board.append(['.', '.', '.', '.', '.'])
    
def printBoard(board):
    for row in board:
        print(" ".join(row))

printBoard(board=board)
print(ship_xcoord, ship_ycoord)
for i in range(3):
    user_guess_xcoord = int(input("Guess the x-coordinate: "))
    user_guess_ycoord = int(input("Guess the y-coordinate: "))
    
    if ship_xcoord == user_guess_xcoord and ship_ycoord == user_guess_ycoord:
        print("HIT!")
        board[user_guess_ycoord][user_guess_xcoord] = 'H'
        # display the board
        printBoard(board)
        
        break
    else:
        print("MISS!")
        board[user_guess_ycoord][user_guess_xcoord] = 'M'
                
        # display the board
        printBoard(board)