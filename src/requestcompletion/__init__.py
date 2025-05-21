#   -------------------------------------------------------------
#   Copyright (c) Railtown AI. All rights reserved.
#   Licensed under the MIT License. See LICENSE in project root for information.
#   -------------------------------------------------------------
"""Railtown AI Request Completion Framework for building resilient agentic systems"""

from __future__ import annotations
from dotenv import load_dotenv

__all__ = [
    "Node",
    "library",
    "Runner",
    "call",
    "submit" "stream",
    "ExecutionInfo",
    "ExecutorConfig",
    "llm",
    "set_config",
    "set_streamer",
]


from .nodes import library
from .nodes.nodes import Node
from .interaction.call import call, stream, submit
from .run import Runner, ExecutionInfo, set_config, set_streamer
from .config import ExecutorConfig
from . import llm


load_dotenv()
# Only change the MAJOR.MINOR if you need to. Do not change the PATCH. (vMAJOR.MINOR.PATCH).
__version__ = "0.1.0"
