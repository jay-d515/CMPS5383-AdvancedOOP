import threading
import time


class Stock:
    def __init__(self, beans, milk):
        self.beans = beans
        self.milk = milk

        self.beans_lock = threading.Lock()
        self.milk_lock = threading.Lock()


class AliceBarista(threading.Thread):

    def __init__(self, name, stock):
        super().__init__()
        self.name = name
        self.stock = stock

    def make_coffee(self):

        self.stock.beans_lock.acquire()

        print(f"{self.name} locked BEANS")
        self.stock.beans -= 10

        time.sleep(1)

        print(f"{self.name} waiting for MILK")
        self.stock.milk_lock.acquire()

        print(f"{self.name} locked MILK")
        self.stock.milk -= 10

        self.stock.milk_lock.release()
        self.stock.beans_lock.release()

        print(f"{self.name} finished coffee")

    def run(self):
        self.make_coffee()


class JohnBarista(threading.Thread):

    def __init__(self, name, stock):
        super().__init__()
        self.name = name
        self.stock = stock

    def make_coffee(self):

        self.stock.milk_lock.acquire()

        print(f"{self.name} locked MILK")
        self.stock.milk -= 10

        time.sleep(1)

        # John tries to lock BEANS
        print(f"{self.name} waiting for BEANS")
        self.stock.beans_lock.acquire()

        print(f"{self.name} locked BEANS")
        self.stock.beans -= 10

        self.stock.beans_lock.release()
        self.stock.milk_lock.release()

        print(f"{self.name} finished coffee")

    def run(self):
        self.make_coffee()


class Manager:

    def __init__(self):
        self.stock = Stock(100, 100)

        self.alice = AliceBarista("Alice", self.stock)
        self.john = JohnBarista("John", self.stock)

    def main(self):

        self.alice.start()
        self.john.start()

        self.alice.join()
        self.john.join()


boss = Manager()
boss.main()