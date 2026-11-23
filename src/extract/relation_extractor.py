"""Capped qualitative extraction with normalized matching and original evidence."""
import logging
import re
from pydantic import BaseModel, Field
from config.ontology import ENTITY_ALIASES
from src.llm_client import OfflineCacheMiss
from src.extract.metadata_extractor import claim
from src.graph.entity_resolution import canonicalize

LOG = logging.getLogger(__name__)
QUALITATIVE = ('ACQUIRED','DEPENDS_ON_SUPPLIER','MAJOR_CUSTOMER','HAS_CEO',
               'COMPETES_WITH','OPERATES_SEGMENT','FACES_RISK')
PROMPT_VERSION = "v3"
SYSTEM_PROMPT = (
    f'SEC qualitative extraction PROMPT_VERSION={PROMPT_VERSION}. Return only JSON. '
    'Use this exact object/field structure (synthetic example, not a source fact): '
    '{"claims":[{"relation_type":"OPERATES_SEGMENT","target_name":"Regional Services",'
    '"page_num":12,"verbatim_quote":"Our reportable segments include Regional Services."}]}. '
    'Use the actual supplied physical PDF page number, not the example number. '
    'Return {"claims":[]} when the page has no supported facts. '
    'Extract ONLY completed or current relationships explicitly stated affirmatively in the supplied page. '
    'Definitions: OPERATES_SEGMENT = an explicitly named current reportable/operating business segment '
    '(ASC 280) or business unit; a product or brand is not automatically a segment. '
    'HAS_CEO = the named current Chief Executive Officer or Principal Executive Officer; '
    'exclude former officers and announced future appointments. '
    'ACQUIRED = a completed, consummated acquisition of a named entity/business; never pending deals, '
    'agreements awaiting closing/approval, plans, intentions or hypothetical acquisitions. '
    'DEPENDS_ON_SUPPLIER = an explicit current dependency on a specifically named external supplier; '
    'unnamed/general supplier exposure is insufficient for this predicate. '
    'MAJOR_CUSTOMER = a specifically named external entity explicitly identified as a current major '
    'customer or customer-concentration relationship. '
    'COMPETES_WITH = a specifically named external competitor and an explicit current competitive relationship; '
    'do not infer competitors from industry knowledge. '
    'FACES_RISK = an affirmatively stated current exposure; target_name must be a short exact risk/exposure '
    'phrase appearing in the quote, not an invented risk label, mere section heading, or hypothetical future event. '
    'For every relation, copy target_name from the evidence (or use an established entity alias). '
    'Reject speculation, negations, conditional/forward-looking statements and unsupported inferences. '
    '**Copy `verbatim_quote` as ONE exact, contiguous substring directly from the page text as printed. '
    'NEVER reorder words, skip intervening dates/lines, or stitch together text from separate table columns. '
    'If the entity name and role sit in separate columns, copy the exact contiguous span that includes both '
    'in the order they appear in the text.** '
    'Preserve intervening signature markers, dates, punctuation and lines, even if the span is longer. '
    'If no supported contiguous span contains the named target and relationship, omit the claim. '
    'Do not copy the synthetic example as evidence. Do not emit deterministic metadata predicates such as '
    'AUDITED_BY, HEADQUARTERED_IN or INCORPORATED_IN. Allowed relations: '+', '.join(QUALITATIVE)+'.'
)
SEGMENT_TERMS = ('segment information','reportable segments','reportable segment','operating segments',
                 'operating segment','chief operating decision maker','segment reporting')
EXECUTIVE_TERMS = ('chief executive officer','principal executive officer')
KEYWORDS = ('business combinations','business combination','acquisition','acquired','completed acquisition',
            'single source','single-source','sole source','sole-source','supplier concentration',
            'customer concentration','major customer','10% or more','10%','competition','competes with',
            'principal risk factors','principal risk','risk factors')

class Candidate(BaseModel):
    relation_type: str
    target_name: str = Field(min_length=1)
    page_num: int
    verbatim_quote: str = Field(min_length=1)
class Candidates(BaseModel):
    claims: list[Candidate]

def normalized_with_offsets(text: str) -> tuple[str, list[int]]:
    """Map each normalized character back to its original PDF-text position."""
    chars=[]; positions=[]
    wraps = {i for m in re.finditer(r'-[ \t]*\r?\n[ \t]*',text) for i in range(m.start(),m.end())}
    for i,c in enumerate(text):
        if i in wraps: continue
        c=c.translate(str.maketrans({'’':"'",'‘':"'",'“':'"','”':'"','\xa0':' '}))
        if c.isspace():
            if chars and chars[-1]!=' ': chars.append(' ');positions.append(i)
        else:
            for lower in c.casefold(): chars.append(lower);positions.append(i)
    return ''.join(chars), positions

def normalize(text: str) -> str:
    return normalized_with_offsets(text)[0].strip()

def verified_snippet(candidate, page) -> str | None:
    if candidate.page_num!=page.page_num or candidate.relation_type not in QUALITATIVE: return None
    quote=normalize(candidate.verbatim_quote)
    if not quote: return None
    target=canonicalize(candidate.target_name)
    aliases=[candidate.target_name]+[a for a,id in ENTITY_ALIASES.items() if id==target]
    if not any(re.search(r'(?<!\w)'+re.escape(normalize(a))+r'(?!\w)',quote) for a in aliases): return None
    normalized, offsets=normalized_with_offsets(page.text)
    start=normalized.find(quote)
    if start<0: return None
    return page.text[offsets[start]:offsets[start+len(quote)-1]+1]

def verify(candidate, page) -> bool:
    return verified_snippet(candidate,page) is not None

def select_candidate_pages(pages):
    """Reserve 3 business, 2 segment and 2 officer slots; fill remaining slots by density.

    A page is counted once. Vacant reserved slots return to the remainder pool. Output
    is in physical page order, with deterministic page-number tie breaks. Contents,
    cover forms, auditor reports and exhibit-only boilerplate are not filler pages.
    """
    nonempty=sorted((p for p in pages if p.text.strip() and p.section!='Table of Contents'),key=lambda p:p.page_num)
    texts={p.page_num:normalize(p.text) for p in nonempty}
    selected={}

    def density(page,terms):
        text=texts[page.page_num]
        return sum(text.count(term) for term in terms)/max(1,len(text.split()))

    def reserve(candidates,limit):
        if limit<=0:return
        count=0
        for page in candidates:
            if page.page_num in selected:continue
            selected[page.page_num]=page
            count+=1
            if count>=limit:break

    reserve([p for p in nonempty if p.section=='Item 1'],3)
    segments=[p for p in nonempty if p.section not in ('Cover','Auditor Report') and density(p,SEGMENT_TERMS)>0]
    segments.sort(key=lambda p:(-density(p,SEGMENT_TERMS),p.page_num))
    reserve(segments,2)
    executives=[p for p in nonempty if p.section not in ('Cover','Auditor Report') and density(p,EXECUTIVE_TERMS)>0
                and (p.section=='Item 10' or re.search(r'(?i)signatures?|executive officers?|/s/',p.text))]
    executives.sort(key=lambda p:(-density(p,EXECUTIVE_TERMS),p.page_num))
    reserve(executives,2)
    remainder=[p for p in nonempty if p.section not in ('Cover','Auditor Report','Item 15','Item 16')
               and density(p,KEYWORDS)>0]
    remainder.sort(key=lambda p:(-density(p,KEYWORDS),p.page_num))
    reserve(remainder,10-len(selected))
    return sorted(selected.values(),key=lambda p:p.page_num)


def extract(pages, company_id, client, *, skip_llm=False, stats=None):
    selected=select_candidate_pages(pages)
    LOG.info('%s candidate_pages=%d',company_id,len(selected))
    stats = stats if stats is not None else {}
    stats.update(candidate_pages_selected=len(selected), candidate_pages_sent=0, pages_replayed=0,
                 accepted_claims=0, rejected_by_provenance_gate=0, offline_cache_misses=0,
                 mode='skipped' if skip_llm else 'offline' if client.offline else 'live_or_cache')
    if skip_llm: return []
    accepted=[];rejected=0;misses=0
    for page in selected:
        system = SYSTEM_PROMPT
        try:
            result,source=client.structured(system,f'Company: {company_id}; PDF page {page.page_num}\n{page.text}',Candidates)
        except OfflineCacheMiss:
            misses+=1;continue
        stats['candidate_pages_sent'] += int(source=='llm_live')
        stats['pages_replayed'] += int(source=='llm_cache')
        for c in result.claims:
            snippet=verified_snippet(c,page)
            if snippet is not None: accepted.append(claim(page,company_id,c.relation_type,c.target_name,snippet))
            else: rejected+=1
    stats.update(accepted_claims=len(accepted), rejected_by_provenance_gate=rejected, offline_cache_misses=misses)
    LOG.info('Relation gate accepted=%d rejected=%d offline_cache_misses=%d',len(accepted),rejected,misses)
    return accepted
