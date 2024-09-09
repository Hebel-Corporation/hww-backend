import random


def generate_subcription_code() -> str :

    leters = "abcdefghijklmnopkrstuvwxyz"
    numbers = "0123456789"

    use_for = leters + leters.upper() + numbers
    length_for_pass = 10

    return "".join(random.sample(use_for, length_for_pass))


