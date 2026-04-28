from models import CommitAuthor

def parse_file_history_entry(entry: dict[str, object]) -> CommitAuthor:
    name: str = entry.get("commit", {}).get("author", {}).get("name", "")
    email: str = entry.get("commit", {}).get("author", {}).get("email", "")
    date: str = entry.get("commit", {}).get("author", {}).get("date", "")
    message: str = entry.get("commit", {}).get("message", "")
    url: str = entry.get("html_url", "")

    return CommitAuthor(name=name, email=email, date=date, message=message, url=url)
