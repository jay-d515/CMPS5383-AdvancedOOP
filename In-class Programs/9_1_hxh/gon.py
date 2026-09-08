
import random
import time

class Character:
    def __init__(self, name, health, attack_power):
            self.name = name
            self.health = health
            self.attack_power = attack_power
        
    def heal(self, extra_health_points):
        self.health = self.heath + extra_health_points
        
    def attack(self):
        return self.attack_power + random.randint(-5, 5)
    
    def special_attack(self):
        pass
            
    def apply_damage(self, damage):
        self.health = self.health - damage
            
    def is_dead(self):
        if self.health == 0:
            return True
        return False
    
    def show_status(self):
        print(self.name)
        print(self.health)
        print(self.attack_power)

class Gon(Character):
    def __init__(self):
        super().__init__("Gon", 100, 20)
        
    def special_attack(self):
        print("This is Gon's special attack!")
        return self.attack_power + random.randint(1, 5)

class Hisoka(Character):
    def __init__(self):
        super().__init__("Hisoka", 120, 40)
        self.maneuver = True
        
    def special_attack(self):
        print("This is Hisoka's special attack!")
        return self.attack_power + random.randint(1, 5)
        
    def is_dodging(self):
        return self.maneuver
    
class Game:
    def __init__(self, gon, hisoka):
        self.gon = gon
        self.hisoka = hisoka
        
    def gons_turn(self):
        # give gon a turn to attack
        option = input("Option: ")
                    
        damage = 0
        if option == "1":      
            damage = self.gon.attack()
        elif option == "2":
            damage = self.gon.special_attack()
        else:
            print("You missed your chance")
                    
        # calc damage
        self.hisoka.apply_damage(damage)
        
    def start(self):
        while True:
            
            self.gons_turn()
            
            self.hisoka.show_status()
            
            # check if hisoka is alive
            if self.hisoka.is_dead():
                print("Hisoka is dead! Gon wins!") 
                # end the game
                break
            
            time.sleep(1)
            
            hisoka_option = random.choice(["1"], ["2", "3"])
    
            damage = 0
            if hisoka_option == "1":      
                damage = self.hisoka.attack()
            elif hisoka_option == "2":
                damage = self.hisoka.special_attack()
            else:
                print("Hisoka missed their chance")
            
            # calc damage
            self.gon.apply_damage(damage)
            #print (f"Hisoka attacks Gon for {damage} damage!")
            
            # check if gon is dead
            if self.gon.is_dead():
                print("Gon is dead! Hisoka wins!") 
                # end the game
                break
        print("Game Over!")
       
        
gon = Gon()
hisoka = Hisoka()

game = Game(gon, hisoka)
game.start()