from dotenv import load_dotenv, find_dotenv
import os

print(f"Finding .env: {find_dotenv()}")
loaded = load_dotenv()
print(f"load_dotenv() returned: {loaded}")
print(f"GOOGLE_API_KEY in os.environ: {'GOOGLE_API_KEY' in os.environ}")

if 'GOOGLE_API_KEY' in os.environ:
    val = os.environ['GOOGLE_API_KEY']
    print(f"Key length: {len(val)}")
    print(f"Key start: {val[:5]}...")
else:
    print("Printing all keys:")
    for k in os.environ:
        if 'API' in k or 'KEY' in k:
            print(k)
