"""
HTTP web server 
This server provides REST API endpoints for the game and serves the web interface.
"""

import sys
import re
from pathlib import Path
from aiohttp import web
import asyncio

from board import Board
from commands import look, flip, map_command, watch


class WebServer:
    """
    Provides REST API endpoints for the Memory Scramble game.
    """
    
    def __init__(self, board: Board, port: int):
        """
        Make a new web game server using board that listens on port.
        
        Args:
            board: A board
            port
        """
        self.board = board
        self.port = port
        self.app = web.Application()
        self._setup_routes()
    
    def _setup_routes(self):
        #Configure HTTP routes.
        self.app.router.add_get('/look/{player_id}', self.handle_look)
        self.app.router.add_get('/flip/{player_id}/{location}', self.handle_flip)
        self.app.router.add_get('/watch/{player_id}', self.handle_watch)
        
        # Serve static files
        public_dir = Path(__file__).parent.parent / 'public'
        if public_dir.exists():
            self.app.router.add_static('/', public_dir, name='static')
    
    async def handle_look(self, request: web.Request) -> web.Response:
        """
        Handle GET /look/<player_id>
        
        Args:
            request: HTTP request with player_id in path
        
        Returns:
            Board state from player's perspective
        """
        player_id = request.match_info['player_id']
        
        # Validate player_id
        if not re.match(r'^[a-zA-Z0-9_]+$', player_id):
            return web.Response(text="Invalid player ID", status=400)
        
        try:
            board_state = await look(self.board, player_id)
            return web.Response(text=board_state, content_type='text/plain')
        except Exception as e:
            return web.Response(text=str(e), status=500)
    
    async def handle_flip(self, request: web.Request) -> web.Response:
        """
        Handle GET /flip/<player_id>/<row>,<column>
        
        Args:
            request: HTTP request with player_id and location in path
        
        Returns:
            Board state after the flip from player's perspective
        """
        player_id = request.match_info['player_id']
        location = request.match_info['location']
        
        # Validate player_id
        if not re.match(r'^[a-zA-Z0-9_]+$', player_id):
            return web.Response(text="Invalid player ID", status=400)
        
        # Parse location
        try:
            parts = location.split(',')
            if len(parts) != 2:
                raise ValueError("Location must be row,column")
            row = int(parts[0])
            column = int(parts[1])
        except (ValueError, IndexError) as e:
            return web.Response(text=f"Invalid location: {e}", status=400)
        
        try:
            board_state = await flip(self.board, player_id, row, column)
            return web.Response(text=board_state, content_type='text/plain')
        except ValueError as e:
            # Return 409 Conflict for flip failures 
            return web.Response(text=str(e), status=409)
        except Exception as e:
            return web.Response(text=str(e), status=500)
    
    async def handle_watch(self, request: web.Request) -> web.Response:
        """
        Handle GET /watch/<player_id>
        
        Args:
            request: HTTP request with player_id in path
        
        Returns:
            Updated board state from player's perspective
        """
        player_id = request.match_info['player_id']
        
        # Validate player_id
        if not re.match(r'^[a-zA-Z0-9_]+$', player_id):
            return web.Response(text="Invalid player ID", status=400)
        
        try:
            board_state = await watch(self.board, player_id)
            return web.Response(text=board_state, content_type='text/plain')
        except Exception as e:
            return web.Response(text=str(e), status=500)
    
    async def start(self):
        """Start the web server."""
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, 'localhost', self.port)
        await site.start()
        
        # Get actual port if 0 was specified
        actual_port = site._server.sockets[0].getsockname()[1]
        print(f"Server started on http://localhost:{actual_port}")
        print(f"Open http://localhost:{actual_port}/index.html to play")
        
        # Keep server running
        try:
            await asyncio.Event().wait()
        except KeyboardInterrupt:
            print("\nShutting down server...")
            await runner.cleanup()


async def main():
    #Start a game server using command-line arguments.
    if len(sys.argv) < 3:
        print("Usage: python server.py PORT FILENAME")
        print("  PORT: server port number (0 for random)")
        print("  FILENAME: path to board file")
        sys.exit(1)
    
    try:
        port = int(sys.argv[1])
        if port < 0:
            raise ValueError("Port must be non-negative")
    except ValueError as e:
        print(f"Invalid PORT: {e}")
        sys.exit(1)
    
    filename = sys.argv[2]
    
    try:
        board = await Board.parse_from_file(filename)
        server = WebServer(board, port)
        await server.start()
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    asyncio.run(main())
