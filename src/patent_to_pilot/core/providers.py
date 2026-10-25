"""Provider seam. No network provider is enabled by this package."""

from __future__ import annotations

from .models import ProviderRequest, ProviderResponse


class MockProvider:
    def __init__(self, text: str = "MOCK_RESPONSE") -> None:
        self.text = text
        self.requests: list[ProviderRequest] = []

    def complete(self, request: ProviderRequest) -> ProviderResponse:
        self.requests.append(request)
        return ProviderResponse(provider="mock", model="mock", text=self.text, mock=True)
