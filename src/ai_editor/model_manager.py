"""ModelManager – downloads and runs flan-t5-base for AI editing."""
import os
from src.utils.constants import APPDATA_DIR

MODELS_DIR = os.path.join(APPDATA_DIR, 'models')
MODEL_NAME = "google/flan-t5-base"


class ModelManager:
    def __init__(self, progress_callback=None):
        self._progress_callback = progress_callback  # callable(message: str)
        self._model = None
        self._tokenizer = None

    # ------------------------------------------------------------------
    def _emit(self, msg: str):
        if self._progress_callback:
            self._progress_callback(msg)

    # ------------------------------------------------------------------
    def check_model_available(self) -> bool:
        """Return True if the model is already cached locally."""
        local_path = os.path.join(MODELS_DIR, MODEL_NAME.replace('/', '--'))
        return os.path.isdir(local_path)

    # ------------------------------------------------------------------
    def load_model(self):
        """Download (first time) and load the model into memory."""
        try:
            from transformers import T5ForConditionalGeneration, T5Tokenizer
        except ImportError:
            raise ImportError("transformers library is required for AI editing.")

        os.makedirs(MODELS_DIR, exist_ok=True)
        cache_dir = MODELS_DIR

        self._emit(f"Loading {MODEL_NAME} …")
        self._tokenizer = T5Tokenizer.from_pretrained(MODEL_NAME, cache_dir=cache_dir)
        self._emit("Tokenizer loaded. Loading model weights …")
        self._model = T5ForConditionalGeneration.from_pretrained(MODEL_NAME, cache_dir=cache_dir)
        self._emit("Model ready.")

    # ------------------------------------------------------------------
    def run_prompt(self, text: str, instruction: str) -> str:
        """Apply *instruction* to *text* and return the result."""
        if self._model is None or self._tokenizer is None:
            self.load_model()

        prompt = f"{instruction}: {text}"
        inputs = self._tokenizer(
            prompt,
            return_tensors="pt",
            max_length=512,
            truncation=True,
        )
        outputs = self._model.generate(
            **inputs,
            max_new_tokens=512,
            num_beams=4,
            early_stopping=True,
        )
        result = self._tokenizer.decode(outputs[0], skip_special_tokens=True)
        return result

    # ------------------------------------------------------------------
    def unload_model(self):
        self._model = None
        self._tokenizer = None
