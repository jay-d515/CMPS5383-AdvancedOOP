# Uno Rules:
# CARDS-
# - should be 108 cards; 25 of each color (red, blue, green, yellow) and 8 wild cards
#   - 19 number cards (1 number 0 and 2 of each number 1-9) of each color
#   - 6 action cards (2 each of skip, reverse, draw 2) of each color
#   - 8 wild card (4 each of wild and wild draw 4)
# SETUP- (will be focused on 2 player gameplay)
# - Each player is dealt 7 cards from the deck
#   - The remaining cards are placed face down to form a draw pile
#   - The top card of te draw pile is turned over to form a discard pile
# GAMEPLAY-
# - Randomize which player goes first
#   - If the first card turned up from the draw pile is an action card, the action 
#     is applied to the first player
#   - If the first card turned up from the draw pile is a wild card, the first player must
#     choose a color for the next player to match
#   - If the first card turned up from the draw pile is a wild draw 4 card, the first player must
#     return it to the draw pile shuffle the deck, and turn over a new card
# - Players take turns playing a card from their hand that matches the card in the discard pile
#   - If the player has a card that matches the number, color, or the symbol/action of 
#     the card in the discard pile, they may play that card
#   - If the player plays a wild card, they must choose a color for the next player to match
#   - If the player plays a draw 2 or wild draw 4 card, the next player must draw 2 or 4 cards
#     respectively and forfeit their turn
#   - If a player plays a skip card, the next player loses their turn
#   - If a player plays a reverse card, the order of play is reversed
#   - If a player does not have a playable card OR chooses not to play any of their cards,
#     they must draw a card from the draw pile
# - If the draw pile is empty, the discard pile is shuffled and turned over to form a new draw pile
# - ONLY ONE CARD MAY BE PLAYED PER TURN
# - The game continues until a player has 1 card left
# - When a player has 1 card left, they must say "UNO" before the next player takes their turn
#   - If the player does not say "UNO" and is caught by the other player, they must draw 2 cards
#   - If the is unable to play their last card and needs to draw, but after drawing, is able to play that card,
#     they still must say "UNO"

import random

class Card:
    def __init__(self, color):
        self.color = color # (Red, Yellow, Green, Blue, or Wild)
        
    def matches(self, current_color, other_card):
        return self.color == current_color
    
        # discard_pile will be defined later in the Game class, so we can use it here to add the card to the discard pile when played

    def play(self, game):
        game.discard_pile.append(self)
    
    def __str__(self):
        return print(f"{self.color} Card")
        
class NumberCard(Card):
    """Represents a number card in Uno (0-9)"""
    def __init__(self, color, number):
        super().__init__(color)
        self.number = number
    
    # Checks if the card matches the current color or the number of the card 
    def matches(self, current_color, other_card):
        # Check if the color of the card matches the current color
        if self.color == current_color:
            # the card matches 
            return True
        # Check if the card is a number card and has the same number
        if isinstance(other_card, NumberCard) and self.number == other_card.number:
            # the card matches if the number is the same, regardless of color
            return True
        # The card does not match the current color or the number of the other card
        else:
            return False
    
    # discard_pile will be defined later in the Game class, so we can use it here to add the card to the discard pile when played
    def play(self, game):
        super.play(game)
        
    def __str__(self):
        return print(f"{self.color} {self.number} Card")
    
class PlusTwoCard(Card):
    """Forces the next player to draw two cards"""
    def __init__(self, color):
        super().__init__(color)
    
class SkipCard(Card):
    """Skips the next player's turn"""
    def __init__(self, color):
        super().__init__(color)
        
    def play(self, game):
        super.play(game)
        game.advance_turn # player index + 1
        print(f"{game.current_player} has been skipped!")

    def __str__(self):
        return print(f"{self.color} Skip")      
    
class ReverseCard(Card):
    """Reverses the order of play"""
    def __init__(self, color):
        super.__init__(color)
    
class WildCard(Card):
    """Changes the current color to one of the player's choice"""
    def __init__(self):
        pass
    
class WildDrawFourCard(WildCard):
    """Changes the current color to one of the player's choice and forces the next player to draw four cards"""
    def __init__(self):
        pass