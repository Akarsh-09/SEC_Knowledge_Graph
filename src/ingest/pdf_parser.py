"""Extract physical PDF pages, verbatim text and table cells without retrieval."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re

import pymupdf
import pdfplumber
from pydantic import BaseModel, Field


class ParsedPage(BaseModel):
    source_doc: str
    page_num: int = Field(ge=1)
    section: str
    text: str
    statement_header: str = ''
    statement_kind: str | None = None
    statement_start: int = 0
    audit_scope: str | None = None
    signals: list[str] = Field(default_factory=list)
    tables: list[list[list[str | None]]]


ITEM = re.compile(r'^\s*ITEM\s+(1A|1B|1C|1|2|3|4|5|6|7A|7|8|9A|9B|9C|9|10|11|12|13|14|15|16)\s*[.：:\-–]?\s+(.+)$', re.I | re.M)


# Only primary statement titles, not comprehensive-income/equity/analysis titles.
STATEMENT = re.compile(
    r'^[ \t]*(?:[^\n]{1,100}?\b(?:and\s+)?subsidiaries\s+)?(?:(?:consolidated|condensed|combined)\s+)*'
    r'(?P<title>statements?\s+of\s+(?:(?:consolidated|condensed)\s+)?'
    r'(?:income|operations|earnings|financial\s+(?:position|condition)|cash\s+flows?)|'
    r'(?:income|cash\s+flows?)\s+statements?|balance\s+sheets?)'
    r'(?=[ \t]*(?:[.:(]?(?:\r?$|\n)|\(?continued\b|\bfor\b|\bas\s+of\b|\byears?\b|\band\s+comprehensive\b)|[ \t]{2,})', re.I|re.M)
AUDIT_REPORT = re.compile(r'^[ \t]*(?:report\s+of\s+independent\s+(?:registered\s+public\s+accounting\s+firm|auditors?)|independent\s+(?:registered\s+public\s+accounting\s+firm|auditors?)[’\']?s?\s+report)',re.I|re.M)


def is_contents_page(text: str) -> bool:
    """A running contents link alone never makes an ordinary page a TOC."""
    titles=list(STATEMENT.finditer(text))
    items=list(ITEM.finditer(text))
    if len(items)>=4 or len(titles)>=3:return True
    references=0
    for title in titles:
        tail=text[title.end():].split('\n',1)[0]
        if re.search(r'\s+(?:\d{1,3})(?:[-–]\d{1,3})?\s*$',tail):references+=1
    return references>=2 or (references>=1 and bool(re.search(r'(?i)index|table of contents',text[:1000])))


def primary_heading(text: str, match) -> bool:
    preceding=text[:match.start()]
    if len([l for l in preceding.splitlines() if l.strip()])>10:return False
    previous=[l for l in preceding.splitlines() if l.strip()]
    if previous and re.search(r'(?i)included in|reported in|refer to|see .*consolidated|of our|in our',previous[-1]):return False
    if re.search(r'(?i)following discussion|as adjusted|pro forma|selected.*data|balance sheets? analysis',preceding):return False
    tail_lines=text[match.end():].split('\n')
    tail=tail_lines[0].strip(' .:')
    # A combined operations/income + comprehensive-income primary statement can
    # wrap its suffix. Do not weaken the separate comprehensive-only exclusion.
    if re.fullmatch(r'and\s+comprehensive',tail,re.I):
        following=next((line.strip() for line in tail_lines[1:] if line.strip()),'')
        if re.fullmatch(r'income',following,re.I):return True
    if not tail:return True
    return bool(re.match(r'(?i)(?:for\b|as of\b|years?\b|and comprehensive income|\(continued\)|(?:image|figure)\w*\.(?:jpg|png)|(?:January|February|March|April|May|June|July|August|September|October|November|December)\b)',tail)
                or re.fullmatch(r'[A-Za-z][^\n]{0,80}(?:Inc\.?|Corp\.?|Corporation|Subsidiaries)',tail))


def statement_kind(title: str) -> str:
    title=' '.join(title.lower().split())
    if 'balance' in title or 'financial position' in title or 'financial condition' in title:return 'balance'
    if 'cash' in title:return 'cash_flow'
    return 'income'


def parse_pdf(path: Path) -> list[ParsedPage]:
    """Carry section headings across pages; ignore table-of-contents headings.

    Page numbers always refer to the 1-indexed physical PDF, not printed labels.
    Scanned pages remain empty; OCR is not silently substituted.
    """
    pages: list[ParsedPage] = []
    section = 'Cover'
    audit_scope = None
    in_notes = False
    with pymupdf.open(path) as doc, pdfplumber.open(path) as tables_doc:
        for index, page in enumerate(doc):
            text = page.get_text(sort=True)
            normalized = text.replace('\xa0', ' ')
            headings = list(ITEM.finditer(normalized))
            toc = is_contents_page(normalized)
            notes_heading=re.search(r'(?im)^[ \t]*notes\s+to\s+(?:the\s+)?(?:condensed\s+)?(?:consolidated\s+)?financial\s+statements[ \t]*(?:\(continued\))?(?=[ \t]{2,}|\r?$)',normalized[:900])
            if not toc and notes_heading and len([l for l in normalized[:notes_heading.start()].splitlines() if l.strip()])<=3:
                in_notes=True
            signals: list[str] = []
            kind = None
            statement_start = 0
            statement_header = ''
            if not toc:
                for heading in headings:
                    if not re.search(r'\.{3,}|\s\d+\s*$', heading.group(2)):
                        section = 'Item ' + heading.group(1).upper()
                statement = next((m for m in STATEMENT.finditer(normalized[:1800])
                                  if not in_notes and primary_heading(normalized,m) and not re.search(r'(?im)^\s*notes?\s+(?:\d+|to\s+(?:the\s+)?(?:consolidated\s+)?financial)',normalized[:m.start()])), None)
                if statement:
                    signals.append('Financial Statements')
                    kind=statement_kind(statement['title'])
                    statement_start=statement.start()
                    section = 'Item 8'
                    statement_header = '\n'.join(text[statement.start():].splitlines()[:20])
                elif not in_notes and not re.search(r'(?i)(?:statements?\s+of\s+(?:comprehensive\s+income|(?:changes\s+in\s+)?(?:shareholders.?|stockholders.?)?\s*equity)|comprehensive\s+income\s+statements?)',normalized[:600]) and pages and 'Financial Statements' in pages[-1].signals and (len(pages[-1].text.strip()) < 400 or re.search(r'(?i)(?:statement|sheet|table).{0,35}continu',pages[-1].text[-500:]) or re.search(r'(?m)^\s*(?:20\d{2}\s+){1,3}20\d{2}\s*$',normalized[:400])):
                    signals.append('Financial Statements')
                    statement_header=pages[-1].statement_header
                    kind=pages[-1].statement_kind
                    section='Item 8'
                if re.search(r"(?im)^\s*management[’']?s\s+discussion\s+and\s+analysis", normalized[:500]):
                    signals.append('MD&A')
                    section = 'Item 7'
            page_section = 'Table of Contents' if toc else section
            if not toc and AUDIT_REPORT.search(normalized[:1400]):
                page_section = 'Auditor Report'
                section = 'Auditor Report'
            if page_section=='Auditor Report':
                financial=re.search(r'opinions?\s+on\s+(?:the\s+)?(?:consolidated\s+)?financial\s+statements',normalized[:2400],re.I)
                internal=re.search(r'opinions?\s+on\s+internal\s+control',normalized[:2400],re.I)
                if financial and (not internal or financial.start()<internal.start()):audit_scope='financial_statements'
                elif internal:audit_scope='internal_control'
            if page_section == 'Item 1': signals.append('Business')
            if page_section == 'Item 1A': signals.append('Risk')
            if page_section == 'Item 7': signals.append('MD&A')
            pages.append(ParsedPage(source_doc=path.name, page_num=index + 1,
                                    section=page_section, statement_header=statement_header, statement_kind=kind, statement_start=statement_start, audit_scope=audit_scope if page_section=='Auditor Report' else None, signals=sorted(set(signals)), text=text,
                                    tables=tables_doc.pages[index].extract_tables()))
    return pages


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('pdf', type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    pages = parse_pdf(args.pdf)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps([p.model_dump() for p in pages], indent=2))
    print(json.dumps({'document': args.pdf.name, 'pages': len(pages),
                      'tables': sum(len(p.tables) for p in pages),
                      'sections': sorted({p.section for p in pages})}, indent=2))


if __name__ == '__main__':
    main()
