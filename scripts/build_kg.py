"""Parse PDFs, extract provenance-bearing facts and build the JSON graph."""
import argparse
import json
import logging
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from dotenv import load_dotenv
from src.ingest.pdf_parser import parse_pdf
from src.extract import table_extractor,metadata_extractor,relation_extractor
from src.graph.builder import build
from src.llm_client import LLMClient
from src.extract.freeze import verify_rules
ROOT=Path(__file__).resolve().parents[1]

def main():
    load_dotenv(ROOT/'.env')
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=ROOT/'data/graph/kg.json',help='Graph destination; scratch builds isolate reports under results/<output stem>')
    parser.add_argument('--tickers',nargs='+')
    parser.add_argument('--limit',type=int)
    parser.add_argument('--offline',action='store_true')
    parser.add_argument('--skip-llm',action='store_true')
    args=parser.parse_args()
    if args.limit is not None and args.limit<1: parser.error('--limit must be positive')
    rules_digest=verify_rules(ROOT)
    logging.basicConfig(level=logging.INFO)
    companies=json.loads((ROOT/'config/companies.json').read_text())
    wanted={t.upper() for t in args.tickers} if args.tickers else None
    if wanted and wanted-{c['ticker'] for c in companies}: parser.error('Unknown ticker')
    paths=sorted((ROOT/'data/pdfs').glob('*.pdf'))
    if wanted: paths=[p for p in paths if p.name.split('_')[0] in wanted]
    if args.limit: paths=paths[:args.limit]
    if not paths: parser.error('No matching PDFs')
    result=ROOT/'results' if args.output.resolve()==(ROOT/'data/graph/kg.json').resolve() else ROOT/'results'/args.output.stem
    facts=[]; summaries={}; relation_stats={}; parse_stats={}; balance_diagnostics={}
    client=LLMClient(offline=args.offline)
    for path in paths:
        ticker=path.name.split('_')[0]; company='COMP:'+ticker
        print('Parsing',path.name,flush=True)
        try:
            pages=parse_pdf(path)
        except Exception as error:
            logging.exception('Failed parsing %s',path.name)
            parse_stats[path.name]={'ticker':ticker,'parsed_cleanly':False,'error':f'{type(error).__name__}: {error}'}
            continue
        parse_stats[path.name]={'ticker':ticker,'parsed_cleanly':True,'pages':len(pages),
                               'text_pages':sum(bool(p.text.strip()) for p in pages),
                               'tables':sum(len(p.tables) for p in pages)}
        print(f'Parsed {path.name}: {len(pages)} pages',flush=True)
        summaries[ticker]={s:[p.page_num for p in pages if p.section==s] for s in sorted({p.section for p in pages})}
        summaries[ticker]['Financial Statements']=[p.page_num for p in pages if 'Financial Statements' in p.signals]
        for page in pages:
            facts.extend(table_extractor.extract(page,company))
            balance_diagnostics.setdefault(company,[]).extend(table_extractor.mezzanine_diagnostics(page))
        facts.extend(metadata_extractor.extract(pages,company))
        relation_stats.setdefault(company,[])
        stats={'source_doc':path.name}
        facts.extend(relation_extractor.extract(pages,company,client,skip_llm=args.skip_llm,stats=stats))
        relation_stats[company].append(stats)
    build(companies,facts,args.output,relation_stats=relation_stats,audit_dir=result,parse_stats=parse_stats,balance_diagnostics=balance_diagnostics,rules_digest=rules_digest)
    result.mkdir(parents=True,exist_ok=True)
    (result/'section_detection.json').write_text(json.dumps(summaries,indent=2))
    observations=[f.model_dump() for f in facts if f.node_type=='MetricObservation']
    (result/'metric_coverage.json').write_text(json.dumps(observations,indent=2))
    (result/'metadata.json').write_text(json.dumps([f.model_dump() for f in facts if f.node_type=='RelationClaim'],indent=2))
    lines=['# Extracted metric observations','', '| Company | Metric | Period | Raw | Scale | Signed USD | Analytical USD | Unit | PDF page |', '|---|---|---|---:|---:|---:|---:|---|---:|']
    for f in sorted(observations,key=lambda f:(f['company_id'],f['metric_id'],f['period'])):
        lines.append(f"| {f['company_id']} | {f['metric_id']} | {f['period']} | {f['value_raw']:.15g} | {f['scale_multiplier']:g} | {f['value_usd']:.2f} | {f['analytical_value_usd']:.2f} | {f['unit']} | {f['page_num']} |")
    (result/'metric_coverage.md').write_text('\n'.join(lines)+'\n')
    print(f'Graph: {args.output}; reports: {result}',flush=True)
    if any(not item['parsed_cleanly'] for item in parse_stats.values()):
        raise SystemExit(1)
if __name__=='__main__': main()
