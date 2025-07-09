from pydantic import BaseModel
from enum import Enum


class OpType(str, Enum):
    ECHO = "echo"


class DataIn(BaseModel):
    text: str = ""
    op: OpType = OpType.ECHO
