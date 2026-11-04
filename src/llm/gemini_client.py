
import os
import time

from dotenv import load_dotenv
from google import genai

load_dotenv()

class GeminiClient:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        model = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")

        if not api_key:
            raise ValueError("GEMINI_API_KEY is missing. Check your .env file.")

        self.model = model
        self.client = genai.Client(api_key=api_key)

    def generate(self, prompt: str) -> str:
        max_attempts = 3

        for attempt in range(1, max_attempts + 1):
            try:
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=prompt,
                )

                if not response.text:
                    raise RuntimeError("Gemini returned an empty response.")

                return response.text

            except Exception as error:
                if attempt == max_attempts:
                    raise RuntimeError(
                        f"Gemini failed after {max_attempts} attempts: {error}"
                    ) from error

                delay = 2 ** attempt

                print(
                    f"Gemini request failed (attempt {attempt}/{max_attempts}). "
                    f"Retrying in {delay} seconds..."
                )

                time.sleep(delay)
