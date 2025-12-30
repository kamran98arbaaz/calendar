from app import create_app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)

# Vercel expects the WSGI application to be named 'app'
# This allows Vercel to import and run the Flask application