
import http.server
import socketserver
import webbrowser
import os
import sys

PORT = 8000
Handler = http.server.SimpleHTTPRequestHandler

# Change directory to where the script is located (if needed)
# os.chdir(os.path.dirname(os.path.abspath(__file__)))

print(f"Serving at http://localhost:{PORT}")
print("Opening browser...")

try:
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"Server started at port {PORT}")
        # Open the specific file
        webbrowser.open(f"http://localhost:{PORT}/standalone.html")
        httpd.serve_forever()
except OSError as e:
    print(f"Error starting server: {e}")
    print("Try using a different port or check if the address is in use.")
except KeyboardInterrupt:
    print("\nServer stopped.")
