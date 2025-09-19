from ebd import app

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))  # Render usa $PORT, local usa 5000
    app.run(host="0.0.0.0", port=port, debug=True)

