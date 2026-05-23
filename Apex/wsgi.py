import threading
import sys
import os

# Add parent dir to path so bot2 package is found
sys.path.insert(0, os.path.dirname(__file__))

from bot2.main import app, socketio, bot_loop

# Start bot loop in background thread
t = threading.Thread(target=bot_loop, daemon=True)
t.start()

# Expose for gunicorn
application = app

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, host="0.0.0.0", port=port, debug=False)
