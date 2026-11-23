"""Stable entity aliases and explicit conflict links."""
import re
from collections import defaultdict
from config.ontology import ENTITY_ALIASES

def canonicalize(name: str) -> str:
    key = ' '.join(name.lower().split())
    return ENTITY_ALIASES.get(key, 'EXT:'+re.sub(r'[^A-Z0-9]+','_',name.upper()).strip('_'))

def link_conflicts(graph):
    groups = defaultdict(list)
    for id, data in graph.nodes(data=True):
        if data['node_type']=='MetricObservation':
            groups[(data['company_id'],data['metric_id'],data['period'])].append((id,data))
    for entries in groups.values():
        entries.sort(key=lambda x: (not x[1]['audited'],x[1]['section']!='Item 8',x[1]['page_num'],x[0]))
        preferred, data = entries[0]
        for other, observation in entries[1:]:
            if observation['value_usd'] != data['value_usd']:
                observation['status'] = 'superseded'
                graph.add_edge(preferred,other,relation='SUPERSEDES')

    relations = defaultdict(list)
    for id, data in graph.nodes(data=True):
        if data['node_type'] == 'RelationClaim':
            relations[(data['company_id'],data['relation_type'],data['target_id'],data['source_doc'])].append((id,data))
    for entries in relations.values():
        entries.sort(key=lambda x: (x[1]['relation_type']=='AUDITED_BY' and x[1].get('audit_scope')!='financial_statements',x[1]['page_num'],x[0]))
        primary, data = entries[0]
        data['status'] = 'active'
        for other, duplicate in entries[1:]:
            duplicate['status'] = 'corroborating'
            graph.add_edge(other, primary, relation='CORROBORATES')
