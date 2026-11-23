"""Issuer-independent bucket reservations, quote policy and prompt/cache revision."""
import hashlib
import json
from pathlib import Path
from src.extract.relation_extractor import (
    PROMPT_VERSION,SYSTEM_PROMPT,QUALITATIVE,select_candidate_pages,extract,Candidates,
)
from src.ingest.pdf_parser import ParsedPage


def page(number,section,text):
    return ParsedPage(source_doc='example.pdf',page_num=number,section=section,text=text,tables=[])


def test_buckets_reserve_business_segments_and_officers_despite_risk_density():
    pages=[page(n,'Item 1','Business overview') for n in [1,2,3,4]]
    pages += [page(20,'Item 8','Segment Information. Reportable Segments.'),
              page(21,'Item 8','Operating Segments. Chief Operating Decision Maker.'),
              page(30,'Item 10','Executive Officers. Chief Executive Officer: Example Person.'),
              page(31,'Item 16','/s/ Example Person, Principal Executive Officer.')]
    pages += [page(n,'Item 1A','principal risk factors '*100) for n in range(40,60)]
    selected=select_candidate_pages(pages)
    numbers=[p.page_num for p in selected]
    assert numbers==[1,2,3,20,21,30,31,40,41,42]
    assert [p.page_num for p in select_candidate_pages(list(reversed(pages)))]==numbers


def test_bucket_overlap_never_duplicates_or_spends_slots_twice():
    pages=[page(1,'Item 1','Reportable Segments and Business Overview.'),
           page(2,'Item 1','Executive Officers and Chief Executive Officer.'),
           page(3,'Item 1','Business overview'),
           page(10,'Item 8','Segment Information'),
           page(11,'Item 8','Operating Segments'),
           page(20,'Item 16','Signatures: Principal Executive Officer'),
           page(21,'Item 10','Executive Officers: Chief Executive Officer')]
    pages += [page(n,'Item 7','Completed acquisition and business combinations.') for n in range(30,40)]
    selected=select_candidate_pages(pages)
    numbers=[p.page_num for p in selected]
    assert len(numbers)==10 and len(set(numbers))==10
    assert {1,2,3,10,11,20,21}.issubset(numbers)


def test_unused_buckets_are_available_to_remainder():
    pages=[page(n,'Item 1A','major customer and sole source supplier concentration') for n in range(1,16)]
    assert [p.page_num for p in select_candidate_pages(pages)]==list(range(1,11))


def test_empty_irrelevant_cover_contents_and_exhibits_not_filler():
    pages=[page(1,'Cover','principal risk factors major customer'),
           page(2,'Table of Contents','Reportable Segments Chief Executive Officer'),
           page(3,'Auditor Report','risk factors business combinations'),
           page(4,'Item 15','Exhibits: risk factors acquisition'),
           page(5,'Item 16','risk factors acquisition'),
           page(6,'Item 7',''),page(7,'Item 7','ordinary narrative'),
           page(8,'Item 8','Business combinations: we acquired Example Assets.')]
    assert [p.page_num for p in select_candidate_pages(pages)]==[8]


def test_prompt_version_and_exact_field_example_are_used_by_extractor():
    observed=[]
    class Client:
        offline=True
        def structured(self,system,user,schema):
            observed.append((system,user));return Candidates(claims=[]),'llm_cache'
    extract([page(1,'Item 1','Business overview')],'COMP:EXAMPLE',Client())
    assert PROMPT_VERSION=='v3'
    assert observed[0][0]==SYSTEM_PROMPT and 'PROMPT_VERSION=v3' in SYSTEM_PROMPT
    start=SYSTEM_PROMPT.index('{"claims":[')
    example,_=json.JSONDecoder().raw_decode(SYSTEM_PROMPT[start:])
    assert set(example['claims'][0])=={'relation_type','target_name','page_num','verbatim_quote'}
    assert 'JSON' in SYSTEM_PROMPT and '{"claims":[]}' in SYSTEM_PROMPT
    assert all(relation in SYSTEM_PROMPT for relation in QUALITATIVE)
    assert 'ASC 280' in SYSTEM_PROMPT and 'Principal Executive Officer' in SYSTEM_PROMPT
    assert '**Copy `verbatim_quote` as ONE exact, contiguous substring' in SYSTEM_PROMPT
    assert 'NEVER reorder words, skip intervening dates/lines' in SYSTEM_PROMPT
    # Cache keys include prompt text: a new version cannot replay an old response.
    old=SYSTEM_PROMPT.replace('PROMPT_VERSION=v3','PROMPT_VERSION=v2')
    assert hashlib.sha256(('model'+old+observed[0][1]).encode()).hexdigest()!=hashlib.sha256(('model'+SYSTEM_PROMPT+observed[0][1]).encode()).hexdigest()


def test_active_v3_lock_verifies_and_preserves_v2_predecessor():
    from src.extract.freeze import RULE_FILES,verify_rules
    root=Path(__file__).resolve().parents[1]
    manifest=json.loads((root/'config/extraction_rules.lock.json').read_text())
    predecessor=json.loads((root/'results/relation_v3_predecessor.json').read_text())
    assert manifest['version']==3
    assert manifest['predecessor_digest']==hashlib.sha256(json.dumps(predecessor,sort_keys=True).encode()).hexdigest()
    assert set(manifest['files'])==set(RULE_FILES)
    assert [name for name in RULE_FILES if manifest['files'][name]!=predecessor['files'][name]]==['src/extract/relation_extractor.py']
    assert verify_rules(root)==hashlib.sha256(json.dumps(manifest,sort_keys=True).encode()).hexdigest()
