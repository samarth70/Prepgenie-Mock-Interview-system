"""
Model Manager - Using Groq SDK Directly (NO AgentScope)
FREE Models: Groq (Qwen 2.5 32B - FREE & FAST!)
"""

import os
from groq import Groq

class GroqClient:
    """Simple Groq client wrapper."""
    
    def __init__(self):
        self.client = None
        self.initialize()
    
    def initialize(self):
        """Initialize Groq client."""
        api_key = os.getenv("GROQ_API_KEY")
        
        if api_key:
            try:
                self.client = Groq(api_key=api_key)
                print("✅ Groq client initialized (Qwen 2.5 32B - FREE & FAST!)")
            except Exception as e:
                print(f"❌ Groq initialization failed: {e}")
        else:
            print("⚠️ Groq: API key not configured")
            print("💡 Get FREE key: https://console.groq.com/keys")
    
    def generate(self, prompt: str, system_prompt: str = "You are a helpful assistant.", 
                 temperature: float = 0.6, max_tokens: int = 2048) -> str:
        """Generate text using Groq."""
        if not self.client:
            raise Exception("Groq client not initialized")
        
        completion = self.client.chat.completions.create(
            model="qwen-2.5-32b",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=0.95
        )
        
        return completion.choices[0].message.content

# Global client instance
groq_client = None

def get_groq_client() -> GroqClient:
    """Get or create Groq client."""
    global groq_client
    if groq_client is None:
        groq_client = GroqClient()
    return groq_client
