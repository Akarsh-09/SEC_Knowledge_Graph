"""Conservative primary-statement rows, period alignment and table-cell fallback.

All numeric observations require explicit scale (except EPS), exact column counts,
verbatim page evidence, and a recognized whole row label. Equal-priority conflicts
are rejected, not resolved by guessing. No missing totals are manufactured.
"""
import hashlib
import re
from config.ontology import METRIC_SYNONYMS
from src.graph.schema import MetricObservationNode
from src.ingest.pdf_parser import ParsedPage, statement_kind, STATEMENT

NUMBER = re.compile(r'\(\s*-?\d[\d,]*(?:\.\d+)?\s*\)|-?\d[\d,]*(?:\.\d+)?|[—–-]')

def normalize(text: str) -> str:
    return ' '.join(text.lower().replace('’',"'").replace('‘',"'").replace('\xa0',' ').split()).strip(' :.;')

def clean_label(text: str) -> str:
    text=normalize(text)
    # Remove note references/abbreviation glosses, retaining semantic (loss)/(deficit).
    text=re.sub(r'\((?:notes?\b[^)]*|\d+(?:\s*[,–-]\s*\d+)*|[a-z](?:\s*,\s*[a-z])*|cor|r&d|included\b[^)]*|see\b[^)]*)\)','',text)
    return normalize(text)

def parse_number(text: str) -> float:
    text=text.strip().replace('$','').replace(',','').replace(' ','')
    if text in ('—','–','-'):return 0.0
    if text.startswith('(') and text.endswith(')'):return -float(text[1:-1])
    return float(text)

def detect_scale(text: str, *, per_share: bool=False) -> float | None:
    if per_share:return 1.0
    match=re.search(r'(?:\bin\s+|\(\s*|\$\s*)(billions|millions|thousands)\b',text,re.I)
    if match:return {'billions':1e9,'millions':1e6,'thousands':1e3}[match[1].lower()]
    if re.search(r'\bin (?:dollars|USD)\b|unscaled',text,re.I):return 1.0
    return None

def parse_fiscal_years(text: str) -> list[str]:
    return list(dict.fromkeys('FY'+y for y in re.findall(r'\b(20\d{2})\b',text)))

def column_years(text: str) -> list[str]:
    choices=[parse_fiscal_years(line) for line in text.splitlines()]
    choices=[years for years in choices if 2<=len(years)<=4]
    return max(choices,key=len) if choices else parse_fiscal_years(text)

def vector(text: str) -> list[float] | None:
    text=re.sub(r'\([a-z]\)','',text,flags=re.I)
    tokens=list(NUMBER.finditer(text))
    residue=NUMBER.sub('',text)
    if not tokens or re.sub(r'[\s$]','',residue):return None
    try:return [parse_number(m[0]) for m in tokens]
    except ValueError:return None

SYNONYMS={clean_label(a):m for m,aliases in METRIC_SYNONYMS.items() for a in aliases}

def metric_label(label: str, *, eps_mode: str | None=None, noncurrent: bool=False):
    label=clean_label(label)
    if label=='term debt':return ('LONG_TERM_DEBT',0) if noncurrent else (None,0)
    if label in ('diluted','diluted earnings','diluted net income') and eps_mode:return 'EPS_DILUTED',0
    if eps_mode and re.search(r'net (?:income|earnings)',label):
        return ('EPS_DILUTED',0) if eps_mode=='diluted' else (None,0)
    metric=SYNONYMS.get(label)
    if metric:
        priority=0
        if metric=='REVENUE':priority=0 if label.startswith('total ') else 1
        return metric,priority
    if re.fullmatch(r'net (?:income|earnings)(?: \(loss\))? (?:attributable|applicable|available) to .+',label):
        if re.search(r'non.?controlling|\bnci\b|per .?share',label):return None,0
        return 'NET_INCOME',2
    if re.match(r'^capital expenditures\b',label):return 'CAPEX',1
    if re.fullmatch(r'(?:purchases|payments|additions|acquisitions)(?: (?:for|of|to acquire|related to))? (?:property|plant|equipment)[a-z ,&-]*',label):return 'CAPEX',1
    return None,0


def split_row(line: str, count: int):
    for separator in re.finditer(r'\s{2,}|\s+(?=\$|\(?-?\d|[—–])',line):
        label=line[:separator.start()].strip()
        if not label or not re.search(r'[A-Za-z]',label):continue
        values=vector(line[separator.end():])
        if values is not None and len(values)==count:return label,values
    return None


def original_table_span(page: ParsedPage, label: str, values: list[float]) -> str | None:
    """Admit fallback rows only when label and amounts can be found in original text."""
    words=label.split()
    if not words:return None
    pattern=r'\s+'.join(re.escape(w) for w in words)
    for match in re.finditer(pattern,page.text,re.I):
        end=page.text.find('\n',match.end())
        if end<0:end=len(page.text)
        for _ in range(4):
            block=page.text[match.end():end]
            numbers=vector(block)
            if numbers==values:
                start=page.text.rfind('\n',0,match.start())+1
                return page.text[start:end]
            following=page.text.find('\n',end+1)
            if following<0:following=len(page.text)
            if following==end:break
            end=following
    return None


def extract(page: ParsedPage, company_id: str) -> list[MetricObservationNode]:
    if 'Financial Statements' not in page.signals or page.section=='Table of Contents':return []
    lines=page.text[page.statement_start:].splitlines()
    header=page.statement_header+'\n'+'\n'.join(lines[:24])
    years=column_years(header)
    if not years or len(years)>4:return []
    scale=detect_scale(header)
    kind=page.statement_kind
    if not kind:
        title=STATEMENT.search(header)
        kind=statement_kind(title['title']) if title else 'income'
    allowed={'cash_flow':{'OPERATING_CASH_FLOW','CAPEX'},'balance':{'CASH_AND_EQUIVALENTS','TOTAL_ASSETS','TOTAL_LIABILITIES','LONG_TERM_DEBT','SHAREHOLDERS_EQUITY'}}.get(kind,set(METRIC_SYNONYMS)-{'OPERATING_CASH_FLOW','CAPEX','TOTAL_ASSETS','TOTAL_LIABILITIES','SHAREHOLDERS_EQUITY','LONG_TERM_DEBT','CASH_AND_EQUIVALENTS'})
    candidates={};eps_mode=None;noncurrent=False
    def admit(label,values,snippet,priority_offset=0):
        metric,priority=metric_label(label,eps_mode=eps_mode,noncurrent=noncurrent)
        if metric not in allowed or (scale is None and metric!='EPS_DILUTED'):return
        candidates.setdefault(metric,[]).append((priority+priority_offset,label,values,snippet))
    prior=[]
    for i,line in enumerate(lines):
        if re.match(r'^\s*\(a\)\s',line):break
        if re.search(r'non[- ]current liabilities',line,re.I):noncurrent=True
        text=normalize(line)
        if re.search(r'(?:earnings|income).*per.*share|per.*share.*(?:earnings|income)',text):eps_mode='general'
        if 'diluted' in text and ('per share' in text or eps_mode):eps_mode='diluted'
        if re.match(r'^basic\b',text) and eps_mode:eps_mode='basic'
        if re.search(r'(?:shares used|weighted.average.*shares|average common shares|share computation)',text):eps_mode=None
        row=split_row(line,len(years))
        if row is None:
            values_only=vector(line)
            if values_only is not None and len(values_only)==len(years):
                for length in (1,2):
                    if len(prior)>=length and all(split_row(s,len(years)) is None for _,s in prior[-length:]):
                        fragments=prior[-length:]
                        admit(' '.join(s.strip() for _,s in fragments),values_only,'\n'.join(lines[fragments[0][0]:i+1]))
        if row:
            label,values=row
            admit(label,values,line)
            # Only join preceding nonnumeric label fragments, never prior data rows.
            for length in (1,2):
                if len(prior)>=length:
                    fragment=prior[-length:]
                    if all(split_row(s,len(years)) is None for _,s in fragment):
                        label2=' '.join([s.strip() for _,s in fragment]+[label])
                        snippet='\n'.join(lines[fragment[0][0]:i+1])
                        admit(label2,values,snippet)
        if line.strip():prior=(prior+[(i,line)])[-2:]
    # Grid fallback is subordinate to aligned text and requires original-page evidence.
    for table in page.tables:
        table_header='\n'.join(' '.join(c or '' for c in row) for row in table[:6])
        table_years=column_years(table_header)
        if table_years and table_years!=years:continue
        for row in table:
            cells=[c for c in row if c and c.strip() and c.strip()!='$']
            if len(cells)<2:continue
            label=cells[0];values=vector(' '.join(cells[1:]))
            if values is None or len(values)!=len(years):continue
            snippet=original_table_span(page,label,values)
            if snippet:admit(label,values,snippet,10)
    facts=[]
    for metric,choices in candidates.items():
        best=min(c[0] for c in choices);choices=[c for c in choices if c[0]==best]
        if len({tuple(c[2]) for c in choices})!=1:continue
        _,label,values,snippet=choices[0]
        multiplier=1.0 if metric=='EPS_DILUTED' else scale
        for period,raw in zip(years,values):
            identity=f'{company_id}|{page.source_doc}|{page.page_num}|{metric}|{period}|{snippet}'
            facts.append(MetricObservationNode(id='FACT:'+hashlib.sha256(identity.encode()).hexdigest()[:20],company_id=company_id,
                source_doc=page.source_doc,page_num=page.page_num,section=page.section,snippet=snippet,metric_id='METRIC:'+metric,
                period=period,value_raw=raw,scale_multiplier=multiplier,value_usd=raw*multiplier,raw_label=label,
                unit='USD/share' if metric=='EPS_DILUTED' else 'USD',audited=True))
    return facts


def mezzanine_diagnostics(page: ParsedPage) -> list[dict]:
    """Report separately presented redeemable/temporary equity; never balance by inference."""
    if page.statement_kind!='balance' or 'Financial Statements' not in page.signals:return []
    header=page.statement_header+'\n'+'\n'.join(page.text.splitlines()[:24])
    years=column_years(header);scale=detect_scale(header)
    if not years or scale is None:return []
    results=[]
    for line in page.text.splitlines():
        row=split_row(line,len(years))
        if not row:continue
        label,values=row
        if not re.match(r'^(?:redeemable\s+(?:non[- ]?controlling\s+interests?|preferred\s+(?:stock|shares))|(?:temporary|mezzanine)\s+equity)\b',normalize(label)):continue
        results.append(dict(source_doc=page.source_doc,page_num=page.page_num,section=page.section,snippet=line,
            raw_label=label,scale_multiplier=scale,values=[dict(period=y,value_raw=v,value_usd=v*scale) for y,v in zip(years,values)],
            note='Separately labeled redeemable/temporary equity (ASC 480-10-S99-3A scope may apply). The strict Assets - (Liabilities + Equity) residual is unchanged; no balancing value is fabricated.'))
    return results
