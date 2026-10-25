"""Production units through the qualified native cook route, immutable labels."""
from cook_pilot import module
from common import *
if __name__=='__main__':module.main(read(RECIPES/'unit-selection.json'),sys.argv[1])
