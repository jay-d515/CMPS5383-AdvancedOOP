"""
main.py
Entry point for the program.
"""

# imports the Game class
from game import Game

if __name__ == "__main__":
    # variable that defines the lsit of players
    players = ["Jadyn", "Maggie", "Gracie", "Isa"]
    # creates a new game
    game = Game(players)
    # runs a game of UNO
    game.run()
    