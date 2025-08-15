# Chess Game - Drag & Drop vs Stockfish

A Python chess game where you can set up custom positions and challenge Stockfish to checkmate you in 5 moves!

## Features
- Drag and drop piece placement to create custom positions
- Choose to play as white or black
- Stockfish AI opponent with 5-move limit
- Beautiful chess piece graphics with transparent backgrounds
- Interactive GUI with pygame

## Setup

1. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Download Stockfish:**
   - Download Stockfish from: https://stockfishchess.org/download/
   - Extract `stockfish.exe` to the chess folder (same directory as main.py)
   - Or place it anywhere and update the path in the code

3. **Run the game:**
   ```bash
   python main.py
   ```

## How to Play

### Setup Phase:
1. **Arrange pieces:** Drag and drop pieces to create your desired position
2. **Choose color:** Click "White" or "Black" to select your side
3. **Start game:** Click "Start Game" to begin

### Game Phase:
1. **Make moves:** Click a piece, then click the destination square
2. **Stockfish challenge:** Stockfish will try to checkmate you in exactly 5 moves
3. **Win condition:** Survive the 5 moves or checkmate Stockfish to win!

## Controls
- **Drag & Drop:** Move pieces around in setup mode
- **Click to Move:** Select piece, then destination in game mode
- **Reset Board:** Return to standard starting position
- **Clear Board:** Remove all pieces for custom setup

## Requirements
- Python 3.7+
- pygame
- python-chess
- stockfish (engine executable)

Have fun creating challenging positions and see if you can survive Stockfish's 5-move attack!
