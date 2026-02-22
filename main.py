import hashlib
import os
import concurrent.futures
import time
import itertools

salt = input("Enter salt: ")

def yield_chunks(file_object, chunk_size):
    # This loop runs forever until the file is empty
    while True:
        # islice grabs exactly 'chunk_size' number of lines from the file
        chunk = list(itertools.islice(file_object, chunk_size))
        
        if not chunk:
            break # The file is empty, stop the loop
            
        # Yield acts like 'return', but it remembers where it paused!
        yield [line.strip() for line in chunk]

# 1. The Worker Function (This is what each core will run independently)
def crack_chunk(word_list, target_hash):
    for word in word_list:
        combined_word = word + salt 
        if hashlib.sha256(combined_word.encode('utf-8')).hexdigest() == target_hash:
            return word
    return None

# 2. The Windows Safety Lock
if __name__ == '__main__':
    
    target_hash = input("Enter the SHA-256 hash to crack: ").strip()

    cores = os.cpu_count()
    print(f"\n[!] Detected {cores} CPU cores.")
    print("[!] Launching lazy-loading multi-core attack...\n")
    
    start_time = time.time()
    found_password = None

    # 1. Open the file AND the multi-core executor
    with open("passwords.txt", "r", encoding="utf-8", errors="ignore") as file:
        with concurrent.futures.ProcessPoolExecutor(max_workers=cores) as executor:
            
            # 2. The Generator Valve: Pull 1.6 million words into RAM at a time
            BATCH_SIZE = 1_600_000 
            
            for mega_batch in yield_chunks(file, BATCH_SIZE):
                
                # 3. Split the mega_batch among your cores
                chunk_size = len(mega_batch) // cores
                if chunk_size == 0: chunk_size = 1 # Failsafe for tiny files
                
                chunks = []
                for i in range(cores):
                    start_index = i * chunk_size
                    if i == cores - 1:
                        end_index = len(mega_batch)
                    else:
                        end_index = start_index + chunk_size
                    
                    chunks.append(mega_batch[start_index:end_index])
                
                # 4. Feed the chunks to the cores
                futures = [executor.submit(crack_chunk, chunk, target_hash) for chunk in chunks if chunk]
                
                # 5. Check if any core found the password in this batch
                for future in concurrent.futures.as_completed(futures):
                    result = future.result()
                    if result is not None:
                        found_password = result
                        break # Break out of the futures loop
                
                if found_password:
                    # Cancel any remaining work in this batch to save CPU power
                    for f in futures: f.cancel()
                    break # Break out of the main generator loop
                
                # Optional: Print a status update so you know it's not frozen on big files!
                print("[*] Scanned 1.6 million words... pulling next batch...")

    end_time = time.time()

    # 6. The Results
    if found_password:
        print(f"\n[+] SUCCESS! Password found: {found_password}")
    else:
        print("\n[-] Password not found in the dictionary.")
        
    print(f"Time taken: {end_time - start_time:.4f} seconds.")