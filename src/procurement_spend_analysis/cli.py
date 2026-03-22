from __future__ import annotations

import uvicorn

from procurement_spend_analysis.config import get_settings


def main() -> None:
    settings = get_settings()
    uvicorn.run(
        "procurement_spend_analysis.api.app:app",
        host="0.0.0.0",
        port=settings.api_port,
        reload=settings.environment == "dev",
    )
