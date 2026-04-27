from dataclasses import dataclass

@dataclass(frozen=True)
class CommitAuthor:
    name: str
    email: str
    date: str
    message: str
    url: str