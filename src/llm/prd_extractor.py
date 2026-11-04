
import json

from src.llm.gemini_client import GeminiClient
from src.state.prd_schema import PRDExtraction


class GeminiPRDExtractor:
    """Uses Gemini to convert natural-language PRDs into structured data."""

    def __init__(self):
        self.gemini = GeminiClient()

    def extract(self, raw_prd: str) -> PRDExtraction:
        prompt = f"""
You are an expert software requirements analyst.

Analyze the following Product Requirements Document (PRD).

Extract these fields:
1. project_name
2. description
3. entities, including their names, database fields and relationships
4. expected_rps (integer)
5. max_latency_ms (integer)
6. availability_sla (string)
7. compliance (list of strings)
8. realtime_features (boolean)
9. extra_nfrs (dictionary of string keys and values)

Rules:
- Extract only information supported by the PRD.
- Do not invent entities or requirements.
- If a numerical requirement is absent, use these defaults:
  expected_rps: 500
  max_latency_ms: 200
  availability_sla: "99.9%"
- Return valid JSON only.
- Each entity must contain name, fields, relations and description.
- Do not include Markdown code fences.

PRD:
{raw_prd}
"""

        response = self.gemini.generate(prompt)

        # Handle accidental Markdown code fences.
        response = response.strip()
        if response.startswith("```"):
            response = response.split("\n", 1)[1]
            response = response.rsplit("```", 1)[0].strip()

        data = json.loads(response)

        return PRDExtraction.model_validate(data)
