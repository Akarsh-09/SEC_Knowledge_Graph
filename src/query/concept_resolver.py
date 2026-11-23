"""Deterministic boundary-aware aliases with conservative token-window fuzzy matching."""
import re
from difflib import SequenceMatcher
from config.ontology import METRIC_SYNONYMS, ENTITY_ALIASES, RELATION_TYPES, FISCAL_PERIODS, CanonicalMetric
from src.entity_names import entity_key

def normalize(text: str) -> str:
    return ' '.join(re.sub(r'[^a-z0-9]+',' ',text.casefold()).split())
FORMULA_ALIASES={
 'OPERATING_MARGIN':['operating margin'], 'NET_MARGIN':['net margin','net profit margin'],
 'GROSS_MARGIN':['gross margin'], 'RD_INTENSITY':['r d intensity','research and development intensity'],
 'DEBT_TO_EQUITY':['debt to equity'], 'FREE_CASH_FLOW':['free cash flow'],
 'YOY_GROWTH':['year over year','yoy','growth'], 'RATIO':['ratio'], 'DIFF':['difference','minus'],
}
RELATION_ALIASES={'AUDITED_BY':['audited by','auditor','audits'], 'HEADQUARTERED_IN':['headquarters','headquartered','hq'],
 'INCORPORATED_IN':['incorporated','incorporation'], 'FISCAL_YEAR_END':['fiscal year end'],
 'ACQUIRED':['acquired','acquisition'], 'DEPENDS_ON_SUPPLIER':['supplier','depends on'],
 'MAJOR_CUSTOMER':['major customer'], 'HAS_CEO':['ceo','chief executive'], 'COMPETES_WITH':['competitor','competes'],
 'OPERATES_SEGMENT':['segments','segment'], 'FACES_RISK':['risk','risks']}


def _external_aliases(nodes):
    """Prefer a unique full legal name over an equivalent bare-name node.

    This grounds aliases to existing nodes only. Two distinct legal forms remain
    ambiguous; neither graph facts nor entity nodes are merged or rewritten.
    """
    roots={}
    def root(name):
        return re.sub(r'(?: (?:holding|holdings))? (?:limited|ltd|inc|incorporated|corp|corporation|llc|llp|plc)$','',entity_key(name))
    for id,data in nodes.items():roots.setdefault(root(data['name']),[]).append(id)
    preferred={id:id for id in nodes}
    for name,ids in roots.items():
        legal=[id for id in ids if entity_key(nodes[id]['name'])!=name]
        if len(legal)==1:
            for id in ids:preferred[id]=legal[0]
    aliases=[(alias,preferred[id]) for alias,id in ENTITY_ALIASES.items() if id in nodes]
    for id,data in nodes.items():
        aliases.extend([(data['name'],preferred[id]),(id,preferred[id])])
        short=root(data['name'])
        if len(short)>=4:aliases.append((short,preferred[id]))
    return list(dict.fromkeys(aliases))


def resolve(question: str, store) -> dict:
    text=normalize(question)
    def contains(alias): return bool(re.search(r'(?<!\w)'+re.escape(normalize(alias))+r'(?!\w)',text))
    companies=[]
    for alias,id in store.companies.items():
        if contains(alias) and id not in companies: companies.append(id)
    companies.sort(key=lambda id: min((text.find(normalize(a)) for a,c in store.companies.items() if c==id and contains(a)),default=len(text)))
    if not companies:
        words=text.split()
        for alias,id in store.companies.items():
            a=normalize(alias)
            if len(a)<5 or alias.startswith('comp:'): continue
            size=len(a.split())
            if any(SequenceMatcher(None,a,' '.join(words[i:i+size])).ratio()>=.92 for i in range(len(words)-size+1)):
                if id not in companies: companies.append(id)
    metrics=[]; metric_positions={}
    extra={'REVENUE':['total net revenue'],'RD_EXPENSE':['r d expense','r d spending'],'CAPEX':['capex'],
           'EPS_DILUTED':['eps'],'SHAREHOLDERS_EQUITY':['equity'],'NET_INTEREST_INCOME':['net interest income'],
           'NONINTEREST_REVENUE':['noninterest revenue']}
    for metric in CanonicalMetric:
        aliases=list(METRIC_SYNONYMS.get(metric.value,()))+extra.get(metric.value,[])+[metric.value]
        positions=[text.find(normalize(a)) for a in aliases if contains(a)]
        if positions:
            id='METRIC:'+metric.value;metrics.append(id);metric_positions[id]=min(positions)
    metrics.sort(key=lambda id:metric_positions[id])
    formulas=[id for id,aliases in FORMULA_ALIASES.items() if any(contains(a) for a in aliases)]
    # A specific phrase owns its component nouns (e.g. net interest income is not revenue).
    if 'METRIC:NONINTEREST_REVENUE' in metrics and 'METRIC:REVENUE' in metrics: metrics.remove('METRIC:REVENUE')
    external=[]
    nodes={id:d for id,d in store.graph.nodes(data=True) if d['node_type']=='ExternalEntity'}
    aliases=_external_aliases(nodes)
    external_text=entity_key(question,question=True)
    mentions=[]
    for alias,id in aliases:
        for match in re.finditer(r'(?<!\w)'+re.escape(entity_key(alias))+r'(?!\w)',external_text):
            mentions.append((match.start(),match.end(),id))
    for start,end,id in sorted(set(mentions),key=lambda m:(m[0],-(m[1]-m[0]),m[2])):
        if any(a<=start and end<=b and b-a>end-start for a,b,_ in mentions):continue
        if id not in external:external.append(id)
    unresolved=[]
    for year in re.findall(r'\b(?:FY\s*)?(20\d{2})\b',question,re.I):
        if 'FY'+year not in FISCAL_PERIODS:unresolved.append('FY'+year)
    known_tickers={d['ticker'] for _,d in store.graph.nodes(data=True) if d['node_type']=='Company'}
    company_words={word for alias in store.companies for word in normalize(alias).split()}
    metric_names={m.value for m in CanonicalMetric}
    exemptions={'FY','USD','EPS','CEO','HQ','GAAP','FCF','YOY','R','D','AND','OR','THE','WHAT','WHICH','HOW','IN','BY','OF','TO','EY','PWC','RD'}
    for token in re.findall(r'\b[A-Z][A-Z0-9]{1,5}\b',question):
        if token not in exemptions and not re.fullmatch(r'FY\d{4}',token) and token not in known_tickers and token.casefold() not in company_words and token not in metric_names:
            if not any(token.casefold() in normalize(a).split() or
                       re.search(r'(?<!\w)'+re.escape(entity_key(token))+r'(?!\w)',entity_key(a))
                       for a,id in aliases if id in external): unresolved.append(token)
    # Detect an extra named company in standard comparison lists, even if another resolved.
    named=re.search(r'(?i)(?:among|between)\s+(.+?)(?=\s+(?:audited|by|in|had|which|what)|[,;]\s*(?:which|what)|[?]|$)',question)
    if named:
        for part in re.split(r',|\band\b|\bor\b',named[1],flags=re.I):
            candidate=normalize(part)
            if not candidate: continue
            if not any(re.search(r'(?<!\w)'+re.escape(normalize(a))+r'(?!\w)',candidate) for a in store.companies):
                if not any(normalize(s) in candidate or 'companies' in candidate for s in store.sectors): unresolved.append(part.strip())
    sector_aliases={'Semiconductors':['semiconductor'],'Big Tech & Cloud':['big tech','cloud'],
                    'Financials':['banks','financial companies'],'Healthcare & Pharma':['healthcare','pharma'],
                    'Retail & Consumer':['retail','consumer companies']}
    return {'unresolved_qualifiers':list(dict.fromkeys(unresolved)),'company_ids':companies,'metric_ids':metrics,'formula_ids':formulas,
            'sectors':[s for s in store.sectors if contains(s) or any(contains(a) for a in sector_aliases.get(s,[]))],
            'period_ids':list(dict.fromkeys('FY'+y for y in re.findall(r'\b(?:fy\s*)?(20\d{2})\b',question,re.I) if 'FY'+y in FISCAL_PERIODS)),
            'relation_types':[r for r in RELATION_TYPES if any(contains(a) for a in RELATION_ALIASES.get(r,[]))],
            'external_entity_ids':external,
            'external_entities':[{'node_id':id,'name':nodes[id]['name']} for id in external]}
