def human_readable_size(size_in_bytes):
    """Convert bytes to human readable format"""
    if not size_in_bytes:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_in_bytes >= 1024 and i < len(size_names) - 1:
        size_in_bytes /= 1024.0
        i += 1
    return f"{size_in_bytes:.2f} {size_names[i]}"
