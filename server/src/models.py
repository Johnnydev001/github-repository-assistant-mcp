from dataclasses import dataclass
from enum import Enum

@dataclass(frozen=True)
class CommitAuthor:
    name: str
    email: str
    date: str
    message: str
    url: str

class RequestUrlSuffix(Enum):
    PULL_REQUEST = "pulls"
    COMMITS = "commits"
    CONTENTS = "contents"
    BRANCHES = "branches"
