from flask import Blueprint, jsonify

ai_bp = Blueprint("ai", __name__)

@ai_bp.route("/test")
def test():
    return jsonify({"message": "AI route working"})