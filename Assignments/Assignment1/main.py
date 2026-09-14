"""
main.py
Entry point for the program.
"""

# imports the Game class
from game import Game

if __name__ == "__main__":
    # creates a new game
    game = Game(["Jadyn", "Maggie", "Gracie"])
    # runs a game of UNO
    game.run()