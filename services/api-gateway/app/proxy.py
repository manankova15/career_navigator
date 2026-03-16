"""HTTP reverse proxy helper."""
from __future__ import annotations
import httpx
from fastapi import Request, Response

_TIMEOUT = httpx.Timeout(30.0)
# Headers the gateway should NOT forward upstream
_HOP_BY_HOP = {
    "host", "connection", "transfer-encoding", "te",
    "trailers", "upgrade", "keep-alive", "proxy-authorization",
}


async def forward(request: Request, target_base: str, strip_prefix: str = "") -> Response:
    """Forward *request* to *target_base*, stripping *strip_prefix* from the path."""
    path = request.url.path
    if strip_prefix and path.startswith(strip_prefix):
        path = path[len(strip_prefix):]

    url = f"{target_base.rstrip('/')}{path}"
    if request.url.query:
        url += f"?{request.url.query}"

    # Filter hop-by-hop headers
    headers = {
        k: v for k, v in request.headers.items()
        if k.lower() not in _HOP_BY_HOP
    }

    body = await request.body()

    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        upstream_resp = await client.request(
            method=request.method,
            url=url,
            headers=headers,
            content=body,
        )

    # Filter response headers
    resp_headers = {
        k: v for k, v in upstream_resp.headers.items()
        if k.lower() not in _HOP_BY_HOP
    }
    return Response(
        content=upstream_resp.content,
        status_code=upstream_resp.status_code,
        headers=resp_headers,
    )
