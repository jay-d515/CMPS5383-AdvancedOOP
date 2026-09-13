from Card import Card, NumberCard, PlusTwoCard, SkipCard, ReverseCard, WildCard, WildDrawFourCard
import random

class Player:
    def __init__(self, name, hand):
        self.name = name
        self.hand = []
        
    def draw(self, deck):
        if deck:
            card = deck.pop()
            self.hand.append(card)
            return card
        else:
            return None   
    def has_playable_card(self, current_card, current_color):
        return any(c.matches(current_card, current_color) for c in self.hand)
    
    def choose_card(self, current_card, current_color):
        for card in self.hand:
            if card.matches(current_card, current_color):
                return card
        return None
    
    def choose_color(self):
        counts = {}
        for c in self.hand:
            if c != "Wild":
                counts[c.color] = counts.get(c.color, 0) + 1   
        if counts:
            return max(counts, key=counts.get)
        return random.choice(["Red", "Yellow", "Green", "Blue"])
    
    def __str__(self):
        return self.name
    
    