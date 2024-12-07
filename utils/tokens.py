from secrets import choice
from string import digits
from string import ascii_uppercase

def generate_uppercase_code(length=5):
    return "".join(choice(ascii_uppercase) for i in range(length))

def generate_integer_code(length=5):
    return "".join(choice(digits) for i in range(length))
