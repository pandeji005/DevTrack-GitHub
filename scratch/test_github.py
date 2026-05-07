from app import create_app
from app.models import User, db
from app.services.github_service import GithubService
import os

app = create_app()
with app.app_context():
    user = User.query.first()
    if not user:
        print("No user found")
    else:
        print(f"Testing GitHub for user: {user.username}")
        try:
            repos = GithubService.list_repos(user)
            print("Successfully connected to GitHub")
            count = 0
            for r in repos:
                print(f"- {r.name}")
                count += 1
                if count >= 5: break
            print(f"Total repos listed: {count}")
        except Exception as e:
            print(f"GitHub Error: {str(e)}")
