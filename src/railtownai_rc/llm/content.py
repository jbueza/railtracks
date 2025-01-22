from __future__ import annotations

from typing import Generic, TypeVar, Union, List, Any, Dict, AnyStr

from pydantic import BaseModel
from abc import ABC, abstractmethod


####################################################################################################
# Simple helper Data Structures for common responses #
####################################################################################################
class ToolCall(BaseModel):
    identifier: str
    name: str
    arguments: Dict[str, Any]


class ToolResponse(BaseModel):
    identifier: str
    name: str
    result: AnyStr


Content = Union[str, List[ToolCall], ToolResponse, BaseModel]
