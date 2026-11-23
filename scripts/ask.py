"""Ask a graph-only financial question and print its complete execution record."""
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from dotenv import load_dotenv
from src.query.synthesizer import ask

def main():
    load_dotenv(Path(__file__).resolve().parents[1]/'.env')
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('question')
    parser.add_argument('--offline',action='store_true')
    args=parser.parse_args()
    print(json.dumps(ask(args.question,offline=args.offline),indent=2))
if __name__=='__main__':main()
