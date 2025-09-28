# common proxy headers in order of preference
headers_to_check = [
    'X-Forwarded-For',
    'X-Real-IP',
    'X-Client-IP',
    'CF-Connecting-IP'  # Cloudflare
]


def get_client_ip(flask_request) -> str:
    """Extract the real client IP, considering proxy headers"""

    for header in headers_to_check:
        ip = flask_request.headers.get(header)
        if ip:
            # X-Forwarded-For can contain multiple IPs, take the first one
            return ip.split(',')[0].strip()
    
    # Fallback to remote_addr
    return flask_request.remote_addr \
        or flask_request.environ.get('REMOTE_ADDR', 'unknown')