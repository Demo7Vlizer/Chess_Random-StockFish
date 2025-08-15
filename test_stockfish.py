#!/usr/bin/env python3
"""
Test script to check if Stockfish is working properly
"""

import os
from stockfish import Stockfish

def test_stockfish():
    print("=" * 50)
    print("STOCKFISH CONNECTION TEST")
    print("=" * 50)
    
    # Test paths for your Stockfish installation
    stockfish_paths = [
        r"C:\Users\NAV\Downloads\stockfish-windows-x86-64-avx2\stockfish\stockfish.exe",
        r"C:\Users\NAV\Downloads\stockfish-windows-x86-64-avx2\stockfish\stockfish",
        r"C:\Users\NAV\Downloads\stockfish-windows-x86-64-avx2\stockfish.exe",
        "stockfish.exe",
        "stockfish"
    ]
    
    stockfish = None
    working_path = None
    
    print("Testing Stockfish paths...")
    print()
    
    for i, path in enumerate(stockfish_paths, 1):
        print(f"{i}. Testing: {path}")
        
        # Check if file exists
        if os.path.exists(path):
            print(f"   ✓ File exists")
        else:
            print(f"   ✗ File not found")
            continue
            
        # Try to initialize Stockfish
        try:
            stockfish = Stockfish(path=path)
            working_path = path
            print(f"   ✓ Stockfish initialized successfully!")
            break
        except Exception as e:
            print(f"   ✗ Failed to initialize: {e}")
            continue
    
    print()
    print("=" * 50)
    
    if stockfish:
        print("🎉 SUCCESS! Stockfish is working!")
        print(f"Working path: {working_path}")
        print()
        
        # Test some basic functionality
        print("Testing Stockfish functionality...")
        try:
            # Test if we can set a position
            stockfish.set_position(["e2e4", "e7e5"])
            print("✓ Can set position")
            
            # Test if we can get best move
            best_move = stockfish.get_best_move()
            print(f"✓ Best move: {best_move}")
            
            # Test evaluation
            eval_score = stockfish.get_evaluation()
            print(f"✓ Position evaluation: {eval_score}")
            
            print()
            print("🎯 Stockfish is fully functional!")
            
        except Exception as e:
            print(f"✗ Stockfish initialization worked but functionality failed: {e}")
            
    else:
        print("❌ FAILED! Stockfish not found or not working")
        print()
        print("Troubleshooting steps:")
        print("1. Make sure you downloaded Stockfish from: https://stockfishchess.org/download/")
        print("2. Extract the downloaded file completely")
        print("3. Find the actual stockfish.exe file location")
        print("4. Update the path in the code")
        print()
        print("Expected location based on your info:")
        print(r"C:\Users\NAV\Downloads\stockfish-windows-x86-64-avx2\stockfish\stockfish.exe")

if __name__ == "__main__":
    test_stockfish()
    input("\nPress Enter to exit...")
