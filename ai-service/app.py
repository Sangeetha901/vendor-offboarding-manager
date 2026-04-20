from flask import Flask
from routes.ai_routes import ai_bp

app = Flask(__name__)

app.register_blueprint(ai_bp)

@app.route("/")
def home():
    return "AI Service Running"

@app.route("/health")
def health():
    return {"status": "ok"}

if __name__ == "__main__":
    app.run(port=5000, debug=True)