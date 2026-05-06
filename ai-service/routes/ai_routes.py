from flask import Blueprint, request, jsonify
from services.groq_client import get_ai_response
from utils.sanitizer import sanitize_input, is_prompt_injection
from datetime import datetime, timezone
import json
import re
import logging

ai_bp = Blueprint("ai", __name__)

history = []


# ---------- HELPERS ----------
def current_time():
    return datetime.now(timezone.utc).isoformat()


def success(data):
    return jsonify({
        "success": True,
        "data": data,
        "timestamp": current_time()
    })


def error(msg, code=400):
    return jsonify({
        "success": False,
        "error": msg,
        "timestamp": current_time()
    }), code


def extract_json_array(text):
    try:
        return json.loads(text)
    except:
        pass

    match = re.search(r"\[.*\]", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except:
            pass

    return None


def add_history(api_type, user_input):
    history.append({
        "type": api_type,
        "input": user_input,
        "timestamp": current_time()
    })


# ---------- DESCRIBE ----------
@ai_bp.route("/describe", methods=["POST"])
def describe():
    logging.info("Describe API called")

    try:
        data = request.get_json()

        if not data:
            return error("No input provided")

        user_input = data.get("input")

        if not user_input:
            return error("Input is required")

        user_input = sanitize_input(user_input)

        if is_prompt_injection(user_input):
            return error("Malicious input detected")

        prompt = f"""
Generate professional vendor offboarding explanation.

Vendor:
{user_input}
"""

        result = get_ai_response(prompt)

        if "error" in result:
            return error(result["error"], 500)

        add_history("describe", user_input)

        return success({
            "description": result.get("response", "")
        })

    except Exception as e:
        return error(str(e), 500)


# ---------- RECOMMEND ----------
@ai_bp.route("/recommend", methods=["POST"])
def recommend():
    logging.info("Recommend API called")

    try:
        data = request.get_json()

        if not data:
            return error("No input provided")

        user_input = data.get("input")

        if not user_input:
            return error("Input is required")

        user_input = sanitize_input(user_input)

        if is_prompt_injection(user_input):
            return error("Malicious input detected")

        prompt = f"""
Return 3 recommendations as JSON.

Vendor:
{user_input}
"""

        result = get_ai_response(prompt)

        if "error" in result:
            return error(result["error"], 500)

        recs = extract_json_array(result.get("response", ""))

        if not recs:
            return success({
                "recommendations": [],
                "is_fallback": True
            })

        add_history("recommend", user_input)

        return success({
            "recommendations": recs[:3],
            "is_fallback": False
        })

    except Exception as e:
        return error(str(e), 500)


# ---------- GENERATE REPORT ----------
@ai_bp.route("/generate-report", methods=["POST"])
def generate_report():
    logging.info("Generate Report API called")

    try:
        data = request.get_json()

        if not data:
            return error("No input provided")

        user_input = data.get("input")

        if not user_input:
            return error("Input is required")

        user_input = sanitize_input(user_input)

        if is_prompt_injection(user_input):
            return error("Malicious input detected")

        prompt = f"""
Generate structured vendor offboarding report.

Sections:
1. Reason
2. Risks
3. Business Impact
4. Recommendations

Vendor:
{user_input}
"""

        result = get_ai_response(prompt)

        if "error" in result:
            return error(result["error"], 500)

        report = result.get("response", "")

        add_history("generate-report", user_input)

        return success({
            "report": report
        })

    except Exception as e:
        return error(str(e), 500)


# ---------- EXPORT REPORT ----------
@ai_bp.route("/export-report", methods=["POST"])
def export_report():
    logging.info("Export Report API called")

    try:
        data = request.get_json()

        if not data:
            return error("No input provided")

        report = data.get("report")

        if not report:
            return error("Report is required")

        exported_text = f"""
VENDOR OFFBOARDING REPORT
Generated At: {current_time()}

{report}
"""

        return success({
            "exported_report": exported_text
        })

    except Exception as e:
        return error(str(e), 500)


# ---------- HISTORY ----------
@ai_bp.route("/history", methods=["GET"])
def get_history():
    try:
        limit = int(request.args.get("limit", 5))
        offset = int(request.args.get("offset", 0))

        sliced = history[offset:offset + limit]

        return success({
            "history": sliced,
            "count": len(history),
            "limit": limit,
            "offset": offset
        })

    except Exception as e:
        return error(str(e), 500)


# ---------- SEARCH HISTORY ----------
@ai_bp.route("/search-history", methods=["GET"])
def search_history():
    try:
        keyword = request.args.get("keyword", "").lower()

        results = [
            item for item in history
            if keyword in item["input"].lower()
        ]

        return success({
            "results": results,
            "count": len(results)
        })

    except Exception as e:
        return error(str(e), 500)


# ---------- CLEAR HISTORY ----------
@ai_bp.route("/clear-history", methods=["DELETE"])
def clear_history():
    try:
        history.clear()

        return success({
            "message": "History cleared successfully"
        })

    except Exception as e:
        return error(str(e), 500)


# ---------- STATS ----------
@ai_bp.route("/stats", methods=["GET"])
def stats():
    try:
        describe_count = len([x for x in history if x["type"] == "describe"])
        recommend_count = len([x for x in history if x["type"] == "recommend"])
        report_count = len([x for x in history if x["type"] == "generate-report"])

        return success({
            "total_requests": len(history),
            "describe_requests": describe_count,
            "recommend_requests": recommend_count,
            "report_requests": report_count
        })

    except Exception as e:
        return error(str(e), 500)