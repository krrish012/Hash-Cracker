import hashlib

word = input("Enter the word you want to hash:")

real_hash = hashlib.sha256(word.encode('utf-8')).hexdigest()

print(f"The SHA-256 hash is: {real_hash}")