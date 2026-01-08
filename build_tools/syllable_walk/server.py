"""HTTP server for the syllable walker web interface.

This module provides a web-based interface for exploring syllable walks using the
standard library's http.server module (no Flask dependency). The server handles:
- Serving the HTML interface (/)
- Serving CSS styles (/styles.css)
- Providing walker statistics (/api/stats)
- Generating syllable walks (/api/walk)

Usage:
    from build_tools.syllable_walk.server import run_server
    run_server(data_path, max_neighbor_distance=3, port=5000)
"""

import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any

from build_tools.syllable_walk.walker import SyllableWalker
from build_tools.syllable_walk.web_assets import CSS_CONTENT, HTML_TEMPLATE


class WalkerHTTPHandler(BaseHTTPRequestHandler):
    """HTTP request handler for the syllable walker web interface.

    This handler processes HTTP requests and serves the web interface. It maintains
    a reference to the SyllableWalker instance and handles routing for HTML, CSS,
    and API endpoints.

    Class Attributes:
        walker: Shared SyllableWalker instance used for all requests
    """

    # Class attribute to hold the walker instance (shared across requests)
    walker: SyllableWalker | None = None

    def log_message(self, format: str, *args: Any) -> None:
        """Override to suppress default request logging to keep console clean.

        Args:
            format: Log message format string
            *args: Arguments to format into the message
        """
        # Suppress default logging (we'll log errors only)
        pass

    def _send_response(
        self, content: str, content_type: str = "text/html", status: int = 200
    ) -> None:
        """Send HTTP response with specified content and headers.

        Args:
            content: Response body content
            content_type: MIME type for Content-Type header. Default: text/html
            status: HTTP status code. Default: 200
        """
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content.encode("utf-8"))))
        self.end_headers()
        self.wfile.write(content.encode("utf-8"))

    def _send_json_response(self, data: dict[str, Any], status: int = 200) -> None:
        """Send JSON response with appropriate headers.

        Args:
            data: Dictionary to serialize as JSON
            status: HTTP status code. Default: 200
        """
        content = json.dumps(data)
        self._send_response(content, content_type="application/json", status=status)

    def _send_error_response(self, message: str, status: int = 400) -> None:
        """Send JSON error response.

        Args:
            message: Error message to include in response
            status: HTTP status code. Default: 400 (Bad Request)
        """
        self._send_json_response({"error": message}, status=status)

    def do_GET(self) -> None:  # noqa: N802
        """Handle GET requests for HTML, CSS, and stats API endpoint.

        Routes:
            /: Serve main HTML interface
            /styles.css: Serve CSS stylesheet
            /api/stats: Return walker statistics as JSON
            *: 404 for all other paths
        """
        if self.path == "/":
            # Serve main HTML page
            self._send_response(HTML_TEMPLATE, content_type="text/html")

        elif self.path == "/styles.css":
            # Serve CSS stylesheet
            self._send_response(CSS_CONTENT, content_type="text/css")

        elif self.path == "/api/stats":
            # Return walker statistics
            if self.walker is None:
                self._send_error_response("Walker not initialized", status=500)
                return

            stats = {
                "total_syllables": len(self.walker.syllables),
                "max_neighbor_distance": self.walker.max_neighbor_distance,
            }
            self._send_json_response(stats)

        else:
            # 404 for unknown paths
            self.send_error(404, "Not Found")

    def do_POST(self) -> None:  # noqa: N802
        """Handle POST requests for walk generation API endpoint.

        Routes:
            /api/walk: Generate a syllable walk based on JSON parameters

        Request JSON format:
            {
                "start": str | null,              # Starting syllable (null = random)
                "profile": str,                   # Walk profile name or "custom"
                "steps": int,                     # Number of steps in walk
                "max_flips": int,                 # Max feature flips (for custom)
                "temperature": float,             # Temperature (for custom)
                "frequency_weight": float,        # Frequency weight (for custom)
                "seed": int | null                # Random seed (null = random)
            }

        Response JSON format:
            {
                "walk": list[dict],               # List of syllable dicts
                "profile": str,                   # Profile name used
                "start": str                      # Starting syllable used
            }
        """
        if self.path == "/api/walk":
            if self.walker is None:
                self._send_error_response("Walker not initialized", status=500)
                return

            try:
                # Parse JSON request body
                content_length = int(self.headers.get("Content-Length", 0))
                if content_length == 0:
                    self._send_error_response("Empty request body")
                    return

                body = self.rfile.read(content_length)
                params = json.loads(body.decode("utf-8"))

                # Extract parameters with defaults
                start = params.get("start") or self.walker.get_random_syllable()
                profile = params.get("profile", "dialect")
                steps = params.get("steps", 5)
                seed = params.get("seed")

                # Generate walk based on profile
                if profile == "custom":
                    # Use custom parameters
                    walk = self.walker.walk(
                        start=start,
                        steps=steps,
                        max_flips=params.get("max_flips", 2),
                        temperature=params.get("temperature", 0.7),
                        frequency_weight=params.get("frequency_weight", 0.0),
                        seed=seed,
                    )
                else:
                    # Use named profile
                    walk = self.walker.walk_from_profile(
                        start=start, profile=profile, steps=steps, seed=seed
                    )

                # Return walk results
                response = {"walk": walk, "profile": profile, "start": start}
                self._send_json_response(response)

            except json.JSONDecodeError as e:
                self._send_error_response(f"Invalid JSON: {e}")
            except ValueError as e:
                self._send_error_response(str(e))
            except Exception as e:
                self._send_error_response(f"Server error: {e}", status=500)

        else:
            # 404 for unknown POST paths
            self.send_error(404, "Not Found")


def run_server(
    data_path: Path | str, max_neighbor_distance: int = 3, port: int = 5000, verbose: bool = True
) -> None:
    """Initialize syllable walker and start the web server.

    This function loads the syllable data, initializes the walker with neighbor
    graph construction, and starts the HTTP server on the specified port. The
    server runs until interrupted with Ctrl+C.

    Args:
        data_path: Path to syllables_annotated.json file
        max_neighbor_distance: Maximum Hamming distance for neighbor graph (1-3).
            Higher values allow more diverse walks but slower initialization. Default: 3
        port: Port number for HTTP server. Default: 5000
        verbose: Whether to print initialization progress. Default: True

    Raises:
        FileNotFoundError: If data_path does not exist
        ValueError: If max_neighbor_distance is invalid
        OSError: If port is already in use

    Example:
        >>> run_server("data/annotated/syllables_annotated.json", port=8000)
        # Server starts on http://localhost:8000
    """
    data_path = Path(data_path)

    if not data_path.exists():
        raise FileNotFoundError(f"Data file not found: {data_path}")

    if verbose:
        print("=" * 60)
        print("Syllable Walker - Web Interface")
        print("=" * 60)
        print(f"\nLoading data from: {data_path}")
        print("This may take a minute for large datasets...\n")

    # Initialize walker (this builds the neighbor graph)
    walker = SyllableWalker(data_path, max_neighbor_distance=max_neighbor_distance, verbose=verbose)

    # Set walker as class attribute (shared across all request handlers)
    WalkerHTTPHandler.walker = walker

    if verbose:
        print("\n" + "=" * 60)
        print("✓ Walker initialized successfully!")
        print("=" * 60)
        print(f"\nStarting web server on port {port}...")
        print(f"Open your browser and navigate to: http://localhost:{port}")
        print("\nPress Ctrl+C to stop the server\n")

    # Create and start HTTP server
    server = HTTPServer(("0.0.0.0", port), WalkerHTTPHandler)  # nosec B104

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        if verbose:
            print("\n\nShutting down server...")
        server.shutdown()
        if verbose:
            print("Server stopped.")
