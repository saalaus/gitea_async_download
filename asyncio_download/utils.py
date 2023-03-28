def chunked(lst: list, chunk_size: int) -> list[list]:
    return [lst[range_item:range_item+chunk_size] for range_item in range(0, len(lst), chunk_size)]
