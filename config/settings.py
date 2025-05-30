import os
import streamlit as st
from typing import Optional
from dotenv import load_dotenv

# Carregar variáveis do arquivo .env
load_dotenv()


class Settings:
    def __init__(self):
        # Primeiro tenta pegar do .env (desenvolvimento local)
        self.api_key: Optional[str] = os.getenv("API_KEY")

        # Se não encontrar, tenta pegar dos secrets do Streamlit
        if not self.api_key:
            try:
                self.api_key = st.secrets["API_KEY"]
            except (KeyError, FileNotFoundError, AttributeError):
                self.api_key = None

        self.debug: bool = os.getenv("DEBUG", "False").lower() == "true"

    def validate(self):
        if not self.api_key:
            raise ValueError("API_KEY não configurada. Verifique as variáveis de ambiente ou secrets do Streamlit.")


settings: Settings = Settings()