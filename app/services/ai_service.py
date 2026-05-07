import os
import requests
from flask import current_app

class AIService:
    @staticmethod
    def get_api_key():
        api_key = current_app.config.get('GROQ_API_KEY')
        if not api_key:
            raise ValueError("GROQ_API_KEY is not configured")
        return api_key

    @staticmethod
    def _call_groq(messages, model="llama-3.1-8b-instant", temperature=0.5, max_tokens=400):
        api_key = AIService.get_api_key()
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code != 200:
            raise Exception(f"Groq API Error: {response.text}")
            
        return response.json()['choices'][0]['message']['content'].strip()

    @staticmethod
    def generate_smart_commit(tasks, log_content):
        task_list = "\n".join([f"- [{t.type}] {t.title}" for t in tasks])
        
        prompt = f"""
You are an expert developer. Generate a professional 'Conventional Commit' message based on the following daily work.
Keep it strictly to one subject line (under 50 chars) and an optional short body. Do not output anything else.

Tasks completed:
{task_list}

Daily Log Notes:
{log_content}
"""
        messages = [{"role": "user", "content": prompt}]
        return AIService._call_groq(messages, temperature=0.3, max_tokens=150).replace('`', '')

    @staticmethod
    def chat_with_data(query, recent_data, history=None):
        system_prompt = f"""
You are DevTrack, a helpful AI assistant built into a developer's productivity dashboard.
Answer the user's question based on their recent activity data below. Be concise, friendly, and helpful.

User's Recent Activity Context:
{recent_data}
"""
        messages = [{"role": "system", "content": system_prompt}]
        
        if history:
            for msg in history:
                messages.append(msg)
                
        messages.append({"role": "user", "content": query})
        
        return AIService._call_groq(messages)
