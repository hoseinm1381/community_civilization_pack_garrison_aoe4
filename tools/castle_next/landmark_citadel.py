"""Scratch Imperial Citadel visual, Garrison building-source/v1.

Run only in a dedicated factory-startup background Blender process. The shared
launcher holds native-build.lock. This file never edits the active mod.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from landmark_shared import build

if __name__ == '__main__':
    build('imperial_citadel')
