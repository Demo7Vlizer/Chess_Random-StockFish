import pygame
import chess
import chess.engine
import os
import sys
from stockfish import Stockfish

# Initialize Pygame
pygame.init()

# Constants
BOARD_SIZE = 640
SQUARE_SIZE = BOARD_SIZE // 8
PANEL_WIDTH = 280
WINDOW_WIDTH = BOARD_SIZE + PANEL_WIDTH
WINDOW_HEIGHT = BOARD_SIZE + 200  # Increased height for bottom controls

# Colors
WHITE = (240, 217, 181)
BLACK = (181, 136, 99)
HIGHLIGHT = (255, 255, 0, 128)
TEXT_COLOR = (255, 255, 255)
BUTTON_COLOR = (74, 144, 226)
BUTTON_HOVER = (100, 170, 255)

class ChessGame:
    def __init__(self):
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Chess - Drag & Drop vs Stockfish")
        
        # Initialize difficulty mode FIRST (needed for Stockfish initialization)
        self.difficulty_mode = "normal"  # "easy", "normal", "strongest"
        
        # Game state
        self.setup_mode = True
        self.game_started = False
        self.user_color = None  # Will be set to chess.WHITE or chess.BLACK
        self.board = chess.Board(fen=None)  # Empty board for setup
        self.board.clear()  # Start with empty board
        
        # Piece palette for setup mode
        self.show_piece_palette = True
        self.palette_pieces = [
            (chess.KING, chess.WHITE), (chess.KING, chess.BLACK),
            (chess.QUEEN, chess.WHITE), (chess.QUEEN, chess.BLACK),
            (chess.ROOK, chess.WHITE), (chess.ROOK, chess.BLACK),
            (chess.BISHOP, chess.WHITE), (chess.BISHOP, chess.BLACK),
            (chess.KNIGHT, chess.WHITE), (chess.KNIGHT, chess.BLACK),
            (chess.PAWN, chess.WHITE), (chess.PAWN, chess.BLACK),
        ]
        
        # Dragging state
        self.dragging_piece = None
        self.dragging_from_palette = False
        self.drag_offset = (0, 0)
        
        # Stockfish setup - using your specific path
        try:
            # Try your Stockfish path and common alternatives
            stockfish_paths = [
                r"C:\Users\NAV\Downloads\stockfish-windows-x86-64-avx2\stockfish\stockfish-windows-x86-64-avx2.exe",
                r"C:\Users\NAV\Downloads\stockfish-windows-x86-64-avx2\stockfish\stockfish.exe",
                r"C:\Users\NAV\Downloads\stockfish-windows-x86-64-avx2\stockfish\stockfish",
                "stockfish.exe",
                "stockfish",
                "./stockfish.exe",
                "./stockfish"
            ]
            
            self.stockfish = None
            for path in stockfish_paths:
                try:
                    # Configure Stockfish with better initial parameters
                    self.stockfish = Stockfish(path=path, depth=8, parameters={
                        "Threads": 2,
                        "Hash": 32,
                        "UCI_Elo": 1500,  # Will be updated based on difficulty
                        "Skill Level": 8   # Will be updated based on difficulty
                    })
                    
                    # Set initial difficulty
                    self.update_stockfish_difficulty()
                    print(f"Stockfish 17.1 loaded successfully from: {path}")
                    break
                except Exception as e:
                    print(f"Failed to load from {path}: {e}")
                    continue
                    
            if not self.stockfish:
                print("Warning: Stockfish not found at any of the expected paths.")
                print(f"Please ensure stockfish.exe is at: C:\\Users\\NAV\\Downloads\\stockfish-windows-x86-64-avx2\\stockfish\\")
                
        except Exception as e:
            print(f"Error initializing Stockfish: {e}")
            self.stockfish = None
        
        # Load piece images
        self.piece_images = self.load_piece_images()
        
        # Drag and drop
        self.dragging = False
        self.dragged_piece = None
        self.drag_pos = (0, 0)
        self.selected_square = None
        
        # Game state
        self.move_count = 0
        self.max_moves = 5
        self.max_moves_user = float('inf')  # Unlimited moves for user
        self.game_over = False
        self.game_result = ""
        
        # Move limit options for Stockfish
        self.move_options = ["Unlimited", "5", "6", "7", "8", "9", "10"]
        self.selected_move_option = 1  # Default to "5"
        
        # Undo/Redo functionality
        self.move_history = []  # Stack of moves for undo
        self.redo_history = []  # Stack of moves for redo
        
        # Board rotation
        self.board_flipped = False  # False = White at bottom, True = Black at bottom
        
        # Window state
        self.fullscreen = False
        self.original_size = (WINDOW_WIDTH, WINDOW_HEIGHT)
        
        # Fonts
        self.font = pygame.font.Font(None, 24)
        self.big_font = pygame.font.Font(None, 36)
        
        # Buttons - Right panel (simplified)
        self.buttons = {
            'start': pygame.Rect(BOARD_SIZE + 20, 50, 160, 40),
            'white': pygame.Rect(BOARD_SIZE + 20, 100, 75, 30),
            'black': pygame.Rect(BOARD_SIZE + 105, 100, 75, 30),
            'move_limit': pygame.Rect(BOARD_SIZE + 20, 140, 160, 30),
            'mate_puzzle': pygame.Rect(BOARD_SIZE + 20, 180, 160, 30),
            'reset': pygame.Rect(BOARD_SIZE + 20, 220, 160, 40),
            'clear': pygame.Rect(BOARD_SIZE + 20, 270, 160, 40),
            'undo': pygame.Rect(BOARD_SIZE + 20, 310, 75, 30),
            'redo': pygame.Rect(BOARD_SIZE + 105, 310, 75, 30),
            'rotate': pygame.Rect(BOARD_SIZE + 20, 350, 160, 30)
        }
        
        # Bottom panel buttons
        self.bottom_buttons = {
            'easy': pygame.Rect(20, BOARD_SIZE + 20, 120, 35),
            'normal': pygame.Rect(150, BOARD_SIZE + 20, 120, 35),
            'strongest': pygame.Rect(280, BOARD_SIZE + 20, 120, 35),
            'minimize': pygame.Rect(410, BOARD_SIZE + 20, 100, 35),
            'fullscreen': pygame.Rect(520, BOARD_SIZE + 20, 100, 35)
        }
        
        # Setup default position or empty board
        self.setup_initial_pieces()

    def load_piece_images(self):
        images = {}
        piece_files = {
            'P': 'Pawn_White.png',    # White Pawn
            'R': 'Rook_White.png',    # White Rook
            'N': 'Knight_White.png',  # White Knight
            'B': 'Bishop_White.png',  # White Bishop
            'Q': 'Queen_White.png',   # White Queen
            'K': 'King_White.png',    # White King
            'p': 'Pawn.png',          # Black Pawn
            'r': 'Rook.png',          # Black Rook
            'n': 'Knight.png',        # Black Knight
            'b': 'Bishop.png',        # Black Bishop
            'q': 'Queen.png',         # Black Queen
            'k': 'King.png'           # Black King
        }
        
        for piece, filename in piece_files.items():
            try:
                path = os.path.join('Chess_All', filename)
                img = pygame.image.load(path)
                img = pygame.transform.scale(img, (SQUARE_SIZE - 10, SQUARE_SIZE - 10))
                images[piece] = img
            except pygame.error as e:
                print(f"Could not load {filename}: {e}")
                # Create a placeholder
                surf = pygame.Surface((SQUARE_SIZE - 10, SQUARE_SIZE - 10))
                surf.fill((255, 0, 0))
                images[piece] = surf
        
        return images

    def toggle_fullscreen(self):
        """Toggle between fullscreen and windowed mode"""
        if self.fullscreen:
            # Return to windowed mode
            self.screen = pygame.display.set_mode(self.original_size)
            self.fullscreen = False
            print("Switched to windowed mode")
        else:
            # Switch to fullscreen
            self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
            self.fullscreen = True
            print("Switched to fullscreen mode")

    def minimize_window(self):
        """Minimize the window"""
        pygame.display.iconify()
        print("Window minimized")

    def update_stockfish_difficulty(self):
        """Update Stockfish parameters based on difficulty mode"""
        if self.stockfish is None:
            return
            
        print(f"Updating Stockfish to {self.difficulty_mode} mode...")
            
        if self.difficulty_mode == "easy":
            # Easy mode: very weak player, makes mistakes
            self.stockfish.set_skill_level(1)  # Very low skill
            self.stockfish.set_elo_rating(600)  # Very low rating
            self.stockfish.set_depth(2)  # Very shallow search
            print("Easy mode: Stockfish will play very weakly")
        elif self.difficulty_mode == "strongest":
            # Strongest mode: maximum strength, quick checkmates
            self.stockfish.set_skill_level(20)  # Maximum skill
            self.stockfish.set_elo_rating(3200)  # Maximum rating
            self.stockfish.set_depth(15)  # Deeper search for strongest mode
            print("Strongest mode: Stockfish will play at maximum strength")
        else:  # normal mode
            # Normal mode: balanced
            self.stockfish.set_skill_level(8)  # Medium skill
            self.stockfish.set_elo_rating(1500)  # Medium rating
            self.stockfish.set_depth(6)  # Medium search
            print("Normal mode: Stockfish will play at medium strength")

    def setup_initial_pieces(self):
        """Set up a default chess position for easy editing"""
        # Standard starting position
        starting_fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
        self.board = chess.Board(starting_fen)

    def setup_mate_puzzle(self):
        """Set up a position where Stockfish can deliver mate in 5 or fewer moves"""
        # Famous "Légal's mate" position - Stockfish should win quickly
        # This is a position where White (Stockfish) has a clear winning advantage
        mate_fen = "rnbqk2r/pppp1ppp/5n2/2b1p3/2B1P3/3P1N2/PPP2PPP/RNBQK2R w KQkq - 0 4"
        
        try:
            self.board = chess.Board(mate_fen)
            # Set move limit to 5 for the challenge
            self.selected_move_option = 1  # "5" moves
            self.max_moves = 5
            # Force strongest mode for the puzzle
            self.difficulty_mode = "strongest"
            self.update_stockfish_difficulty()
            print("Mate puzzle loaded! Stockfish should win in 5 moves or less.")
            print("Set your color and click Start Game!")
        except Exception as e:
            print(f"Error loading mate puzzle: {e}")
            # Fallback to a simpler winning position
            simple_mate_fen = "6k1/5ppp/8/8/8/8/5PPP/4R1K1 w - - 0 1"
            self.board = chess.Board(simple_mate_fen)
            print("Loaded simpler mate puzzle")

    def square_to_coords(self, square):
        """Convert chess square to screen coordinates"""
        file = chess.square_file(square)
        rank = chess.square_rank(square)
        
        if self.board_flipped:
            x = (7 - file) * SQUARE_SIZE  # Flip horizontally
            y = rank * SQUARE_SIZE        # Flip vertically
        else:
            x = file * SQUARE_SIZE
            y = (7 - rank) * SQUARE_SIZE
        return x, y

    def coords_to_square(self, x, y):
        """Convert screen coordinates to chess square"""
        if x < 0 or x >= BOARD_SIZE or y < 0 or y >= BOARD_SIZE:
            return None
        
        if self.board_flipped:
            file = 7 - (x // SQUARE_SIZE)  # Flip horizontally
            rank = y // SQUARE_SIZE        # Flip vertically
        else:
            file = x // SQUARE_SIZE
            rank = 7 - (y // SQUARE_SIZE)
        return chess.square(file, rank)

    def draw_board(self):
        """Draw the chess board with border"""
        # Draw board border
        border_width = 4
        border_color = (101, 67, 33)  # Dark brown border
        border_rect = pygame.Rect(-border_width, -border_width, 
                                 BOARD_SIZE + 2*border_width, BOARD_SIZE + 2*border_width)
        pygame.draw.rect(self.screen, border_color, border_rect)
        
        # Draw squares
        for rank in range(8):
            for file in range(8):
                color = WHITE if (rank + file) % 2 == 0 else BLACK
                rect = pygame.Rect(file * SQUARE_SIZE, rank * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE)
                pygame.draw.rect(self.screen, color, rect)
                
                # Add coordinate labels
                if file == 0:  # Rank labels
                    if self.board_flipped:
                        rank_label = str(rank + 1)  # Flipped rank numbers
                    else:
                        rank_label = str(8 - rank)  # Normal rank numbers
                    text = self.font.render(rank_label, True, (0, 0, 0))
                    self.screen.blit(text, (5, rank * SQUARE_SIZE + 5))
                
                if rank == 7:  # File labels
                    if self.board_flipped:
                        file_label = chr(ord('h') - file)  # Flipped file letters
                    else:
                        file_label = chr(ord('a') + file)  # Normal file letters
                    text = self.font.render(file_label, True, (0, 0, 0))
                    self.screen.blit(text, (file * SQUARE_SIZE + SQUARE_SIZE - 15, BOARD_SIZE - 20))

    def draw_pieces(self):
        """Draw pieces on the board"""
        for square in chess.SQUARES:
            piece = self.board.piece_at(square)
            if piece and not (self.dragging and square == self.selected_square):
                piece_symbol = piece.symbol()
                if piece_symbol in self.piece_images:
                    x, y = self.square_to_coords(square)
                    self.screen.blit(self.piece_images[piece_symbol], (x + 5, y + 5))
                    
    def draw_piece_palette(self):
        """Draw piece palette for piece selection"""
        if not self.show_piece_palette or not self.setup_mode:
            return
            
        # Palette background
        palette_x = BOARD_SIZE + 10
        palette_y = 500
        palette_width = PANEL_WIDTH - 20
        palette_height = 200
        
        pygame.draw.rect(self.screen, (40, 40, 40), 
                        (palette_x, palette_y, palette_width, palette_height))
        pygame.draw.rect(self.screen, (80, 80, 80), 
                        (palette_x, palette_y, palette_width, palette_height), 2)
        
        # Title
        title = self.font.render("Piece Palette", True, TEXT_COLOR)
        self.screen.blit(title, (palette_x + 10, palette_y + 10))
        
        # Draw pieces in a grid
        piece_size = 40
        pieces_per_row = 2
        start_x = palette_x + 15
        start_y = palette_y + 40
        
        for i, (piece_type, color) in enumerate(self.palette_pieces):
            row = i // pieces_per_row
            col = i % pieces_per_row
            
            x = start_x + col * 80
            y = start_y + row * 45
            
            # Create piece object to get symbol
            piece = chess.Piece(piece_type, color)
            piece_symbol = piece.symbol()
            
            # Piece background
            piece_rect = pygame.Rect(x, y, piece_size, piece_size)
            if color:  # White pieces
                pygame.draw.rect(self.screen, (200, 200, 200), piece_rect)
            else:  # Black pieces
                pygame.draw.rect(self.screen, (50, 50, 50), piece_rect)
            pygame.draw.rect(self.screen, (100, 100, 100), piece_rect, 1)
            
            # Draw piece image if available
            if piece_symbol in self.piece_images:
                piece_img = pygame.transform.scale(self.piece_images[piece_symbol], (piece_size-4, piece_size-4))
                self.screen.blit(piece_img, (x + 2, y + 2))
                
        # Instructions
        inst_text = self.font.render("Drag pieces to board", True, TEXT_COLOR)
        self.screen.blit(inst_text, (palette_x + 10, palette_y + 170))
        
    def get_palette_piece_at(self, pos):
        """Get piece from palette at given position"""
        if not self.show_piece_palette or not self.setup_mode:
            return None
            
        x, y = pos
        palette_x = BOARD_SIZE + 10
        palette_y = 500
        
        piece_size = 40
        pieces_per_row = 2
        start_x = palette_x + 15
        start_y = palette_y + 40
        
        for i, (piece_type, color) in enumerate(self.palette_pieces):
            row = i // pieces_per_row
            col = i % pieces_per_row
            
            piece_x = start_x + col * 80
            piece_y = start_y + row * 45
            
            piece_rect = pygame.Rect(piece_x, piece_y, piece_size, piece_size)
            if piece_rect.collidepoint(pos):
                return chess.Piece(piece_type, color)
                
        return None

    def draw_ui(self):
        """Draw the user interface"""
        # Right panel background
        panel_rect = pygame.Rect(BOARD_SIZE, 0, PANEL_WIDTH, WINDOW_HEIGHT)
        pygame.draw.rect(self.screen, (40, 40, 40), panel_rect)
        
        # Title
        title = self.big_font.render("Chess Setup", True, TEXT_COLOR)
        self.screen.blit(title, (BOARD_SIZE + 20, 10))
        
        # Color selection
        if self.setup_mode:
            color_text = self.font.render("Choose Color:", True, TEXT_COLOR)
            self.screen.blit(color_text, (BOARD_SIZE + 20, 105))
            
            if self.user_color is not None:
                selected_text = f"Selected: {'White' if self.user_color == chess.WHITE else 'Black'}"
                selected_surface = self.font.render(selected_text, True, (0, 255, 0))
                self.screen.blit(selected_surface, (BOARD_SIZE + 20, 135))
            else:
                # Show instruction if no color selected
                instruction_text = "Please select a color first!"
                instruction_surface = self.font.render(instruction_text, True, (255, 255, 0))
                self.screen.blit(instruction_surface, (BOARD_SIZE + 20, 135))
            
            # Note about difficulty controls
            note_text = "Difficulty controls moved to bottom panel"
            note_surface = self.font.render(note_text, True, (150, 150, 150))
            self.screen.blit(note_surface, (BOARD_SIZE + 20, 160))
        
        # Start button
        start_color = BUTTON_HOVER if self.user_color is not None else (100, 100, 100)
        pygame.draw.rect(self.screen, start_color, self.buttons['start'])
        start_text = self.font.render("Start Game", True, TEXT_COLOR)
        self.screen.blit(start_text, (BOARD_SIZE + 60, 60))
        
        # Color buttons
        white_color = BUTTON_HOVER if self.user_color == chess.WHITE else BUTTON_COLOR
        black_color = BUTTON_HOVER if self.user_color == chess.BLACK else BUTTON_COLOR
        
        pygame.draw.rect(self.screen, white_color, self.buttons['white'])
        white_text = self.font.render("White", True, TEXT_COLOR)
        self.screen.blit(white_text, (BOARD_SIZE + 35, 105))
        
        pygame.draw.rect(self.screen, black_color, self.buttons['black'])
        black_text = self.font.render("Black", True, TEXT_COLOR)
        self.screen.blit(black_text, (BOARD_SIZE + 120, 105))
        
        # Move limit selection
        pygame.draw.rect(self.screen, BUTTON_COLOR, self.buttons['move_limit'])
        move_text = f"Stockfish: {self.move_options[self.selected_move_option]} moves"
        if self.move_options[self.selected_move_option] == "Unlimited":
            move_text = "Stockfish: Unlimited moves"
        move_limit_text = self.font.render(move_text, True, TEXT_COLOR)
        self.screen.blit(move_limit_text, (BOARD_SIZE + 25, 147))
        
        # Mate puzzle button
        pygame.draw.rect(self.screen, (255, 140, 0), self.buttons['mate_puzzle'])  # Orange color
        puzzle_text = self.font.render("🎯 Mate in 5 Puzzle", True, TEXT_COLOR)
        self.screen.blit(puzzle_text, (BOARD_SIZE + 30, 187))
        
        # Reset button
        pygame.draw.rect(self.screen, BUTTON_COLOR, self.buttons['reset'])
        reset_text = self.font.render("Reset Board", True, TEXT_COLOR)
        self.screen.blit(reset_text, (BOARD_SIZE + 40, 230))
        
        # Clear button
        pygame.draw.rect(self.screen, BUTTON_COLOR, self.buttons['clear'])
        clear_text = self.font.render("Clear Board", True, TEXT_COLOR)
        self.screen.blit(clear_text, (BOARD_SIZE + 45, 280))
        
        # Undo button
        undo_color = BUTTON_COLOR if self.move_history else (100, 100, 100)
        pygame.draw.rect(self.screen, undo_color, self.buttons['undo'])
        undo_text = self.font.render("↶ Undo", True, TEXT_COLOR)
        self.screen.blit(undo_text, (BOARD_SIZE + 25, 317))
        
        # Redo button
        redo_color = BUTTON_COLOR if self.redo_history else (100, 100, 100)
        pygame.draw.rect(self.screen, redo_color, self.buttons['redo'])
        redo_text = self.font.render("↷ Redo", True, TEXT_COLOR)
        self.screen.blit(redo_text, (BOARD_SIZE + 110, 317))
        
        # Rotate board button
        pygame.draw.rect(self.screen, BUTTON_COLOR, self.buttons['rotate'])
        rotate_text = f"🔄 Flip Board ({'Black' if self.board_flipped else 'White'} view)"
        self.screen.blit(self.font.render(rotate_text, True, TEXT_COLOR), (BOARD_SIZE + 25, 357))
        
        # Game status
        if self.game_started:
            status_y = 320
            
            # Move counter for Stockfish
            if self.max_moves == float('inf'):
                moves_text = f"Stockfish moves: {self.move_count} / ∞"
            else:
                moves_text = f"Stockfish moves: {self.move_count}/{self.max_moves}"
            moves_surface = self.font.render(moves_text, True, TEXT_COLOR)
            self.screen.blit(moves_surface, (BOARD_SIZE + 20, status_y))
            
            # User moves (unlimited)
            user_moves_text = f"Your moves: {self.move_count} / ∞"
            user_moves_surface = self.font.render(user_moves_text, True, TEXT_COLOR)
            self.screen.blit(user_moves_surface, (BOARD_SIZE + 20, status_y + 25))
            
            # Turn indicator
            turn_text = "Your turn" if self.board.turn == self.user_color else "Stockfish thinking..."
            turn_surface = self.font.render(turn_text, True, TEXT_COLOR)
            self.screen.blit(turn_surface, (BOARD_SIZE + 20, status_y + 50))
            
            # Game result
            if self.game_result:
                result_surface = self.font.render(self.game_result, True, (255, 255, 0))
                self.screen.blit(result_surface, (BOARD_SIZE + 20, status_y + 75))
        else:
            # Instructions
            instructions = [
                "Instructions:",
                "1. Drag pieces to set up",
                "2. Choose your color",
                "3. Click move limit button",
                "4. Click Start Game",
                "5. You have unlimited moves!",
                "6. Stockfish has limited moves"
            ]
            
            for i, line in enumerate(instructions):
                text = self.font.render(line, True, TEXT_COLOR)
                self.screen.blit(text, (BOARD_SIZE + 20, 320 + i * 25))

    def handle_mouse_down(self, pos):
        """Handle mouse button down events"""
        x, y = pos
        
        # Check UI buttons
        if self.buttons['start'].collidepoint(pos):
            if self.user_color is not None:
                print(f"Starting game as {'White' if self.user_color == chess.WHITE else 'Black'}")
                self.start_game()
            else:
                print("Cannot start game: No color selected!")
        elif self.buttons['white'].collidepoint(pos) and self.setup_mode:
            self.user_color = chess.WHITE
            print("Selected White")
        elif self.buttons['black'].collidepoint(pos) and self.setup_mode:
            self.user_color = chess.BLACK
            print("Selected Black")
        elif self.buttons['reset'].collidepoint(pos):
            print("Resetting board")
            self.reset_board()
        elif self.buttons['clear'].collidepoint(pos):
            print("Clearing board")
            self.clear_board()
        elif self.buttons['undo'].collidepoint(pos):
            self.undo_move()
        elif self.buttons['redo'].collidepoint(pos):
            self.redo_move()
        elif self.buttons['move_limit'].collidepoint(pos) and self.setup_mode:
            # Cycle through move limit options
            self.selected_move_option = (self.selected_move_option + 1) % len(self.move_options)
            if self.move_options[self.selected_move_option] == "Unlimited":
                self.max_moves = float('inf')
                print("Selected: Unlimited moves")
            else:
                self.max_moves = int(self.move_options[self.selected_move_option])
                print(f"Selected: {self.max_moves} moves")
        elif self.buttons['mate_puzzle'].collidepoint(pos) and self.setup_mode:
            print("Setting up Mate in 5 puzzle...")
            self.setup_mate_puzzle()
        elif self.buttons['rotate'].collidepoint(pos):
            self.board_flipped = not self.board_flipped
            view_name = "Black" if self.board_flipped else "White"
            print(f"Board flipped to {view_name} view")
        # Check bottom panel buttons first
        for button_name, rect in self.bottom_buttons.items():
            if rect.collidepoint(pos):
                if button_name == 'easy':
                    self.difficulty_mode = "easy"
                    self.update_stockfish_difficulty()
                    print("Selected Easy mode - Stockfish will play weakly")
                    return
                elif button_name == 'normal':
                    self.difficulty_mode = "normal"
                    self.update_stockfish_difficulty()
                    print("Selected Normal mode - Stockfish will play balanced")
                    return
                elif button_name == 'strongest':
                    self.difficulty_mode = "strongest"
                    self.update_stockfish_difficulty()
                    print("Selected Strongest mode - Stockfish will play at maximum strength")
                    return
                elif button_name == 'minimize':
                    self.minimize_window()
                    return
                elif button_name == 'fullscreen':
                    self.toggle_fullscreen()
                    return
        else:
            # Check for palette piece click first
            palette_piece = self.get_palette_piece_at(pos)
            if palette_piece and self.setup_mode:
                print(f"Selected piece from palette: {palette_piece.symbol()}")
                self.dragging = True
                self.dragging_from_palette = True
                self.dragged_piece = palette_piece
                self.drag_pos = pos
                self.selected_square = None
            elif x < BOARD_SIZE and y < BOARD_SIZE:  # Click on board
                square = self.coords_to_square(x, y)
                if square is not None:
                    if self.setup_mode:
                        # Setup mode: start dragging piece
                        piece = self.board.piece_at(square)
                        if piece:
                            self.dragging = True
                            self.dragging_from_palette = False
                            self.selected_square = square
                            self.dragged_piece = piece
                            self.drag_pos = pos
                            # Remove piece from board temporarily
                            self.board.remove_piece_at(square)
                    elif self.game_started and self.board.turn == self.user_color:
                        # Game mode: make move
                        self.handle_game_move(square)

    def handle_mouse_up(self, pos):
        """Handle mouse button up events"""
        if self.dragging:
            x, y = pos
            target_square = self.coords_to_square(x, y)
            
            if target_square is not None:
                # Place piece on target square
                self.board.set_piece_at(target_square, self.dragged_piece)
                print(f"Placed {self.dragged_piece.symbol()} on {chess.square_name(target_square)}")
            elif not self.dragging_from_palette and self.selected_square is not None:
                # Return piece to original position (only if dragged from board)
                self.board.set_piece_at(self.selected_square, self.dragged_piece)
            
            # Reset dragging state
            self.dragging = False
            self.dragging_from_palette = False
            self.selected_square = None
            self.dragged_piece = None

    def handle_mouse_motion(self, pos):
        """Handle mouse motion events"""
        if self.dragging:
            self.drag_pos = pos

    def handle_game_move(self, square):
        """Handle player moves during the game"""
        # Simple click-to-move system
        if self.selected_square is None:
            # Select piece
            piece = self.board.piece_at(square)
            if piece and piece.color == self.user_color:
                self.selected_square = square
        else:
            # Try to make move
            move = chess.Move(self.selected_square, square)
            
            # Check for promotion
            piece = self.board.piece_at(self.selected_square)
            if piece and piece.piece_type == chess.PAWN:
                if (piece.color == chess.WHITE and chess.square_rank(square) == 7) or \
                   (piece.color == chess.BLACK and chess.square_rank(square) == 0):
                    move = chess.Move(self.selected_square, square, promotion=chess.QUEEN)
            
            if move in self.board.legal_moves:
                self.board.push(move)
                self.move_history.append(move)  # Record move for undo
                self.redo_history.clear()  # Clear redo history when new move is made
                self.selected_square = None
                
                # Check game state
                if self.board.is_checkmate():
                    if self.max_moves == float('inf'):
                        self.game_result = "You won! Stockfish couldn't checkmate you!"
                    else:
                        self.game_result = f"You won! Stockfish couldn't mate in {self.max_moves}!"
                    self.game_over = True
                elif self.board.is_stalemate():
                    self.game_result = "Stalemate!"
                    self.game_over = True
                else:
                    # Stockfish's turn
                    self.make_stockfish_move()
            else:
                self.selected_square = None

    def start_game(self):
        """Start the game with current board position"""
        if self.user_color is None:
            return
            
        # Ensure position is valid by adding kings if missing
        self.ensure_valid_position()
            
        self.setup_mode = False
        self.game_started = True
        self.show_piece_palette = False  # Hide palette during game
        self.move_count = 0
        self.game_over = False
        self.game_result = ""
        
        # Set the turn based on user color
        # If user is black, stockfish goes first
        if self.user_color == chess.BLACK:
            self.make_stockfish_move()
            
    def ensure_valid_position(self):
        """Ensure the position has kings and is valid"""
        # Check if kings exist
        white_king_exists = any(piece.piece_type == chess.KING and piece.color == chess.WHITE 
                               for piece in self.board.piece_map().values())
        black_king_exists = any(piece.piece_type == chess.KING and piece.color == chess.BLACK 
                               for piece in self.board.piece_map().values())
        
        # Add missing kings
        if not white_king_exists:
            # Find empty square for white king
            for square in [chess.E1, chess.D1, chess.F1, chess.C1, chess.G1]:
                if self.board.piece_at(square) is None:
                    self.board.set_piece_at(square, chess.Piece(chess.KING, chess.WHITE))
                    print(f"Added white king at {chess.square_name(square)}")
                    break
                    
        if not black_king_exists:
            # Find empty square for black king
            for square in [chess.E8, chess.D8, chess.F8, chess.C8, chess.G8]:
                if self.board.piece_at(square) is None:
                    self.board.set_piece_at(square, chess.Piece(chess.KING, chess.BLACK))
                    print(f"Added black king at {chess.square_name(square)}")
                    break

    def make_stockfish_move(self):
        """Make a move with Stockfish"""
        if self.stockfish is None or self.game_over or (self.max_moves != float('inf') and self.move_count >= self.max_moves):
            if self.max_moves != float('inf') and self.move_count >= self.max_moves and not self.board.is_checkmate():
                self.game_result = f"You survived! Stockfish failed to mate in {int(self.max_moves)}!"
                self.game_over = True
            return
        
        try:
            # Set the current position directly (position should be valid now)
            self.stockfish.set_fen_position(self.board.fen())
            
            # Get best move based on difficulty with time limits for responsiveness
            if self.difficulty_mode == "strongest":
                # In strongest mode, give more time for maximum strength
                print("Strongest mode: Stockfish thinking deeply...")
                best_move = self.stockfish.get_best_move_time(2000)  # 2 seconds max for maximum strength
            elif self.difficulty_mode == "easy":
                # In easy mode, very quick thinking
                print("Easy mode: Stockfish thinking quickly...")
                best_move = self.stockfish.get_best_move_time(200)  # 0.2 seconds max
            else:
                # Normal mode
                print("Normal mode: Stockfish thinking...")
                best_move = self.stockfish.get_best_move_time(500)  # 0.5 seconds max
            
            if best_move and best_move != "None":
                move = chess.Move.from_uci(best_move)
                if move in self.board.legal_moves:
                    self.board.push(move)
                    self.move_history.append(move)  # Record Stockfish move for undo
                    self.redo_history.clear()  # Clear redo history when new move is made
                    self.move_count += 1
                    
                    # Check game state
                    if self.board.is_checkmate():
                        self.game_result = f"Stockfish wins in {self.move_count} moves!"
                        self.game_over = True
                    elif self.max_moves != float('inf') and self.move_count >= self.max_moves:
                        if not self.board.is_checkmate():
                            self.game_result = f"You survived! Stockfish failed to mate in {int(self.max_moves)}!"
                        self.game_over = True
                    elif self.board.is_stalemate():
                        self.game_result = "Stalemate!"
                        self.game_over = True
                        
        except Exception as e:
            print(f"Stockfish error: {e}")
            # Try to restart Stockfish if it crashed
            try:
                self.restart_stockfish()
            except:
                print("Failed to restart Stockfish")
                self.stockfish = None

    def restart_stockfish(self):
        """Restart Stockfish if it crashes"""
        print("Attempting to restart Stockfish...")
        stockfish_paths = [
            r"C:\Users\NAV\Downloads\stockfish-windows-x86-64-avx2\stockfish\stockfish-windows-x86-64-avx2.exe",
            r"C:\Users\NAV\Downloads\stockfish-windows-x86-64-avx2\stockfish\stockfish.exe",
            "stockfish.exe",
            "stockfish"
        ]
        
        for path in stockfish_paths:
            try:
                self.stockfish = Stockfish(path=path, depth=8, parameters={
                    "Threads": 2,
                    "Hash": 32,
                    "UCI_Elo": 1500,  # Will be updated based on difficulty
                    "Skill Level": 8   # Will be updated based on difficulty
                })
                # Update to current difficulty mode
                self.update_stockfish_difficulty()
                print(f"Stockfish restarted successfully from: {path}")
                return True
            except Exception as e:
                continue
        return False

    def reset_board(self):
        """Reset to starting position"""
        self.setup_initial_pieces()
        self.setup_mode = True
        self.game_started = False
        self.game_over = False
        self.game_result = ""
        self.move_count = 0

    def clear_board(self):
        """Clear all pieces from board and show piece palette"""
        self.board.clear()
        self.setup_mode = True
        self.game_started = False
        self.game_over = False
        self.game_result = ""
        self.show_piece_palette = True
        
    def undo_move(self):
        """Undo the last move"""
        if not self.move_history:
            print("No moves to undo")
            return
            
        # Get the last move and remove it from history
        last_move = self.move_history.pop()
        
        # Add to redo history
        self.redo_history.append(last_move)
        
        # Undo the move on the board
        try:
            self.board.pop()  # chess.Board.pop() undoes the last move
            self.move_count = max(0, self.move_count - 1)
            print(f"Undid move: {last_move}")
        except Exception as e:
            print(f"Error undoing move: {e}")
            
    def redo_move(self):
        """Redo the last undone move"""
        if not self.redo_history:
            print("No moves to redo")
            return
            
        # Get the move from redo history
        move = self.redo_history.pop()
        
        # Add back to move history
        self.move_history.append(move)
        
        # Apply the move to the board
        try:
            self.board.push(move)
            self.move_count += 1
            print(f"Redid move: {move}")
        except Exception as e:
            print(f"Error redoing move: {e}")

    def draw_dragged_piece(self):
        """Draw the piece being dragged"""
        if self.dragging and self.dragged_piece:
            piece_symbol = self.dragged_piece.symbol()
            if piece_symbol in self.piece_images:
                x, y = self.drag_pos
                # Center the piece on the cursor
                self.screen.blit(self.piece_images[piece_symbol], 
                               (x - SQUARE_SIZE // 2, y - SQUARE_SIZE // 2))

    def draw_bottom_panel(self):
        """Draw the bottom control panel"""
        # Bottom panel background
        bottom_rect = pygame.Rect(0, BOARD_SIZE, WINDOW_WIDTH, 200)
        pygame.draw.rect(self.screen, (60, 60, 60), bottom_rect)
        pygame.draw.rect(self.screen, (100, 100, 100), bottom_rect, 2)
        
        # Title
        title_text = self.big_font.render("Game Controls", True, TEXT_COLOR)
        self.screen.blit(title_text, (20, BOARD_SIZE + 5))
        
        # Difficulty selection
        difficulty_text = self.font.render("Difficulty Level:", True, TEXT_COLOR)
        self.screen.blit(difficulty_text, (20, BOARD_SIZE + 45))
        
        # Difficulty buttons
        for button_name, rect in self.bottom_buttons.items():
            if button_name in ['easy', 'normal', 'strongest']:
                # Difficulty buttons
                if button_name == self.difficulty_mode:
                    color = BUTTON_HOVER
                else:
                    color = BUTTON_COLOR
                    
                pygame.draw.rect(self.screen, color, rect, border_radius=5)
                pygame.draw.rect(self.screen, (120, 120, 120), rect, 1, border_radius=5)
                
                # Button text
                if button_name == 'easy':
                    text = "Easy"
                elif button_name == 'normal':
                    text = "Normal"
                else:
                    text = "Strongest"
                    
                text_surface = self.font.render(text, True, TEXT_COLOR)
                text_rect = text_surface.get_rect(center=rect.center)
                self.screen.blit(text_surface, text_rect)
                
            elif button_name == 'minimize':
                # Minimize button
                pygame.draw.rect(self.screen, (200, 100, 100), rect, border_radius=5)
                pygame.draw.rect(self.screen, (120, 120, 120), rect, 1, border_radius=5)
                text_surface = self.font.render("Minimize", True, TEXT_COLOR)
                text_rect = text_surface.get_rect(center=rect.center)
                self.screen.blit(text_surface, text_rect)
                
            elif button_name == 'fullscreen':
                # Fullscreen button
                if self.fullscreen:
                    pygame.draw.rect(self.screen, (100, 200, 100), rect, border_radius=5)
                    text = "Windowed"
                else:
                    pygame.draw.rect(self.screen, (100, 100, 200), rect, border_radius=5)
                    text = "Fullscreen"
                    
                pygame.draw.rect(self.screen, (120, 120, 120), rect, 1, border_radius=5)
                text_surface = self.font.render(text, True, TEXT_COLOR)
                text_rect = text_surface.get_rect(center=rect.center)
                self.screen.blit(text_surface, text_rect)
        
        # Current difficulty display
        current_diff = f"Current: {self.difficulty_mode.title()}"
        diff_surface = self.font.render(current_diff, True, (0, 255, 0))
        self.screen.blit(diff_surface, (20, BOARD_SIZE + 70))
        
        # Move limit info
        if self.max_moves == float('inf'):
            moves_info = "Stockfish has unlimited moves"
        else:
            moves_info = f"Stockfish has {self.max_moves} moves to checkmate you"
        moves_surface = self.font.render(moves_info, True, TEXT_COLOR)
        self.screen.blit(moves_surface, (20, BOARD_SIZE + 95))
        
        # User moves info
        user_moves_info = "You have unlimited moves!"
        user_moves_surface = self.font.render(user_moves_info, True, (0, 255, 255))
        self.screen.blit(user_moves_surface, (20, BOARD_SIZE + 120))

    def run(self):
        """Main game loop"""
        clock = pygame.time.Clock()
        running = True
        
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    self.handle_mouse_down(event.pos)
                elif event.type == pygame.MOUSEBUTTONUP:
                    self.handle_mouse_up(event.pos)
                elif event.type == pygame.MOUSEMOTION:
                    self.handle_mouse_motion(event.pos)
            
            # Clear screen
            self.screen.fill((40, 40, 40))
            
            # Draw everything
            self.draw_board()
            self.draw_pieces()
            self.draw_ui()
            self.draw_piece_palette()
            self.draw_dragged_piece()
            self.draw_bottom_panel()  # Add bottom panel
            
            # Highlight selected square in game mode
            if self.game_started and self.selected_square is not None:
                x, y = self.square_to_coords(self.selected_square)
                highlight_surf = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE))
                highlight_surf.set_alpha(128)
                highlight_surf.fill((255, 255, 0))
                self.screen.blit(highlight_surf, (x, y))
            
            pygame.display.flip()
            clock.tick(60)
        
        pygame.quit()

if __name__ == "__main__":
    game = ChessGame()
    game.run()
