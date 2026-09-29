import threading
import time

# a better design the stock is responsible for the locks
class Stock:
    def __init__(self, beans, milk):
        self.beans = beans
        self.milk = milk

        self.beans_lock = threading.Lock()
        self.milk_lock = threading.Lock()

    def get_beans(self, amount):
        self.beans_lock.acquire()

        if self.beans >= amount:
            self.beans -= amount
            print(f"Beans remaining: {self.beans}")

        self.beans_lock.release()

    def get_milk(self, amount):
        self.milk_lock.acquire()

        if self.milk >= amount:
            self.milk -= amount
            print(f"Milk remaining: {self.milk}")

        self.milk_lock.release()


class Barista(threading.Thread):

    def __init__(self, name, stock):
        super().__init__()
        self.name = name
        self.stock = stock

    def make_coffee(self):

        print(f"{self.name} is making coffee")

        self.stock.get_beans(10)
        self.stock.get_milk(10)

        time.sleep(1)

        print(f"{self.name} finished coffee")

    def run(self):
        for i in range(3):
            self.make_coffee()


class Manager:

    def __init__(self):
        self.stock = Stock(100, 100)

        self.barista1 = Barista("John", self.stock)
        self.barista2 = Barista("Alice", self.stock)

    def main(self):

        self.barista1.start()
        self.barista2.start()

        self.barista1.join()
        self.barista2.join()

        print("Coffee shop closed")
        print("Beans:", self.stock.beans)
        print("Milk:", self.stock.milk)


boss = Manager()
boss.main()