"""Search a local filing or display exact physical PDF page text for human review."""
import argparse
from pathlib import Path
import pymupdf

ROOT=Path(__file__).resolve().parents[2]

def main() -> None:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('pdf',type=Path,help='PDF path or filename under data/pdfs')
    parser.add_argument('--page',type=int,help='Physical 1-indexed PDF page')
    parser.add_argument('--search',help='Case-insensitive literal keyword search')
    parser.add_argument('--context',type=int,default=160,help='Context characters around search hits')
    args=parser.parse_args()
    if not args.page and not args.search:parser.error('Specify --page or --search')
    if args.context<0:parser.error('--context must be nonnegative')
    path=args.pdf if args.pdf.is_file() else ROOT/'data/pdfs'/args.pdf
    with pymupdf.open(path) as doc:
        if args.page is not None and not 1<=args.page<=len(doc):parser.error(f'--page must be in 1..{len(doc)}')
        indices=[args.page-1] if args.page else range(len(doc))
        for index in indices:
            text=doc[index].get_text(sort=True)
            if not args.search:
                print(f'[{path.name}, p. {index+1}]\n{text}')
            else:
                start=0
                while True:
                    hit=text.lower().find(args.search.lower(),start)
                    if hit<0:break
                    line_end=text.find('\n',hit+len(args.search))
                    if line_end<0:line_end=len(text)
                    end=max(line_end,hit+len(args.search)+args.context)
                    print(f'[{path.name}, p. {index+1}]\n{text[max(0,hit-args.context):end]}\n')
                    start=hit+max(1,len(args.search))

if __name__=='__main__':main()
