import time
import threading
# class Drink:
#     def __init__(self, name):
#         pass


class Barista(threading.Thread):
    def __init__(self, name):
        super().__init__
        self.name = name 
    
    def make_coffee(self):
        print(f"{self.name} is making coffee")

    def run(self):
        while True:
            self.make_coffee()
            time.sleep(.5)
            
class Manager:
    def __init__(self):
        self.barista1 = Barista("John")
        self.barista2 = Barista("Alice")
    
    def main(self):
        self.barista1.start()
        self.barista2.start()
        
        self.barista1.join()
        self.barista2.join()
        
boss = Manager()
boss.main()