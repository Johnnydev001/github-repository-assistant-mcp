from common.types import CommitAuthor


def parse_file_history_entry(self, entry: dict[str, object]) -> CommitAuthor:

    name: str = entry.get("commit",{}).get("author",{}).get("name", "")
    email: str = entry.get("commit",{}).get("author",{}).get("email", "")
    date: str = entry.get("commit",{}).get("author",{}).get("date", "")
    message: str = entry.get("commit",{}).get("message", "")
    url: str = entry.get("html_url", "")

    commit_author: CommitAuthor = CommitAuthor(
        name=name,
        email=email,
        date=date,
        message=message,
        url=url,
    )
    return commit_author