from __future__ import annotations

import unittest

from scripts.contributions.http import HttpResponse, SafeFetcher, SourceError


TRUSTED = frozenset({"example.org", "api.example.org"})


class RecordingTransport:
    def __init__(self, responses: list[HttpResponse]) -> None:
        self.responses = list(responses)
        self.calls: list[tuple[str, str, int]] = []

    def __call__(
        self, url: str, connect_ip: str, timeout: int, max_bytes: int
    ) -> HttpResponse:
        self.calls.append((url, connect_ip, max_bytes))
        return self.responses.pop(0)


def public_resolver(host: str, port: int) -> tuple[str, ...]:
    return ("93.184.216.34",)


class SafeFetcherTests(unittest.TestCase):
    def test_fetches_https_from_exact_or_dot_subdomain_and_pins_checked_ip(self) -> None:
        for url in (
            "https://example.org/paper",
            "https://papers.example.org/paper",
        ):
            with self.subTest(url=url):
                transport = RecordingTransport(
                    [HttpResponse(url=url, status=200, headers={}, body=b"ok")]
                )
                response = SafeFetcher(
                    resolver=public_resolver, transport=transport
                ).get(url, accepted_hosts=TRUSTED)
                self.assertEqual(response.body, b"ok")
                self.assertEqual(transport.calls[0][1], "93.184.216.34")

    def test_rejects_http_unknown_and_suffix_lookalike_before_transport(self) -> None:
        transport = RecordingTransport([])
        fetcher = SafeFetcher(resolver=public_resolver, transport=transport)
        for url in (
            "http://example.org/paper",
            "https://unknown.example/paper",
            "https://example.org.evil.test/paper",
        ):
            with self.subTest(url=url), self.assertRaises(SourceError):
                fetcher.get(url, accepted_hosts=TRUSTED)
        self.assertEqual(transport.calls, [])

    def test_rejects_private_loopback_link_local_and_mixed_dns(self) -> None:
        addresses = (
            ("127.0.0.1",),
            ("10.0.0.1",),
            ("169.254.1.1",),
            ("93.184.216.34", "192.168.1.2"),
        )
        for resolved in addresses:
            with self.subTest(resolved=resolved), self.assertRaises(SourceError):
                SafeFetcher(
                    resolver=lambda host, port, value=resolved: value,
                    transport=RecordingTransport([]),
                ).get("https://example.org/paper", accepted_hosts=TRUSTED)

    def test_rejects_insecure_or_untrusted_redirect(self) -> None:
        targets = (
            "http://example.org/next",
            "https://evil.test/next",
        )
        for target in targets:
            with self.subTest(target=target), self.assertRaises(SourceError):
                SafeFetcher(
                    resolver=public_resolver,
                    transport=RecordingTransport(
                        [
                            HttpResponse(
                                url="https://example.org/start",
                                status=302,
                                headers={"location": target},
                                body=b"",
                            )
                        ]
                    ),
                ).get("https://example.org/start", accepted_hosts=TRUSTED)

    def test_follows_bounded_trusted_redirect(self) -> None:
        transport = RecordingTransport(
            [
                HttpResponse(
                    url="https://example.org/start",
                    status=302,
                    headers={"location": "/paper"},
                    body=b"",
                ),
                HttpResponse(
                    url="https://example.org/paper",
                    status=200,
                    headers={},
                    body=b"paper",
                ),
            ]
        )
        response = SafeFetcher(
            resolver=public_resolver, transport=transport
        ).get("https://example.org/start", accepted_hosts=TRUSTED)
        self.assertEqual(response.url, "https://example.org/paper")
        self.assertEqual(len(transport.calls), 2)

    def test_rejects_oversized_body_even_from_injected_transport(self) -> None:
        response = HttpResponse(
            url="https://example.org/paper",
            status=200,
            headers={},
            body=b"x" * 2_000_001,
        )
        with self.assertRaisesRegex(SourceError, "response-too-large"):
            SafeFetcher(
                resolver=public_resolver,
                transport=RecordingTransport([response]),
            ).get("https://example.org/paper", accepted_hosts=TRUSTED)


if __name__ == "__main__":
    unittest.main()
