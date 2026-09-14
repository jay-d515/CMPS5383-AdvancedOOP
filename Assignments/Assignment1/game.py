import random
import time

from card import NumberCard, PlusTwoCard, SkipCard, ReverseCard, WildCard, WildDrawFourCard
from player import Player

class Game:
    COLORS = ["Red", "Yellow","Green", "Blue"]
    
    def __init__(self, player_names):
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
        for color in self.COLORS:
            self.deck.append(NumberCard(color, 0))
            for number in range(1, 10):
                self.deck.append(NumberCard(color, number))
                self.deck.append(NumberCard(color, number))
                
            for _ in range(2):
                self.deck.append(SkipCard(color))
                self.deck.append(ReverseCard(color))
                self.deck.append(PlusTwoCard(color))
                
        for _ in range(4):
            self.deck.append(WildCard())
            self.deck.append(WildDrawFourCard())
            
        random.shuffle(self.deck)
        
    def _deal_starting_hands(self, hand_size=7):
        for player in self.players:
            for _ in range(hand_size):
                player.draw(self.deck)
            
    def _flip_starting_card(self):
        top = self.deck.pop()
        while isinstance(top, (WildCard,)):
            self.deck.insert(0, top)
            top = self.deck.pop()
        self.discard_pile.append(top)
        self.current_color = top.color
        
    def current_player(self):
        return self.players[self.turn_index]
    
    def advance_turn(self):
        self.turn_index = (self.turn_index + self.direction) % len(self.players)
        
    def top_card(self):
        return self.discard_pile[-1]
    
    def reshuffle_if_needed(self):
        if not self.deck:
            top = self.discard_pile.pop()
            self.deck = self.discard_pile
            self.discard_pile = [top]
            random.shuffle(self.deck)
    
    def play_turn(self):
        player = self.current_player()
        top = self.top_card()
        print(f"\n{player.name}'s turn. Top card: {top} | Color in play: {self.current_color}")
        
        if not player.has_playable_card(top, self.current_color):
            self.reshuffle_if_needed()
            drawn = player.draw(self.deck)
            print(f"  -> {player.name} has no playable card, draws {drawn}.")
        else:
            card = player.choose_card(top, self.current_color)
            player.hand.remove(card)
            print(f"  -> {player.name} plays {card}")
            card.play(self)
            if not isinstance(card, WildCard):
                self.current_color = card.color
        
        if len(player.hand) == 1:
            print(f"  -> UNO! {player.name} has one card remaining!")
                
        if not player.hand:
            print(f"\n***  UNO OUT! {player.name} wins! ***")
            return True
        
        print("  Hand sizes:", ", ".join(f"{p.name}: {len(p.hand)}" for p in self.players))
        
        self.advance_turn()
        time.sleep(1.5)
        return False
    
    def run(self):
        print("Starting Uno!\n")
        game_over = False
        while not game_over:
            game_over = self.play_turn()