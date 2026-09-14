"""
game.py
Defines the Game Coordinator class. This is what drives interaction
- calls player.choose_card() and then card.play(self). which is what
  makes Card and Player objects interact.
"""

# imports the random and time libraries
import random
import time

# imports the child classes from parent class Card
from card import NumberCard, PlusTwoCard, SkipCard, ReverseCard, WildCard, WildDrawFourCard
# imports the Player class
from player import Player

class Game:
    """Drives interaction between Card and Player objects"""
    # global variable of the card colors
    COLORS = ["Red", "Yellow","Green", "Blue"]
    
    def __init__(self, player_names):
        """Initializes the game state."""
        self.players = [Player(name) for name in player_names]
        self.deck = []
        self.discard_pile = []
        self.direction = 1
        self.turn_index = 0
        self.current_color = None
        self._build_deck()
        self._deal_starting_hands()
        self._flip_starting_card()
        
    def _build_deck(self):
        """Builds a deck of 108 cards.
           - 76 numbered cards
             - 19 cards of each color
               - 1 number 0 card and two sets of cards numbered 1-9
           - 24 action cards
             - 2 of each action card (skip, reverse, plus two)
             - 6 total for each color
           - 8 Wild cards"""
        for color in self.COLORS:
            # adds 1 zero of each color to the deck
            self.deck.append(NumberCard(color, 0))
            # adds two sets of cards numbered 1-9 to the deck
            for number in range(1, 10):
                self.deck.append(NumberCard(color, number))
                self.deck.append(NumberCard(color, number))
            # adds 2 of each action card for each color to the deck
            for _ in range(2):
                self.deck.append(SkipCard(color))
                self.deck.append(ReverseCard(color))
                self.deck.append(PlusTwoCard(color))
        # adds 4 of each wild card to the deck        
        for _ in range(4):
            self.deck.append(WildCard())
            self.deck.append(WildDrawFourCard())
            
        random.shuffle(self.deck)
        
    def _deal_starting_hands(self, hand_size=7):
        """deals all player's 7 cards each from the deck."""
        for player in self.players:
            # deals 7 cards to each player
            for _ in range(hand_size):
                player.draw(self.deck)
            
    def _flip_starting_card(self):
        """Flips the top card, from the draw pile, to start the game."""
        # takes the card from the top of the deck
        top = self.deck.pop()
        # if the flipped card is a wild
        while isinstance(top, (WildCard,)):
            # 
            self.deck.insert(0, top)
            top = self.deck.pop()
        # places the card in the discard pile
        self.discard_pile.append(top)
        # changes the current color to the color of the flipped card
        self.current_color = top.color
        
    def current_player(self):
        """Returns the name of a current player."""
        return self.players[self.turn_index]
    
    def advance_turn(self):
        """After a card is place, the game moves to the next player's turn."""
        self.turn_index = (self.turn_index + self.direction) % len(self.players)
        
    def top_card(self):
        """Returns the most recently played card."""
        return self.discard_pile[-1]
    
    def reshuffle_if_needed(self):
        """Reshuffles the discard pile if there are no more cards is the draw pile."""
        if not self.deck:
            # removes the last played card from the discard pile
            top = self.discard_pile.pop()
            # new draw pile is now the previous discard pile
            self.deck = self.discard_pile
            # new discard is started with the last played card
            self.discard_pile = [top]
            # shuffles the new draw pile
            random.shuffle(self.deck)
    
    def play_turn(self):
        """Runs through the turn of a singular player."""
        player = self.current_player()
        top = self.top_card()
        # prints which player's turn it is, what the top card is, and the
        # current color
        print(f"\n{player.name}'s turn. Top card: {top} | Color in play: {self.current_color}")
        
        # if a player does not have a playable card
        if not player.has_playable_card(top, self.current_color):
            # reshuffles the discard pile if the draw pile runs out
            self.reshuffle_if_needed()
            # player draws a card
            drawn = player.draw(self.deck)
            # prints out which player had no playable card, and what they drew
            print(f"  -> {player.name} has no playable card, draws {drawn}.")
        # if the player has a playable card
        else:
            # player chooses a playable card from their hand
            card = player.choose_card(top, self.current_color)
            player.hand.remove(card)
            # prints which card the player played
            print(f"  -> {player.name} plays {card}")
            card.play(self)
            # if the card played was not a wild
            if not isinstance(card, WildCard):
                # set the current color to the color of the card played
                self.current_color = card.color
        
        # if the player has one card left
        if len(player.hand) == 1:
            # prints the player's UNO message notifying players they have one
            # card remaining
            print(f"  -> UNO! {player.name} has one card remaining!")
        
        # if the player has no more cards left
        if not player.hand:
            # prints the winning message
            print(f"\n***  UNO OUT! {player.name} wins! ***")
            # game is now over
            return True
        
        # prints the player's hand sizes after each turn
        print("  Hand sizes:", ", ".join(f"{p.name}: {len(p.hand)}" for p in self.players))
        
        # moves to the next players turn, if the game IS NOT over
        self.advance_turn()
        # slows down the speed of output in the terminal
        time.sleep(1.5)
        # game is not over
        return False
    
    def run(self):
        """Starts the game."""
        # prints the starting message
        print("Starting Uno!\n")
        game_over = False
        # while the game IS NOT over
        while not game_over:
            # player's can play their turn
            game_over = self.play_turn()