import random

from card import WildCard

class Player:
    def __init__(self, name):
        self.name = name
        self.hand = []
        
    def draw(self, deck):
        if deck:
            card = deck.pop()
            self.hand.append(card)
            return card
        return None
      
    def has_playable_card(self, current_card, current_color):
        return any(c.matches(current_card, current_color) for c in self.hand)
    
    def choose_card(self, current_card, current_color):
        for card in self.hand:
            if not isinstance(card, WildCard) and card.matches(current_card, current_color):
                return card
        
        for card in self.hand:
            if isinstance(card, WildCard):
                return card
        return None
    
    def choose_color(self):
        counts = {}
        for c in self.hand:
            if c.color != "Wild":
                counts[c.color] = counts.get(c.color, 0) + 1   
        if counts:
            return max(counts, key=counts.get)
        return random.choice(["Red", "Yellow", "Green", "Blue"])
    
    def __str__(self):
        return self.name
    
    