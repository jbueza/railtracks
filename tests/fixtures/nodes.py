from __future__ import annotations
from src.railtownai_rc.nodes.nodes import Node



class CapitalizeText(Node[str]):

    def __init__(self, data: str):
        super().__init__()
        self.data = data

    @classmethod
    def pretty_name(cls) -> str:
        return "Capitalize Text Node"

    def invoke(self) -> str:
        return self.data.capitalize()
