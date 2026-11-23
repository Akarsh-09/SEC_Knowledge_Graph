"""Verify the immutable pre-benchmark extraction-rule snapshot."""
import hashlib
import json
from pathlib import Path

RULE_FILES = (
    'config/ontology.py', 'src/ingest/pdf_parser.py', 'src/extract/table_extractor.py',
    'src/extract/metadata_extractor.py', 'src/extract/relation_extractor.py',
    'src/graph/schema.py', 'src/graph/entity_resolution.py', 'src/graph/builder.py',
    'src/extract/freeze.py',
)

def verify_rules(root: Path) -> str | None:
    """Fail closed if frozen rules changed; model/provider settings are outside the lock."""
    path=root/'config/extraction_rules.lock.json'
    if not path.exists():return None
    manifest=json.loads(path.read_text())
    if set(manifest['files'])!=set(RULE_FILES):raise RuntimeError('Frozen extraction file set changed')
    changed=[name for name,expected in manifest['files'].items()
             if not (root/name).is_file() or hashlib.sha256((root/name).read_bytes()).hexdigest()!=expected]
    if changed:raise RuntimeError('Frozen extraction rules changed: '+', '.join(changed)+'. Do not tune frozen rules against benchmark questions.')
    return hashlib.sha256(json.dumps(manifest,sort_keys=True).encode()).hexdigest()
