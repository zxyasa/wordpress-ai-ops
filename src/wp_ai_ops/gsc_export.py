"""Export page-level data from Google Search Console API to CSV."""
from __future__ import annotations

import csv
from datetime import datetime, timedelta
from pathlib import Path


def export_gsc_csv(
    property_url: str,
    credentials_path: str | Path,
    output_path: str | Path,
    days: int = 7,
) -> Path:
    """Fetch page-level GSC data for the last *days* days and write a CSV.

    The output CSV has columns: url,clicks,impressions,ctr,position
    compatible with ``weekly_cycle._read_gsc()``.

    Requires the ``google`` optional dependency group::

        pip install wordpress-ai-ops[google]

    Returns the resolved *output_path*.
    """
    try:
        from google.oauth2 import service_account  # type: ignore[import-untyped]
        from googleapiclient.discovery import build  # type: ignore[import-untyped]
    except ImportError as exc:
        raise ImportError(
            "google-api-python-client and google-auth are required. "
            "Install with:  pip install wordpress-ai-ops[google]"
        ) from exc

    credentials_path = Path(credentials_path)
    if not credentials_path.exists():
        raise FileNotFoundError(f"GSC credentials not found: {credentials_path}")

    credentials = service_account.Credentials.from_service_account_file(
        str(credentials_path),
        scopes=["https://www.googleapis.com/auth/webmasters.readonly"],
    )
    service = build("searchconsole", "v1", credentials=credentials)

    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days)

    request_body = {
        "startDate": start_date.strftime("%Y-%m-%d"),
        "endDate": end_date.strftime("%Y-%m-%d"),
        "dimensions": ["page"],
        "rowLimit": 500,
        "startRow": 0,
    }

    response = (
        service.searchanalytics()
        .query(siteUrl=property_url, body=request_body)
        .execute()
    )

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["url", "clicks", "impressions", "ctr", "position"])
        for row in response.get("rows", []):
            writer.writerow([
                row["keys"][0],
                row.get("clicks", 0),
                row.get("impressions", 0),
                f"{row.get('ctr', 0):.4f}",
                f"{row.get('position', 0):.1f}",
            ])

    return output_path
