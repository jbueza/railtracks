from __future__ import annotations
# TODO import railtown_rc here



class CapitalizeText([str]):

    def __init__(self, data: str):
        super().__init__()
        self.data = data

    @classmethod
    def pretty_name(cls) -> str:
        return "Capitalize Text Node"

    def invoke(self) -> str:
        return self.data.capitalize()
