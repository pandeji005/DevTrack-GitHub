# DevTrack OS 🚀

**DevTrack OS** is a premium, minimalist developer operating system designed to streamline your workflow, track your daily growth, and automate your GitHub documentation. Built for high-velocity developers who value focus and structure.



## ✨ Key Features

- **Hyper-Minimalist Workspace**: A clean, distraction-free interface designed to reduce cognitive load.
- **GitHub-Native Integration**: Automatic repository discovery and log publishing directly to your GitHub account.
- **Intelligent Task Engine**: Manage features, bugs, and learning goals with a strictly logical flow (Backlog → In Progress → Done).
- **Daily Journaling with "Magic" Auto-Fill**: Automatically generate professional work summaries by scanning your daily commits and completed tasks.
- **Real-Time Analytics**: Visualize your productivity with GitHub-style heatmaps, streak counters, and velocity charts.
- **AI Copilot**: A context-aware assistant to help you navigate your projects and tasks.

## 🛠️ Tech Stack

- **Backend**: Python / Flask
- **Database**: SQLite (SQLAlchemy ORM)
- **Real-Time**: Flask-SocketIO
- **Frontend**: Jinja2, Tailwind CSS (CDN), Vanilla JavaScript
- **Auth**: GitHub OAuth 2.0
- **AI**: Groq API Integration

## 🚀 Quick Start

### 1. Prerequisites
- Python 3.8+
- GitHub Account (for OAuth)
- Groq API Key (optional, for AI features)

### 2. Installation
```bash
# Clone the repository
git clone https://github.com/pandeji005/DevTrack-GitHub.git
cd DevTrack-GitHub

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration
Create a `.env` file in the root directory:
```env
FLASK_SECRET_KEY=your_secret_key
FLASK_ENV=development
GITHUB_CLIENT_ID=your_github_client_id
GITHUB_CLIENT_SECRET=your_github_client_secret
GITHUB_CALLBACK_URL=http://localhost:5000/auth/github/callback
DATABASE_URL=sqlite:///devtrack.db
GROQ_API_KEY=your_groq_api_key
ENCRYPTION_KEY=your_encryption_key
```

### 4. Run the App
```bash
python run.py
```
Visit `http://localhost:5000` to start your session.

## 📂 Project Structure

- `app/`: Main application package
  - `models/`: Database models (User, Task, Log, etc.)
  - `routes/`: Blueprint-based route handlers
  - `services/`: Core logic (GitHub API, Encryption)
  - `templates/`: Jinja2 templates
  - `static/`: CSS and client-side JS
- `run.py`: Application entry point

## 🤝 Contributing

Contributions are what make the open-source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request


---

Built with ❤️ by [Amogh Deshpande](https://github.com/pandeji005)
