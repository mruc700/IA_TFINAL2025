import requests
from config import Config

class OllamaClient:
    def __init__(self):
        self.host = Config.OLLAMA_HOST
        self.model = 'llama3:8b'  # Usar Llama 3:8b

    def generate_response(self, prompt, context=""):
        """Genera una respuesta usando Ollama."""
        url = f"{self.host}/api/generate"
        
        payload = {
            "model": self.model,
            "prompt": f"{context}\n\nUsuario: {prompt}\nAsistente:",
            "stream": False,
            "options": {
                "temperature": 0.3,  # Reducir temperatura para respuestas más consistentes y menos creativas
                "top_p": 0.9,
                "num_predict": 200  # Limitar longitud para evitar respuestas demasiado largas
            }
        }
        
        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            result = response.json()
            return result.get('response', '').strip()
        except requests.exceptions.RequestException as e:
            return f"Error al comunicarse con Ollama: {str(e)}"