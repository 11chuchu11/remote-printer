from pypdf import PdfReader


def count_pages(path: str) -> int:
    if not path.lower().endswith(".pdf"):
        return 1
    try:
        return len(PdfReader(path).pages)
    except Exception:
        return 1


def resolve_printed_pages(total: int, pages_filter: str) -> int:
    if not pages_filter or pages_filter == "all":
        return total
    if pages_filter == "odd":
        return (total + 1) // 2
    if pages_filter == "even":
        return total // 2

    selected = set()
    for part in pages_filter.split(","):
        if "-" in part:
            start, end = part.split("-", 1)
            selected.update(range(int(start), int(end) + 1))
        else:
            selected.add(int(part))
    return len({p for p in selected if 1 <= p <= total})
