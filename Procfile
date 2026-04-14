# Procfile - tells Render/Heroku how to start the app
# gunicorn = production-grade WSGI server (better than Flask's built-in server)
web: gunicorn run:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120
