from enum import Enum
from pydantic import BaseModel


class TaggableItemType(str, Enum):
    TICKET = "Ticket"
    PROBLEM = "Problem"
    CHANGE = "Change"
    COMPUTER = "Computer"
    PROJECT_TASK = "ProjectTask"


class TagAssignSchema(BaseModel):
    itemtype: TaggableItemType
    items_id: int
    tag_id: int
