#!/usr/bin/env python3
"""
MORI Token Scoring Discrepancy - Bug Analysis and Fix
"""

def analyze_bug():
    print("🔍 MORI SCORING BUG ANALYSIS")
    print("=" * 50)

    print("\n1. THE BUG:")
    print("- MORI shows score 100.0 in high conviction summary")  
    print("- MORI shows score 34.0 in current cycle breakdown")
    print("- This is caused by session registry not updating existing tokens")

    print("\n2. ROOT CAUSE:")
    print("- _update_session_registry only adds NEW tokens")
    print("- Existing tokens never get updated with better scores")
    print("- Session preserves stale high scores")
    print("- Cycle breakdown shows current accurate scores")

    print("\n3. THE FIX:")
    print("Add logic to update existing token records with better scores")

if __name__ == "__main__":
    analyze_bug()
