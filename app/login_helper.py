"""
File to validate usernames and passwords
"""

import hashlib
import os
import random
import string

# global variables to control password requirements
SPECIAL_CHARS = ["!", "@", "#", "$", "%", "^", "&", "*"]
SPEC_REQ = 0
LOWER_REQ = 0
UPPER_REQ = 0
NUM_REQ = 2
MIN_LEN = 8
MAX_LEN = 25

SALT_LEN = 40


def is_good_user(strin):
    """
    Checks if the username does not have white space
    and stops SQL injection
    :param strin:
    :return:
    """
    if strin.isalnum():
        return True
    else:
        return False


def is_good_pass(strin):
    """
    Validates the password (8-25 Char, one upper one lower, special char)
    :param strin: the password string
    :return: True or False
    """
    upper_count = 0
    lower_count = 0
    spec_count = 0
    num_count = 0
    if len(strin) < MIN_LEN or len(strin) > MAX_LEN:
        return False
    for c in strin:
        if c.islower():
            lower_count += 1
        elif c.isupper():
            upper_count += 1
        elif c.isdigit():
            num_count += 1
        else:
            for tes in SPECIAL_CHARS:
                if c == tes:
                    spec_count += 1
    if upper_count >= UPPER_REQ and lower_count >= LOWER_REQ and spec_count >= SPEC_REQ and num_count >= NUM_REQ:
        return True
    else:
        return False


def gen_pass():
    """
    Generates a secure password of length 25 that contains the required characters
    :return:
    """
    random_source = string.ascii_letters + string.digits
    for c in SPECIAL_CHARS:
        random_source += c
    password = random.choice(string.ascii_lowercase)
    password += random.choice(string.ascii_uppercase)
    password += random.choice(string.digits)
    password += random.choice(SPECIAL_CHARS)

    for i in range(MAX_LEN-4):
        password += random.choice(random_source)

    password_list = list(password)
    random.SystemRandom().shuffle(password_list)
    password = ''.join(password_list)
    return password


def hash_pw(plain_text) -> str:
    """
    given the plain texts hashes it in sha-256 and returns it
    :param plain_text:
    :return:
    """
    salt = os.urandom(SALT_LEN)
    salt = str(salt)
    salt = salt[:SALT_LEN]
    hashable = salt + plain_text  # concatenate salt and plain_text
    hashable = hashable.encode('utf-8')  # convert to bytes
    this_hash = hashlib.sha256(hashable).hexdigest()  # hash and hexdigest
    return salt + this_hash  # prepend hash and return


def authenticate(stored, plain_text, salt_length=SALT_LEN) -> bool:
    """
    Authenticate by comparing stored and new hashes.
    :param stored: str (salt + hash retrieved from database)
    :param plain_text: str (user-supplied password)
    :param salt_length: int
    :return: bool
    """
    salt = stored[:salt_length]  # extract salt from stored value
    stored_hash = stored[salt_length:]  # extract hash from stored value
    hashable = salt + plain_text  # concatenate hash and plain text
    hashable = hashable.encode('utf-8')  # convert to bytes
    this_hash = hashlib.sha256(hashable).hexdigest()  # hash and digest
    return this_hash == stored_hash  # compare
