"""
player.py
This file defines the Player class. A player holds a hand and acts when the
Game coordinator calls its methods.
- Does not act on its own.
"""

# imports the random library
import random
# imports the Wildcard child class
from card import WildCard

class Player:
    """Holds each player's card hand."""
    def __init__(self, name):
        self.name = name
        self.hand = []
        
    def draw(self, deck):
        """Player draws card from the deck."""
        if deck:
            # player picks a card from the deck
            card = deck.pop()
            # drawn card is added in the players hand
            self.hand.append(card)
            return card
        return None
      
    def has_playable_card(self, current_card, current_color):
        """Checks if a player has any playable cards"""
        return any(c.matches(current_card, current_color) for c in self.hand)
    
    def choose_card(self, current_card, current_color):
        """Picks the first legal card found in a player's hand."""
        # checks for cards that ARE NOT wild first
        for card in self.hand:
            # if the card IS NOT a wildcard and matches the color or number
            # of the card at the top of the deck
            if not isinstance(card, WildCard) and card.matches(current_card, 
                                                               current_color):
                # the card is chosen to be played
                return card
        # then, checks for any wild cards if there are no other options
        for card in self.hand:
            # if the card is a wild
            if isinstance(card, WildCard):
                # the card is chosen to be played
                return card
        return None
    
    def choose_color(self):
        """Picks the color a player has the most of."""
        counts = {}
        for c in self.hand:
            # if a card in the player's hand IS NOT wild
            if c.color != "Wild":
                # keeps count of the number of cards a player has of each color
                counts[c.color] = counts.get(c.color, 0) + 1   
        if counts:
            # returns the max amount of each color a player has in their hand
            return max(counts, key=counts.get)
        # based on the current color, a random card is picked that is playable
        return random.choice(["Red", "Yellow", "Green", "Blue"])
    
    def __str__(self):
        """Returns a string representation of a Player object."""
        return self.name
    
    