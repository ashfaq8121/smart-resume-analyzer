if __name__ == "__main__":
    from app import create_app
    
    app = create_app("development")
    
    print("=" * 55)
    print("🧠 Smart Resume Analyzer")
    print("=" * 55)
    print("✅ Server starting...")
    print("🌐 Open: http://127.0.0.1:5000")
    print("🛑 Stop: Press CTRL+C")
    print("=" * 55)
    
    app.run(host="0.0.0.0", port=5000, debug=True)