from __future__ import annotations
import railtownai_rc



class CapitalizeText(railtownai_rc[str]):

    def __init__(self, data: str):
        super().__init__()
        self.data = data

    @classmethod
    def pretty_name(cls) -> str:
        return "Capitalize Text Node"

    def invoke(self) -> str:
        return self.data.capitalize()
