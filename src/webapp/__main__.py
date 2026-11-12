"""`python -m src.webapp` sobe o servidor de desenvolvimento em http://127.0.0.1:5000."""
import os

from . import create_app

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    create_app().run(host="127.0.0.1", port=port, debug=False)
