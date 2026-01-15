from app.schemas.text_reports import LLMResponse


class LLMService:
    _instance = None
    _initialized = False
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, model_name="TinyLlama/TinyLlama-1.1B-Chat-v1.0"):
        if not self._initialized:
            self._initialized = True
    
    def generate_response(self, user_input):
        return LLMResponse(
            text="ypur_text: " + user_input,
            time=0,
        )
