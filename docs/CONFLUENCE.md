# Enterprise Confluence Integration Guide

This document details the optional enterprise Atlassian Confluence REST API publishing module (`scripts/confluence_publisher.py`).

---

## 1. Overview & Architecture

`scripts/confluence_publisher.py` provides an automated publishing integration built strictly with the Python Standard Library (`urllib.request`, `json`, `base64`).

When activated, `main.py` sends the generated HTML report content to your enterprise Atlassian Confluence Cloud space via HTTPS REST API.

---

## 2. Environment Variables Configuration (`.env`)

To activate Confluence publishing, configure these variables in `.env`:

```env
# Confluence Cloud Base URL
CONFLUENCE_BASE_URL=https://your-domain.atlassian.net

# Atlassian Account Email
CONFLUENCE_EMAIL=user@company.com

# Atlassian API Token
CONFLUENCE_API_TOKEN=your-atlassian-api-token

# Confluence Space Key
CONFLUENCE_SPACE_KEY=OPS

# Confluence Page ID (Optional: leave blank to create a new page, or provide ID to update existing page)
CONFLUENCE_PAGE_ID=
```

---

## 3. Fallback Behavior (Missing Credentials)

If Confluence credentials are omitted or incomplete in `.env`, the publisher module executes as follows:

1. Detects missing credentials during `get_confluence_config()`.
2. Logs:
   ```text
   Confluence publishing skipped -- credentials not configured.
   ```
3. Returns `True` cleanly without raising an error or interrupting the local workflow. Local HTML report generation and execution logging complete successfully.

---

## 4. REST API Request Behavior

When credentials exist:

1. **Authentication**: Builds an HTTP `Basic` Authentication header using Base64-encoded `email:api_token`.
2. **Payload Storage Representation**: Formats the HTML content into Confluence's `storage` XML representation JSON payload.
3. **Page Creation (No Page ID)**: Sends an HTTP `POST` request to `{base_url}/wiki/rest/api/content` to create a new page under `CONFLUENCE_SPACE_KEY`.
4. **Page Update (Page ID Provided)**: Sends an HTTP `GET` request to retrieve current page version, increments version number, and sends an HTTP `PUT` request to update the page content.
5. **Error Handling**: Catches HTTP errors (e.g. 401 Unauthorized, 404 Space Not Found) safely without crashing main workflow execution.
