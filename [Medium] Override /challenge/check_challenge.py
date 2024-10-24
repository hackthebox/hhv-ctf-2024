from config import *
from password_db import *
import hashlib

#[0, 163, 163, 14, 93, 198, 187, 162, 32, 171, 216, 135, 177, 74, 183, 96, 63, 0]
def check_challenge(flash):
    mem_hash = flash.memory[SECRET_POS:SECRET_POS+18]
    print(mem_hash)

    if mem_hash[0] == 0 and mem_hash[-1] == 0:
        print('correct bounds')
        mem_hash = flash.memory[SECRET_POS+1:SECRET_POS+17]


    # Hash the secret value using SHA-256
    hash_object = hashlib.md5()
    hash_object.update(SECRET.encode())  # Convert secret to bytes and hash it
    hashed_value = list(hash_object.digest())  # Get the hash as bytes

   
    if mem_hash == hashed_value:
        print('hash unchanged!')
        create_table(DB_NAME)
        
    else:
        print('hash changed!')
        print('Updating DB!')
        insert_entry(DB_NAME, str(mem_hash))


            
    return True
