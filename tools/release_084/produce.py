"""One bounded production chunk; network recovery reuses saved provider originals."""
import json
import sys
import time
from batching import main as generate
from providers import OUT
from salvage import main as salvage
from pipeline import guard


def main(secrets):
    guard()
    salvage()
    generate(secrets,max_batches=8,max_seconds=90)


if __name__=='__main__':main(json.load(sys.stdin))
