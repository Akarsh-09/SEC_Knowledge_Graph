"""Build a validated, provenance-bearing NetworkX MultiDiGraph."""
import json
from collections import Counter
from pathlib import Path
import networkx as nx
from config.ontology import CanonicalMetric,FISCAL_PERIODS
from src.graph.schema import CompanyNode,CanonicalMetricNode,FiscalPeriodNode,DocumentNode,ExternalEntityNode
from src.graph.entity_resolution import link_conflicts

def build(companies, facts, output: Path, *, relation_stats=None, audit_dir=None, parse_stats=None, balance_diagnostics=None, rules_digest=None):
    graph=nx.MultiDiGraph(schema_version=1,extraction_rules_digest=rules_digest)
    def add(node): graph.add_node(node.id,**node.model_dump())
    for c in companies: add(CompanyNode(id='COMP:'+c['ticker'],**c))
    for metric in CanonicalMetric: add(CanonicalMetricNode(id='METRIC:'+metric.value,name=metric.value))
    for period in FISCAL_PERIODS: add(FiscalPeriodNode(id=period))
    for fact in facts:
        add(fact)
        doc='DOC:'+fact.source_doc
        add(DocumentNode(id=doc,filename=fact.source_doc))
        graph.add_edge(fact.company_id,fact.id,relation='HAS_FACT')
        graph.add_edge(fact.id,doc,relation='SOURCED_FROM')
        if fact.node_type=='MetricObservation':
            if fact.metric_id not in graph: add(CanonicalMetricNode(id=fact.metric_id,name=fact.metric_id.split(':')[1]))
            if fact.period not in graph: add(FiscalPeriodNode(id=fact.period))
            graph.add_edge(fact.id,fact.metric_id,relation='OBSERVES')
            graph.add_edge(fact.id,fact.period,relation='IN_PERIOD')
        else:
            add(ExternalEntityNode(id=fact.target_id,name=fact.target_name))

    link_conflicts(graph)
    for fact in facts:
        fact.status = graph.nodes[fact.id]['status']
    for id, data in graph.nodes(data=True):
        if data['node_type']=='RelationClaim' and data['status']=='active':
            graph.add_edge(data['company_id'],data['target_id'],relation=data['relation_type'],fact_id=id)
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(nx.node_link_data(graph,edges='edges'),indent=2)+'\n')
    print('Nodes:',dict(Counter(d['node_type'] for _,d in graph.nodes(data=True))))
    print('Edges:',dict(Counter(d['relation'] for *_,d in graph.edges(data=True))))
    for c in companies:
        metrics={f.metric_id for f in facts if f.company_id=='COMP:'+c['ticker'] and f.node_type=='MetricObservation'}
        print(c['ticker'],len(metrics),'metrics')
    write_ingestion_audit(graph, audit_dir or output.parent/'results', relation_stats,parse_stats=parse_stats,balance_diagnostics=balance_diagnostics,rules_digest=rules_digest)
    return graph


def write_ingestion_audit(graph, output_dir: Path, relation_stats=None, *, parse_stats=None, balance_diagnostics=None, rules_digest=None) -> dict:
    """Audit core coverage and latest observed-year balance identities without guessing."""
    core={'METRIC:'+m.value for m in CanonicalMetric if m.value not in ('NET_INTEREST_INCOME','NONINTEREST_REVENUE')}
    report={'extraction_rules_digest':rules_digest,'core_metric_count':len(core),'documents':parse_stats or {},'companies':[]}
    for company,data in graph.nodes(data=True):
        if data['node_type']!='Company': continue
        facts=[f for _,f in graph.nodes(data=True) if f.get('company_id')==company]
        active=[f for f in facts if f.get('status')=='active']
        observations=[f for f in active if f['node_type']=='MetricObservation']
        extracted={f['metric_id'] for f in observations}&core
        latest=max((f['period'] for f in observations),default=None)
        values={}
        for f in sorted(observations,key=lambda f:(not f['audited'],f['section']!='Item 8',f['page_num'])):
            if f['period']==latest:values.setdefault(f['metric_id'],f['value_usd'])
        inputs=('METRIC:TOTAL_ASSETS','METRIC:TOTAL_LIABILITIES','METRIC:SHAREHOLDERS_EQUITY')
        missing=[m for m in inputs if m not in values]
        residual=None if missing else values[inputs[0]]-values[inputs[1]]-values[inputs[2]]
        sources=(relation_stats or {}).get(company,[])
        stats={key:sum(s.get(key,0) for s in sources) for key in ('candidate_pages_selected','candidate_pages_sent','pages_replayed','accepted_claims','rejected_by_provenance_gate','offline_cache_misses')}
        stats['recorded']=company in (relation_stats or {})
        stats['filings']=sources
        counts=Counter(f.get('status','active') for f in facts)
        metadata={predicate:[{'target_name':f['target_name'],'page_num':f['page_num'],'source_doc':f['source_doc']} for f in active if f['node_type']=='RelationClaim' and f['relation_type']==predicate] for predicate in ('AUDITED_BY','HEADQUARTERED_IN')}
        missing_critical=sorted({'METRIC:REVENUE','METRIC:NET_INCOME','METRIC:TOTAL_ASSETS'}-extracted)
        parsed=[dict(source_doc=doc,**stats) for doc,stats in (parse_stats or {}).items() if stats['ticker']==data['ticker']]
        report['companies'].append(dict(company_id=company,parse_results=parsed,
            balance_sheet_diagnostics=(balance_diagnostics or {}).get(company,[]),
            metadata_coverage=metadata,missing_critical_metrics=missing_critical,
            coverage_flag=len(core-extracted)>4 or bool(missing_critical),ticker=data['ticker'],core_metrics_extracted=len(extracted),
            extracted_core_metrics=sorted(extracted),missing_core_metrics=sorted(core-extracted),latest_period=latest,
            balance_sheet_residual_usd=residual,balance_sheet_missing_inputs=missing,
            fact_status_counts={s:counts[s] for s in ('active','corroborating','superseded')},llm_relation_extraction=stats))
    report['summary']={
        'companies_total':len(report['companies']),
        'companies_parsed_cleanly':sum(bool(c['parse_results']) and all(p['parsed_cleanly'] for p in c['parse_results']) for c in report['companies']),
        'companies_flagged':sum(c['coverage_flag'] for c in report['companies']),
        'auditor_coverage':sum(bool(c['metadata_coverage']['AUDITED_BY']) for c in report['companies']),
        'hq_coverage':sum(bool(c['metadata_coverage']['HEADQUARTERED_IN']) for c in report['companies']),
        'nonzero_balance_residuals':sum(c['balance_sheet_residual_usd'] not in (None,0) for c in report['companies']),
        'unavailable_balance_residuals':sum(c['balance_sheet_residual_usd'] is None for c in report['companies'])}
    output_dir.mkdir(parents=True,exist_ok=True)
    (output_dir/'ingestion_audit.json').write_text(json.dumps(report,indent=2)+'\n')
    lines=['# Ingestion audit','','Missing evidence is reported as unavailable, never as a zero residual. LLM pages sent excludes cache replay and skipped pages.','',
        '| Company | Core metrics | Missing core metrics | Latest FY | Balance residual USD | Active / corroborating / superseded | Selected / sent / replayed pages | Accepted / rejected claims |',
        '|---|---:|---|---|---:|---|---|---|']
    for c in report['companies']:
        status=c['fact_status_counts'];s=c['llm_relation_extraction']
        residual='unavailable' if c['balance_sheet_residual_usd'] is None else f"{c['balance_sheet_residual_usd']:.2f}"
        lines.append(f"| {c['ticker']} | {c['core_metrics_extracted']}/{len(core)} | {', '.join(m.removeprefix('METRIC:') for m in c['missing_core_metrics']) or 'none'} | {c['latest_period'] or 'unavailable'} | {residual} | {status['active']} / {status['corroborating']} / {status['superseded']} | {s['candidate_pages_selected']} / {s['candidate_pages_sent']} / {s['pages_replayed']} | {s['accepted_claims']} / {s['rejected_by_provenance_gate']} |")
    lines.extend(['','## Parse and metadata coverage','',json.dumps(report['summary'],sort_keys=True),'',
        '| Company | Parsed | Flagged | Missing Revenue / Net Income / Total Assets | Auditor | HQ |',
        '|---|---|---|---|---|---|'])
    for c in report['companies']:
        parsed='yes' if c['parse_results'] and all(p['parsed_cleanly'] for p in c['parse_results']) else 'failed / not recorded'
        auditor='; '.join(m['target_name'] for m in c['metadata_coverage']['AUDITED_BY']) or 'MISSING'
        hq='; '.join(m['target_name'] for m in c['metadata_coverage']['HEADQUARTERED_IN']) or 'MISSING'
        lines.append(f"| {c['ticker']} | {parsed} | {'YES' if c['coverage_flag'] else 'no'} | {', '.join(c['missing_critical_metrics']) or 'none'} | {auditor} | {hq} |")
    lines.extend(['','## Separate mezzanine / redeemable equity diagnostics','',
        'The strict three-term residual above is NOT adjusted. These lines may explain a residual; presence alone does not establish a full reconciliation.',''])
    for c in report['companies']:
        for diagnostic in c['balance_sheet_diagnostics']:
            values='; '.join(f"{v['period']}: {v['value_usd']:.2f} USD" for v in diagnostic['values'])
            lines.append(f"- {c['ticker']}: {diagnostic['raw_label']} — {values} [{diagnostic['source_doc']}, p. {diagnostic['page_num']}]. {diagnostic['note']}")
    (output_dir/'ingestion_audit.md').write_text('\n'.join(lines)+'\n')
    return report
