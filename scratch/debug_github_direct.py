from github import Github
from cryptography.fernet import Fernet
import sqlite3
import os

# Manual decryption test
db_path = r"d:\pythonFSD\Sample projects\DevTrack\instance\devtrack.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute("SELECT access_token FROM users LIMIT 1")
row = cursor.fetchone()
conn.close()

if not row:
    print("No token in DB")
    exit()

encrypted_token = row[0]
print(f"Encrypted token length: {len(encrypted_token)}")

# Use the key from .env
key = "YtgZl8uuqJb2BlaEx4SQhT334c79-elUGHDU8-hASGU="
cipher = Fernet(key.encode())

try:
    token = cipher.decrypt(encrypted_token.encode()).decode()
    print("Decryption successful")
    
    g = Github(token)
    user = g.get_user()
    print(f"Connected as: {user.login}")
    
    print("Fetching first 5 repos...")
    for repo in user.get_repos(sort='updated', direction='desc'):
        print(f"Repo: {repo.name}")
        break
    print("Success")
except Exception as e:
    print(f"Error: {str(e)}")
