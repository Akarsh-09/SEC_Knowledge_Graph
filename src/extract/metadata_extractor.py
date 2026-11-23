"""Caption-anchored cover addresses and explicit audit signatures, with original evidence."""
import hashlib
import re
from src.graph.schema import RelationClaimNode
from src.graph.entity_resolution import canonicalize

# Postal vocabulary, not issuer-specific rules. Includes DC and US territories.
STATE_NAMES = ('Alabama Alaska Arizona Arkansas California Colorado Connecticut Delaware Florida Georgia Hawaii Idaho Illinois Indiana Iowa Kansas Kentucky Louisiana Maine Maryland Massachusetts Michigan Minnesota Mississippi Missouri Montana Nebraska Nevada Ohio Oklahoma Oregon Pennsylvania Tennessee Texas Utah Vermont Virginia Washington Wisconsin Wyoming').split()
STATE_NAMES += ['New Hampshire','New Jersey','New Mexico','New York','North Carolina','North Dakota','Rhode Island','South Carolina','South Dakota','West Virginia','District of Columbia','Puerto Rico','US Virgin Islands']
ABBREVIATIONS = dict(zip('AL AK AZ AR CA CO CT DE FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS MO MT NE NV OH OK OR PA TN TX UT VT VA WA WI WY'.split(),STATE_NAMES[:40]))
# Explicit postal entries for the multiword state names.
ABBREVIATIONS.update({'NH':'New Hampshire','NJ':'New Jersey','NM':'New Mexico','NY':'New York','NC':'North Carolina','ND':'North Dakota','RI':'Rhode Island','SC':'South Carolina','SD':'South Dakota','WV':'West Virginia','DC':'District of Columbia','PR':'Puerto Rico','VI':'US Virgin Islands'})
STATE_PATTERN='|'.join(re.escape(s) for s in sorted(STATE_NAMES+list(ABBREVIATIONS),key=len,reverse=True))
CITY_STATE = re.compile(r'(?:^|,|[ \t]{2,})[ \t]*(?P<city>[A-Za-z][A-Za-z .\'-]*?)(?:,\s*|[ \t]+)(?P<state>'+STATE_PATTERN+r')(?=[ \t,\d]|$)',re.I|re.M)
CAPTION = re.compile(r'address(?:\s+and\s+zip\s+code)?\s+of\s+(?:the\s+)?principal\s+(?:executive\s+)?offices?',re.I)
FIRMS = {
    'Ernst & Young LLP':r'Ernst\s*(?:&|and)\s*Young\s*,?\s*LLP',
    'PricewaterhouseCoopers LLP':r'PricewaterhouseCoopers\s*,?\s*LLP',
    'Deloitte & Touche LLP':r'Deloitte\s*(?:&|and)\s*Touche\s*,?\s*LLP',
    'KPMG LLP':r'KPMG\s*,?\s*LLP',
}
AUDITORS='(?:'+'|'.join(FIRMS.values())+')'
ASSET_FIRMS={'pwc':'PricewaterhouseCoopers LLP','kpmg':'KPMG LLP','ey':'Ernst & Young LLP','deloitte':'Deloitte & Touche LLP'}

def claim(page, company_id, relation, name, snippet):
    identity=f'{company_id}|{page.source_doc}|{page.page_num}|{relation}|{name}'
    return RelationClaimNode(id='FACT:'+hashlib.sha256(identity.encode()).hexdigest()[:20],
        company_id=company_id,source_doc=page.source_doc,page_num=page.page_num,
        section=page.section,snippet=snippet,relation_type=relation,
        target_id=canonicalize(name),target_name=name)


def headquarters(page):
    """Find city/state only in the statutory caption block, in either layout direction.

    Caption-less covers require a unique complete street+city/state/ZIP block before
    the securities registration section. SEC's Washington address has no street and
    is therefore ineligible. No business-section location inference is performed.
    """
    text=page.text;matches=[]
    captions=list(CAPTION.finditer(text))
    windows=[]
    for c in captions:
        before=max(0,c.start()-650);after=min(len(text),c.end()+450)
        windows.append((before,after,False))
    if not captions and page.page_num==1 and re.search(r'form\s+10-k',text,re.I):
        end=re.search(r'securities\s+registered|indicate\s+by\s+check',text,re.I)
        windows=[(0,end.start() if end else min(len(text),3000),True)]
    for start,end,require_street in windows:
        block=text[start:end]
        for m in CITY_STATE.finditer(block):
            state_raw=m['state'].strip();city=m['city'].strip(' ,')
            if re.search(r'(?i)jurisdiction|commission|incorporation|registered|registrant|specified|identification|address|charter',city) or city.casefold() in ('state','other'):continue
            if len(state_raw)==2 and not state_raw.isupper():continue
            state=ABBREVIATIONS.get(state_raw.upper(),next((s for s in STATE_NAMES if s.casefold()==state_raw.casefold()),state_raw))
            absolute_end=start+m.end()
            line_end=text.find('\n',absolute_end)
            if line_end<0:line_end=len(text)
            zip_on_line=bool(re.match(r'[ \t,]*\d{5}(?:-\d{4})?',text[absolute_end:line_end]))
            street_before=bool(re.search(r'(?i)(?:\d+|\bOne\b)\s+[^\n]{0,90}(?:street|avenue|drive|way|road|plaza|boulevard|parkway|lane|mall)\b',text[max(start,start+m.start()-220):absolute_end]))
            if not zip_on_line and not street_before:continue
            # Caption-less covers need both a ZIP and an adjacent street line.
            if require_street:
                tail=block[m.end():m.end()+25]
                preceding=block[max(0,m.start()-140):m.end()]
                if not re.match(r'\s*,?\s*\d{5}(?:-\d{4})?',tail):continue
                if not re.search(r'(?i)(?:\d+|\bOne\b)\s+[^\n]{0,90}(?:street|avenue|drive|way|road|plaza|boulevard|parkway|lane)\b',preceding):continue
            name=city.title()+', '+state
            original_start=text.rfind('\n',0,start+m.start())+1
            original_end=text.find('\n',start+m.end())
            if original_end<0:original_end=len(text)
            snippet=text[original_start:original_end]
            matches.append((name,snippet))
    unique={name:snippet for name,snippet in matches}
    if not captions and len(unique)!=1:return []
    return list(unique.items())


def extract(pages, company_id):
    facts=[]
    for page in pages:
        text=page.text
        if page.page_num==1:
            m=re.search(r'(?m)^\s*('+STATE_PATTERN+r')\s+[^\n]*\n(?:[^\n]*\n){0,3}[^\n]*State or other jurisdiction',text,re.I)
            if m:facts.append(claim(page,company_id,'INCORPORATED_IN',m[1],m[0]))
            m=re.search(r'(?is)for the fiscal year ended.{0,100}?([A-Za-z]+\s+\d{1,2},?\s+20\d{2})',text)
            if m:facts.append(claim(page,company_id,'FISCAL_YEAR_END',m[1],m[0]))
        if page.page_num<=6 and (page.section=='Cover' or page.page_num<=2):
            for name,snippet in headquarters(page):facts.append(claim(page,company_id,'HEADQUARTERED_IN',name,snippet))
        report=page.section=='Auditor Report'
        for name,pattern in FIRMS.items():
            for m in re.finditer(pattern,text,re.I):
                context=text[max(0,m.start()-180):m.end()+140]
                explicit=re.search(r'independent\s+(?:registered\s+public\s+accounting\s+firm|auditor)|audited\s+by|auditor.{0,20}name',context,re.I)
                if not report and not (explicit and re.search(r'our\s+independent|audited\s+by',context,re.I)):continue
                fact=claim(page,company_id,'AUDITED_BY',name,m[0])
                fact.audit_scope=page.audit_scope if report else None
                facts.append(fact)
                break
        if report:
            # Firm-bearing signature asset labels are evidence in the source PDF;
            # never infer a firm from an anonymous image or a PCAOB number alone.
            for brand,name in ASSET_FIRMS.items():
                m=re.search(r'\b'+brand+r'[^\n]{0,45}?signature[^\n]*',text,re.I)
                if m:
                    fact=claim(page,company_id,'AUDITED_BY',name,m[0]);fact.audit_scope=page.audit_scope;fact.evidence_kind='signature_asset'
                    facts.append(fact)
    return list({f.id:f for f in facts}.values())
