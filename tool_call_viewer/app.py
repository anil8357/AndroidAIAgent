"""
Tool Call Viewer — A simple Flask app that queries LiteLLM's Postgres DB
and displays ALL tool calls for any request, bypassing the 50-item UI limit.
"""

import os
import json
from flask import Flask, render_template, request, jsonify
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__)

DB_URL = os.environ.get(
    "DATABASE_URL", "postgresql://postgres:litellm@db:5432/litellm"
)


def get_db():
    return psycopg2.connect(DB_URL, cursor_factory=RealDictCursor)


@app.route("/")
def index():
    """Main page — list recent requests that have tool calls."""
    page = int(request.args.get("page", 1))
    per_page = 30
    offset = (page - 1) * per_page

    conn = get_db()
    cur = conn.cursor()

    # Get requests that contain tool_calls in the response
    cur.execute("""
        SELECT 
            request_id,
            model,
            "startTime",
            "endTime",
            total_tokens,
            spend,
            cache_hit,
            response::text as response_text
        FROM "LiteLLM_SpendLogs"
        WHERE response::text LIKE '%%tool_calls%%'
        ORDER BY "startTime" DESC
        LIMIT %s OFFSET %s
    """, (per_page, offset))

    rows = cur.fetchall()

    # Count tool calls for each row
    results = []
    for row in rows:
        tool_count = 0
        try:
            resp = json.loads(row["response_text"]) if row["response_text"] else {}
            choices = resp.get("choices", [])
            for choice in choices:
                msg = choice.get("message", {})
                tc = msg.get("tool_calls", [])
                tool_count = len(tc)
        except (json.JSONDecodeError, TypeError):
            pass

        results.append({
            "request_id": row["request_id"],
            "model": row["model"],
            "startTime": row["startTime"],
            "endTime": row["endTime"],
            "total_tokens": row["total_tokens"],
            "spend": row["spend"],
            "tool_count": tool_count,
        })

    # Get total count for pagination
    cur.execute("""
        SELECT COUNT(*) as cnt FROM "LiteLLM_SpendLogs"
        WHERE response::text LIKE '%%tool_calls%%'
    """)
    total = cur.fetchone()["cnt"]

    cur.close()
    conn.close()

    total_pages = (total + per_page - 1) // per_page

    return render_template(
        "index.html",
        results=results,
        page=page,
        total_pages=total_pages,
        total=total,
    )


@app.route("/request/<request_id>")
def view_request(request_id):
    """View all tool calls for a specific request."""
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT 
            request_id,
            model,
            "startTime",
            "endTime",
            total_tokens,
            prompt_tokens,
            completion_tokens,
            spend,
            messages::text as messages_text,
            response::text as response_text,
            metadata::text as metadata_text
        FROM "LiteLLM_SpendLogs"
        WHERE request_id = %s
    """, (request_id,))

    row = cur.fetchone()
    cur.close()
    conn.close()

    if not row:
        return "Request not found", 404

    # Parse tool calls from response
    tool_calls = []
    try:
        resp = json.loads(row["response_text"]) if row["response_text"] else {}
        choices = resp.get("choices", [])
        for choice in choices:
            msg = choice.get("message", {})
            tc = msg.get("tool_calls", [])
            tool_calls = tc
    except (json.JSONDecodeError, TypeError):
        pass

    # Parse request messages to find tool results
    tool_results = []
    try:
        messages = json.loads(row["messages_text"]) if row["messages_text"] else []
        if isinstance(messages, list):
            for msg in messages:
                if isinstance(msg, dict) and msg.get("role") == "tool":
                    tool_results.append(msg)
    except (json.JSONDecodeError, TypeError):
        pass

    # Parse metadata
    metadata = {}
    try:
        metadata = json.loads(row["metadata_text"]) if row["metadata_text"] else {}
    except (json.JSONDecodeError, TypeError):
        pass

    return render_template(
        "request_detail.html",
        row=row,
        tool_calls=tool_calls,
        tool_results=tool_results,
        metadata=metadata,
        tool_count=len(tool_calls),
        json=json,
    )


@app.route("/api/request/<request_id>")
def api_request(request_id):
    """JSON API endpoint for programmatic access."""
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT 
            request_id,
            model,
            response::text as response_text
        FROM "LiteLLM_SpendLogs"
        WHERE request_id = %s
    """, (request_id,))

    row = cur.fetchone()
    cur.close()
    conn.close()

    if not row:
        return jsonify({"error": "not found"}), 404

    tool_calls = []
    try:
        resp = json.loads(row["response_text"]) if row["response_text"] else {}
        choices = resp.get("choices", [])
        for choice in choices:
            msg = choice.get("message", {})
            tc = msg.get("tool_calls", [])
            tool_calls = tc
    except (json.JSONDecodeError, TypeError):
        pass

    return jsonify({
        "request_id": row["request_id"],
        "model": row["model"],
        "tool_call_count": len(tool_calls),
        "tool_calls": tool_calls,
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
