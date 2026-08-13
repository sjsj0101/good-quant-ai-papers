"""Bounded HTTPS fetching for recognized public paper sources."""

from __future__ import annotations

import http.client
import ipaddress
import socket
import ssl
from dataclasses import dataclass
from typing import Callable
from urllib.parse import SplitResult, urljoin, urlsplit


MAX_REDIRECTS = 3
MAX_RESPONSE_BYTES = 2_000_000
CONNECT_TIMEOUT_SECONDS = 5
READ_TIMEOUT_SECONDS = 15
_REDIRECT_STATUSES = frozenset({301, 302, 303, 307, 308})


class SourceError(ValueError):
    """A stable, public-safe source retrieval error."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


@dataclass(frozen=True)
class HttpResponse:
    url: str
    status: int
    headers: dict[str, str]
    body: bytes


Resolver = Callable[[str, int], tuple[str, ...]]
Transport = Callable[[str, str, int, int], HttpResponse]


def _host_allowed(host: str, accepted_hosts: frozenset[str]) -> bool:
    return any(host == trusted or host.endswith(f".{trusted}") for trusted in accepted_hosts)


def validated_https_url(url: str, accepted_hosts: frozenset[str]) -> SplitResult:
    """Parse *url* and enforce the fetcher's scheme and host policy."""

    if not isinstance(url, str) or not url or any(character.isspace() for character in url):
        raise SourceError("invalid-url")
    try:
        parsed = urlsplit(url)
        port = parsed.port
    except ValueError:
        raise SourceError("invalid-url") from None
    host = parsed.hostname.casefold() if parsed.hostname else ""
    if (
        parsed.scheme.casefold() != "https"
        or not host
        or parsed.username is not None
        or parsed.password is not None
        or parsed.fragment
        or not _host_allowed(host, accepted_hosts)
        or port not in (None, 443)
    ):
        raise SourceError("unsupported-source")
    return parsed


def _default_resolver(host: str, port: int) -> tuple[str, ...]:
    try:
        rows = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
    except OSError:
        raise SourceError("source-unavailable") from None
    addresses = tuple(dict.fromkeys(row[4][0] for row in rows))
    if not addresses:
        raise SourceError("source-unavailable")
    return addresses


def _global_addresses(addresses: tuple[str, ...]) -> tuple[str, ...]:
    if not addresses:
        raise SourceError("source-unavailable")
    for address in addresses:
        try:
            parsed = ipaddress.ip_address(address)
        except ValueError:
            raise SourceError("unsafe-address") from None
        if not parsed.is_global:
            raise SourceError("unsafe-address")
    return addresses


def _request_target(parsed: SplitResult) -> str:
    target = parsed.path or "/"
    if parsed.query:
        target += f"?{parsed.query}"
    return target


def _default_transport(
    url: str,
    connect_ip: str,
    timeout: int,
    max_bytes: int,
) -> HttpResponse:
    parsed = urlsplit(url)
    host = parsed.hostname
    assert host is not None
    raw: socket.socket | None = None
    tls: ssl.SSLSocket | None = None
    try:
        raw = socket.create_connection(
            (connect_ip, parsed.port or 443), timeout=CONNECT_TIMEOUT_SECONDS
        )
        context = ssl.create_default_context()
        tls = context.wrap_socket(raw, server_hostname=host)
        raw = None
        tls.settimeout(timeout)
        host_header = host if parsed.port in (None, 443) else f"{host}:{parsed.port}"
        request = (
            f"GET {_request_target(parsed)} HTTP/1.1\r\n"
            f"Host: {host_header}\r\n"
            "User-Agent: good-quant-ai-papers-metadata/1\r\n"
            "Accept: application/json, application/atom+xml, text/html;q=0.9\r\n"
            "Connection: close\r\n\r\n"
        ).encode("ascii")
        tls.sendall(request)
        response = http.client.HTTPResponse(tls)
        response.begin()
        headers = {key.casefold(): value for key, value in response.getheaders()}
        length = headers.get("content-length")
        if length is not None:
            try:
                if int(length) > max_bytes:
                    raise SourceError("response-too-large")
            except ValueError:
                raise SourceError("invalid-response") from None
        body = response.read(max_bytes + 1)
        if len(body) > max_bytes:
            raise SourceError("response-too-large")
        return HttpResponse(
            url=url,
            status=response.status,
            headers=headers,
            body=body,
        )
    except SourceError:
        raise
    except (OSError, ssl.SSLError, http.client.HTTPException):
        raise SourceError("source-unavailable") from None
    finally:
        if tls is not None:
            tls.close()
        if raw is not None:
            raw.close()


class SafeFetcher:
    """Fetch a bounded response while preserving checked DNS and TLS identity."""

    def __init__(
        self,
        *,
        resolver: Resolver | None = None,
        transport: Transport | None = None,
    ) -> None:
        self._resolver = resolver or _default_resolver
        self._transport = transport or _default_transport

    def get(
        self,
        url: str,
        *,
        accepted_hosts: frozenset[str],
    ) -> HttpResponse:
        current = url
        for redirect_count in range(MAX_REDIRECTS + 1):
            parsed = validated_https_url(current, accepted_hosts)
            host = parsed.hostname
            assert host is not None
            addresses = _global_addresses(self._resolver(host, parsed.port or 443))
            response = self._transport(
                current,
                addresses[0],
                READ_TIMEOUT_SECONDS,
                MAX_RESPONSE_BYTES,
            )
            validated_https_url(response.url, accepted_hosts)
            if len(response.body) > MAX_RESPONSE_BYTES:
                raise SourceError("response-too-large")
            if response.status in _REDIRECT_STATUSES:
                if redirect_count == MAX_REDIRECTS:
                    raise SourceError("too-many-redirects")
                location = response.headers.get("location")
                if not isinstance(location, str) or not location.strip():
                    raise SourceError("invalid-redirect")
                current = urljoin(current, location.strip())
                validated_https_url(current, accepted_hosts)
                continue
            if not 200 <= response.status < 300:
                raise SourceError("upstream-http-error")
            return HttpResponse(
                url=current,
                status=response.status,
                headers=response.headers,
                body=response.body,
            )
        raise SourceError("too-many-redirects")
