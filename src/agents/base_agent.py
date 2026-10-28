from abc import ABC, abstractmethod
from src.state.prd_schema import PRDExtraction
from src.state.arch_state import ArchitectureOutput

class BaseAgent(ABC):
    @abstractmethod
    def process(self, prd: PRDExtraction, arch: ArchitectureOutput) -> None:
        """Mutates the shared ArchitectureOutput state based on PRDExtraction."""
        pass