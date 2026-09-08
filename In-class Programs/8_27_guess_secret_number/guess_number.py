import random

secret = random.randint(1, 10)
print(secret)

for i in range(3):
    guess = int(input("Guess the secret number: "))
    if guess == secret:
        print("Way to go, you guessed the correct number!")
        break
    elif guess < secret:
        print("Too low, try again.")
    else:
        print("Too high, try again.")