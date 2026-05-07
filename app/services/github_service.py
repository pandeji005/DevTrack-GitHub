from flask import session
from github import Github
from github.InputGitTreeElement import InputGitTreeElement
from app.services.encryption_service import EncryptionService

class GithubService:
    @staticmethod
    def get_client(user):
        if not user.access_token:
            raise ValueError("User has no access token")
            
        token = EncryptionService.decrypt(user.access_token)
        return Github(token)
        
    @staticmethod
    def list_repos(user):
        g = GithubService.get_client(user)
        # Sort by updated to get most relevant repos first and speed up initial fetch
        return g.get_user().get_repos(sort='updated', direction='desc')
            
    @staticmethod
    def create_repo(user, repo_name="devtrack-logs"):
        g = GithubService.get_client(user)
        github_user = g.get_user()
        
        try:
            repo = github_user.get_repo(repo_name)
            return repo, False # False means it already existed
        except Exception:
            # Repo doesn't exist, create it
            repo = github_user.create_repo(
                repo_name, 
                description="My daily developer logs powered by DevTrack", 
                private=False,
                auto_init=True
            )
            return repo, True
            
    @staticmethod
    def push_commit(user, repo_name, file_path, content, commit_message):
        try:
            from github import InputGitAuthor
            print(f"DEBUG: Pushing commit to {repo_name}, file: {file_path}")
            g = GithubService.get_client(user)
            
            # Get user info for attribution - Use session or cache if possible
            github_user = g.get_user()
            author_name = github_user.name or github_user.login
            
            # Simple caching strategy: check if email is in session
            author_email = session.get('github_email')
            
            if not author_email:
                author_email = github_user.email
                if not author_email:
                    try:
                        # Fetch emails if public email is not set
                        emails = github_user.get_emails()
                        for e in emails:
                            if e.get('primary'):
                                author_email = e.get('email')
                                break
                    except:
                        author_email = f"{github_user.login}@users.noreply.github.com"
                
                # Cache it for this session
                if author_email:
                    session['github_email'] = author_email
            
            author = InputGitAuthor(author_name, author_email)
            
            # Clean repo name
            repo_name = repo_name.strip('/').replace('.git', '')
            repo = g.get_repo(repo_name)
            
            # Get default branch dynamically
            default_branch = repo.default_branch
            
            # Get references
            ref = repo.get_git_ref(f"heads/{default_branch}")
            base_tree = repo.get_git_tree(ref.object.sha)
            
            # Create blob
            blob = repo.create_git_blob(content, "utf-8")
            
            # Create tree element
            element = InputGitTreeElement(path=file_path, mode='100644', type='blob', sha=blob.sha)
            
            # Create new tree
            new_tree = repo.create_git_tree([element], base_tree)
            
            # Create commit with explicit author/committer
            parent = repo.get_git_commit(ref.object.sha)
            commit = repo.create_git_commit(commit_message, new_tree, [parent], author=author, committer=author)
            
            # Update ref
            ref.edit(commit.sha)
            print(f"DEBUG: Commit successful: {commit.sha} attributed to {author_email}")
            return commit.sha
        except Exception as e:
            print(f"DEBUG: GitHub Push Error: {str(e)}")
            raise e

    @staticmethod
    def get_repo_contents(user, repo_full_name, path=""):
        g = GithubService.get_client(user)
        repo = g.get_repo(repo_full_name)
        contents = repo.get_contents(path)
        return contents

    @staticmethod
    def get_recent_commits(user, repo_full_name, limit=30):
        try:
            g = GithubService.get_client(user)
            repo = g.get_repo(repo_full_name.strip('/').replace('.git', ''))
            commits = repo.get_commits()
            
            result = []
            for i, commit in enumerate(commits):
                if i >= limit: break
                result.append({
                    'sha': commit.sha,
                    'message': commit.commit.message,
                    'committed_at': commit.commit.author.date,
                    'author_email': commit.commit.author.email
                })
            return result
        except Exception as e:
            print(f"DEBUG: GitHub Fetch Error: {str(e)}")
            return []
