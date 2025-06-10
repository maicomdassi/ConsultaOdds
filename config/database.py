from supabase import create_client, Client
import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

class Database:
    _instance: Optional[Client] = None
    
    @classmethod
    def get_client(cls) -> Client:
        """Retorna uma instância única do cliente Supabase"""
        if cls._instance is None:
            url = os.getenv("NEXT_PUBLIC_SUPABASE_URL", "https://zpauppwkolrbbyzszyrf.supabase.co")
            key = os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InpwYXVwcHdrb2xyYmJ5enN6eXJmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDg5MDkwMTYsImV4cCI6MjA2NDQ4NTAxNn0.pPXnnY7m9QDoTPLwOv5RvIbllRgDqccOxHinVMN2afE")
            cls._instance = create_client(url, key)
        return cls._instance
    
    @classmethod
    def reset_client(cls):
        """Reseta a conexão com o banco"""
        cls._instance = None

# Instância global para uso direto
supabase = Database.get_client()
