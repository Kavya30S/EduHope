def truncate_text(text, max_length=100):
    return text[:max_length] + '...' if len(text) > max_length else text