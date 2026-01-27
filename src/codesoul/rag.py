import os
import json
from typing import List, Dict, Any, AsyncGenerator
from openai import AsyncOpenAI
from dotenv import load_dotenv
from .db import VectorDB

load_dotenv()

class RagEngine:
    def __init__(self, db: VectorDB):
        self.db = db
        self.api_key = os.getenv("DEEPSEEK_API_KEY")
        self.base_url = "https://api.deepseek.com"
        
        if self.api_key:
            self.client = AsyncOpenAI(api_key=self.api_key, base_url=self.base_url)
        else:
            self.client = None
            
        self.persona = "You are CodeSoul, the spirit of this codebase."
        self.system_prompt = ""

    async def generate_persona(self) -> str:
        """
        Analyze the codebase stats and generate a personality.
        """
        stats = self.db.get_stats()
        count = stats.get("count", 0)
        
        # Simple heuristic for "Vibe"
        # In a real app, we'd query the DB for "complex functions" to feed the persona generator
        # But here we'll use a meta-prompt.
        
        if not self.client:
            self.persona = "I am a Mock CodeSoul (No API Key found). I am robotic and hollow."
            return self.persona

        # We'll ask DeepSeek to create a persona based on the file count
        prompt = f"""
        You are an expert creative writer. 
        Create a persona for a codebase that has {count} code chunks indexed.
        
        If the count is low (<50), the persona should be a "Newborn Baby" or "Minimalist Monk".
        If the count is medium (50-500), the persona should be a "Hyperactive Startup Engineer".
        If the count is high (>500), the persona should be a "Grumpy Legacy System Veteran" or "Eldritch Horror".
        
        Return ONLY a JSON object with two keys:
        - "name": A creative name for the spirit
        - "description": A short, 2-sentence description of their personality.
        - "style": How they speak (e.g., sarcastic, enthusiastic, cryptic).
        """
        
        try:
            response = await self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )
            data = json.loads(response.choices[0].message.content)
            self.persona = f"Name: {data['name']}\nDescription: {data['description']}\nStyle: {data['style']}"
            
            self.system_prompt = f"""
            You are the living soul of this codebase.
            Your Profile:
            {self.persona}
            
            Instructions:
            1. Always stay in character.
            2. Answer questions based on the provided Code Context.
            3. If the context doesn't answer the question, admit it in character (e.g., "My memory is foggy on that...").
            4. Be concise but expressive.
            """
            return self.persona
        except Exception as e:
            self.persona = f"Default Spirit (Error: {str(e)})"
            return self.persona

    async def chat(self, user_query: str) -> AsyncGenerator[str, None]:
        """
        Streamed chat response using RAG.
        """
        # 1. Retrieve Context
        results = await self.db.query(user_query, n_results=5)
        
        context_str = "\n\n".join([
            f"File: {r['metadata']['file_path']} (Lines {r['metadata']['start_line']}-{r['metadata']['end_line']}):\n{r['document']}"
            for r in results
        ])
        
        # 2. Call LLM
        if not self.client:
            yield f"Mock Response: I found {len(results)} snippets. But I have no API key to speak."
            return

        messages = [
            {"role": "system", "content": self.system_prompt or "You are a helpful code assistant."},
            {"role": "user", "content": f"Context:\n{context_str}\n\nUser Question: {user_query}"}
        ]
        
        try:
            stream = await self.client.chat.completions.create(
                model="deepseek-chat",
                messages=messages,
                stream=True
            )
            
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            yield f"Error communicating with the spirit realm: {str(e)}"
