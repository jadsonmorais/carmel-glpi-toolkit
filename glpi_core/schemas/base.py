from enum import Enum


class ItemType(str, Enum):
    TICKET = "Ticket"
    PROBLEM = "Problem"
    CHANGE = "Change"
    COMPUTER = "Computer"
    PROJECT = "Project"
    PROJECT_TASK = "ProjectTask"
