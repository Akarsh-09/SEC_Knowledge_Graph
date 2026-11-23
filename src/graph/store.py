"""JSON graph persistence with indexed observation and relation lookups."""
import json
from collections import defaultdict
from pathlib import Path
import networkx as nx

class GraphStore:
    def __init__(self, path: Path):
        self.graph=nx.node_link_graph(json.loads(path.read_text()),edges='edges')
        self.metrics=defaultdict(list); self.relations=defaultdict(list)
        self.companies={}; self.sectors=defaultdict(list)
        for id,d in self.graph.nodes(data=True):
            d['id'] = id
            if d['node_type']=='Company':
                for alias in (id,d['ticker'],d['name']): self.companies[alias.casefold()]=id
                self.sectors[d['sector']].append(id)
            elif d['node_type']=='MetricObservation': self.metrics[(d['company_id'],d['metric_id'],d['period'])].append(d)
            elif d['node_type']=='RelationClaim': self.relations[(d['company_id'],d['relation_type'])].append(d)
    def lookup_metric(self, company_id, metric_id, period, active_only=True):
        return sorted([d for d in self.metrics[(company_id,metric_id,period)] if not active_only or d.get("status", "active")=="active"], key=lambda d:(not d['audited'],d['section']!='Item 8',d['page_num'],d['id']))
    def resolve_company(self, alias): return self.companies.get(alias.casefold())
    def lookup_relation(self, company_id, relation, active_only=True):
        return [d for d in self.relations[(company_id,relation)] if not active_only or d.get('status','active')=='active']
    def relation_claims(self, relation, active_only=True):
        return [d for (company, predicate), facts in self.relations.items() if predicate==relation
                for d in facts if not active_only or d.get('status','active')=='active']
