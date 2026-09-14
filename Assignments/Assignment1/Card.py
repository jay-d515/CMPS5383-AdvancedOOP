"""
card.py
This file defines the Card hierarchy: the parent Card class and its subclasses.
- Each subclass overrides play() to provide different behavior.
"""

class Card:
    """Parent class. holds shared data and default behavior."""
    def __init__(self, color):
        """Initializes the card color."""
        self.color = color # (Red, Yellow, Green, Blue, or Wild)
        
    def matches(self, other_card, current_color):
        """Default matching rule: same color counts as a match."""
        return self.color == current_color

    def play(self, game):
        """This card's effect is applied to the game state.
           - Base class places the card, and the subclasses override this
             to add real behavior (skip, reverse, draw, wild card color pick)."""
             # played card is placed in the discard pile
        game.discard_pile.append(self)
        # prints which card was placed down
        print(f"  -> {self} placed down.")
    
    def __str__(self):
        """returns a string representation of a Card object."""
        return f"{self.color} Card"
        
class NumberCard(Card):
    """Represents a standard number card in Uno (0-9)."""
    def __init__(self, color, number):
        """Initializes the card color and number."""
        super().__init__(color) # inherited from class Card
        self.number = number # (0-9)
    
    def matches(self, other_card, current_color):
        """Overrides the base class "matches" method to check if the card matches
           the current color AND the number."""
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
        
    def __str__(self):
        """Overrides the base class "__str__" method to return a string representation
           of a NumberCard object card."""
        return f"{self.color} {self.number} Card"
    
class PlusTwoCard(Card):
    """Represents and action card in Uno which forces the next player to draw two
       cards and lose their turn."""
    def __init__(self, color):
        """Initializes the card color."""
        super().__init__(color) # inherited from class Card
        
    def play(self, game):
        """Overrides the base class "play" method to force the next player
           to draw 2 cards, and have their turn skipped."""
        # played card is placed in the discard pile
        super().play(game) # inherited from class Card
        # moves to the next player's (i.e. the victim's) turn,
        # that has to draw 2 cards
        game.advance_turn()
        victim = game.current_player()
        # victim draws 2 cards from the deck
        for _ in range(2):
            victim.draw(game.deck)
            # print which player was forced to draw 2 cards
        print(f"  -> {victim.name} draws 2 cards and is skipped!")
    
    def __str__(self):
        """Overrides the base class "__str__" method to return a string representation
           of a PlusTwoCard object."""
        return f"{self.color} Plus Two"
    
class SkipCard(Card):
    """Represents an action card in Uno which skips the next player's turn."""
    def __init__(self, color):
        """Initializes the card color."""
        super().__init__(color) # inherited from class Card
        
    def play(self, game):
        """Overrides the base class "play" method to skip the next player's turn."""
        # played card is placed in the discard pile
        super().play(game) # inherited from class Card
        # moves to the next player's (i.e. the victim's) turn,
        # that will be skipped
        game.advance_turn()
        # prints out which player's turn was skipped
        print(f"  -> {game.current_player().name} has been skipped!")

    def __str__(self):
        """Overrides the base class "__str__" method to return a string representation
           of a SkipCard object."""
        return f"{self.color} Skip"      
    
class ReverseCard(Card):
    """Represents an action card in Uno which reverses the order of play."""
    def __init__(self, color):
        """Initializes the card color."""
        super().__init__(color) # inherited from class Card
        
    def play(self, game):
        """Overrides the base class "play" method to reverse the order of play."""
        # played card is placed in the discard pile
        super().play(game) # inherited from class Card
        # reverses the game direction
        game.direction *= -1
        # prints a message about the game order being reversed
        print("  -> Turn order reversed!")
    
    def __str__(self):
        """Overrides the base class "__str__" method to return a string representation
           of a ReverseCard object."""
        return f"{self.color} Reverse"
    
class WildCard(Card):
    """Represents a wild card in Uno which changes the current color to one of
       the player's choice."""
    def __init__(self):
        """Initializes the card color to Wild."""
        super().__init__("Wild") # inherited from class Card
        
    def matches(self, other_card, current_color):
        """Overrides the base class "matches" method to allow wild cards to always
           be played."""
        # remains true because wild cards can be played no matter what the
        # previous card was
        return True
    
    def play(self, game):
        """Overrides the base class "play" method to change the current color
           to one of the player's choice."""
        # played card is placed in the discard pile
        super().play(game) # inherited from class Card
        # current color is changed to one of the player's choice
        new_color = game.current_player().choose_color()
        game.current_color = new_color
        # prints what the new color is
        print(f"  -> Wild card played. The new color is {new_color}")
        
    def __str__(self):
        """Overrides the base class "__str__" method to return a string representation
           of a WildCard object."""
        return "Wild"
    
class WildDrawFourCard(WildCard):
    """Represents a wild card in Uno which changes the current color to one of the
       player's choice and forces the next player to draw four cards."""
    def __init__(self):
        super().__init__()   
       
    def play(self, game):
        """Overrides the base class "play" method to change the current color
           to one of the player's choice, and force the next player to draw 4 cards."""
        # played card is placed in the discard pile
        super().play(game) # inherited from class Card
        # moves to the next player's (i.e. the victim's) turn,
        # that has to draw 4 cards
        game.advance_turn()
        victim = game.current_player()
        # victim draws 4 cards from the deck
        for _ in range(4):
            victim.draw(game.deck)
        # prints which player was forced to draw 4 cards
        print(f"{victim.name} draws 4 cards and is skipped!")
    
    def __str__(self):
        """Overrides the base class "__str__" method to return a string representation
           of a WildDrawFourCard object."""
        return "Wild Draw Four"
        