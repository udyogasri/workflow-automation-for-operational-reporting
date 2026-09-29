"""
confluence_publisher.py
Lightweight Confluence Publishing Module (Python Standard Library Only).

Supports publishing generated HTML operational reports or documentation to an enterprise
Confluence Cloud space via REST API using standard-library urllib.request.

Configuration (Environment Variables Only):
  - CONFLUENCE_BASE_URL : e.g., https://your-domain.atlassian.net
  - CONFLUENCE_EMAIL    : e.g., user@company.com
  - CONFLUENCE_API_TOKEN: Atlassian API token
  - CONFLUENCE_SPACE_KEY: Confluence Space Key (e.g., OPS)
  - CONFLUENCE_PAGE_ID  : (Optional) Page ID for updating an existing page

Behavior:
  - If credentials are missing: Logs 'Confluence publishing skipped - credentials not configured.' and returns True without failing local workflow.
  - If credentials exist: Performs HTTPS REST API call to publish/update page. Handles auth failures & HTTP errors safely.
"""

import os
import sys
import json
import base64
import logging
import urllib.request
import urllib.error

def get_confluence_config():
    """Read Confluence credentials from environment variables."""
    base_url = os.environ.get("CONFLUENCE_BASE_URL", "").rstrip("/")
    email = os.environ.get("CONFLUENCE_EMAIL", "").strip()
    api_token = os.environ.get("CONFLUENCE_API_TOKEN", "").strip()
    space_key = os.environ.get("CONFLUENCE_SPACE_KEY", "").strip()
    page_id = os.environ.get("CONFLUENCE_PAGE_ID", "").strip()

    if not (base_url and email and api_token and space_key):
        return None

    return {
        "base_url": base_url,
        "email": email,
        "api_token": api_token,
        "space_key": space_key,
        "page_id": page_id
    }


def publish_to_confluence(title, html_content, logger=None):
    """
    Publish or update a page in Confluence.
    Returns True if publication succeeded or was safely skipped, False on HTTP error.
    """
    if logger is None:
        logger = logging.getLogger("confluence_publisher")
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter("%(levelname)-8s | %(message)s"))
            logger.addHandler(handler)

    config = get_confluence_config()
    if config is None:
        logger.info("Confluence publishing skipped -- credentials not configured.")
        return True

    logger.info("Confluence credentials detected. Preparing REST API request...")

    base_url = config["base_url"]
    email = config["email"]
    api_token = config["api_token"]
    space_key = config["space_key"]
    page_id = config["page_id"]

    # Basic Auth header
    auth_str = f"{email}:{api_token}"
    b64_auth = base64.b64encode(auth_str.encode("utf-8")).decode("utf-8")
    headers = {
        "Authorization": f"Basic {b64_auth}",
        "Content-Type": "application/json",
        "User-Agent": "Python-Confluence-Publisher/1.0"
    }

    # Storage representation for Confluence
    body_data = {
        "type": "page",
        "title": title,
        "space": {"key": space_key},
        "body": {
            "storage": {
                "value": html_content,
                "representation": "storage"
            }
        }
    }

    try:
        if page_id:
            # Update existing page
            url = f"{base_url}/wiki/rest/api/content/{page_id}"
            body_data["id"] = page_id
            # Retrieve version for update
            req_get = urllib.request.Request(url, headers=headers, method="GET")
            with urllib.request.urlopen(req_get) as resp_get:
                existing_page = json.loads(resp_get.read().decode("utf-8"))
                current_version = existing_page.get("version", {}).get("number", 1)
                body_data["version"] = {"number": current_version + 1}
            
            method = "PUT"
        else:
            # Create new page
            url = f"{base_url}/wiki/rest/api/content"
            method = "POST"

        payload = json.dumps(body_data).encode("utf-8")
        req = urllib.request.Request(url, data=payload, headers=headers, method=method)

        with urllib.request.urlopen(req) as response:
            res_json = json.loads(response.read().decode("utf-8"))
            new_id = res_json.get("id", "N/A")
            logger.info(f"Confluence publishing successful! Page ID: {new_id} ({method} {url})")
            return True

    except urllib.error.HTTPError as e:
        error_msg = e.read().decode("utf-8") if e.fp else str(e)
        if e.code == 401:
            logger.error(f"Confluence Authentication Failed (HTTP 401): Check CONFLUENCE_EMAIL and API Token.")
        elif e.code == 404:
            logger.error(f"Confluence Space/Page Not Found (HTTP 404): Check SPACE_KEY '{space_key}' or PAGE_ID '{page_id}'.")
        else:
            logger.error(f"Confluence HTTP Error ({e.code}): {error_msg}")
        return False
    except Exception as e:
        logger.error(f"Confluence publishing network error: {e}")
        return False


if __name__ == "__main__":
    sample_title = "Operational Report Test Page"
    sample_html = "<p>Standardized Operational Report Published via Python.</p>"
    print("Testing Confluence Publisher module...")
    success = publish_to_confluence(sample_title, sample_html)
    print(f"Publisher result: {success}")
