# Failure analysis

## Incorrect answers

6 case(s).

### Q08 — single-fact

Which independent registered public accounting firm signed the financial-statement audit report in the supplied Goldman Sachs (GS) 10-K?

```json
{
  "gold": "EXT:PWC",
  "predicted": null,
  "abstention_reason": "The question asks for the independent registered public accounting firm (auditor) that signed the financial-statement audit report for Goldman Sachs, which is qualitative information not directly answerable via the graph query metrics/relations.",
  "missed_facts": [
    {
      "doc_id": "GS_10K_2025.pdf",
      "page_num": 317,
      "company_id": "COMP:GS",
      "predicate": "AUDITED_BY",
      "period": null,
      "expected_value": "PricewaterhouseCoopers LLP"
    }
  ],
  "extra_facts": [],
  "plan": {
    "steps": [
      {
        "output_var": "$answer",
        "action": "abstain",
        "reason": "The question asks for the independent registered public accounting firm (auditor) that signed the financial-statement audit report for Goldman Sachs, which is qualitative information not directly answerable via the graph query metrics/relations."
      }
    ]
  },
  "execution_trace": [
    {
      "action": "abstain",
      "output_var": "$answer",
      "reason": "The question asks for the independent registered public accounting firm (auditor) that signed the financial-statement audit report for Goldman Sachs, which is qualitative information not directly answerable via the graph query metrics/relations.",
      "fact_ids": []
    }
  ]
}
```

### Q09 — single-fact

In which city and state are Costco (COST) principal executive offices located, as printed on the supplied 10-K cover?

```json
{
  "gold": "Issaquah, WA",
  "predicted": null,
  "abstention_reason": "The question asks for the city and state of principal executive offices which is not a metric, relation-traversal, or derivable formula in the financial knowledge graph.",
  "missed_facts": [
    {
      "doc_id": "COST_10K_2026.pdf",
      "page_num": 1,
      "company_id": "COMP:COST",
      "predicate": "HEADQUARTERED_IN",
      "period": null,
      "expected_value": "Issaquah, WA"
    }
  ],
  "extra_facts": [],
  "plan": {
    "steps": [
      {
        "output_var": "$answer",
        "action": "abstain",
        "reason": "The question asks for the city and state of principal executive offices which is not a metric, relation-traversal, or derivable formula in the financial knowledge graph."
      }
    ]
  },
  "execution_trace": [
    {
      "action": "abstain",
      "output_var": "$answer",
      "reason": "The question asks for the city and state of principal executive offices which is not a metric, relation-traversal, or derivable formula in the financial knowledge graph.",
      "fact_ids": []
    }
  ]
}
```

### Q10 — single-fact

List the five US GAAP reportable segments of Procter & Gamble (PG) named in its supplied segment-information note.

```json
{
  "gold": [
    "Beauty",
    "Grooming",
    "Health Care",
    "Fabric & Home Care",
    "Baby, Feminine & Family Care"
  ],
  "predicted": [
    "EXT:BEAUTY",
    "EXT:GROOMING",
    "EXT:HEALTH_CARE",
    "EXT:FABRIC_HOME_CARE",
    "EXT:BABY_FEMININE_FAMILY_CARE",
    "EXT:FABRIC_CARE",
    "EXT:HOME_CARE",
    "EXT:BABY_CARE",
    "EXT:HAIR_CARE",
    "EXT:FAMILY_CARE",
    "EXT:ORAL_CARE",
    "EXT:FEMININE_CARE",
    "EXT:PERSONAL_HEALTH_CARE",
    "EXT:PERSONAL_CARE",
    "EXT:SKIN_CARE"
  ],
  "abstention_reason": null,
  "missed_facts": [
    {
      "doc_id": "PG_10K_2026.pdf",
      "page_num": 82,
      "company_id": "COMP:PG",
      "predicate": "OPERATES_SEGMENT",
      "period": null,
      "expected_value": "Beauty"
    },
    {
      "doc_id": "PG_10K_2026.pdf",
      "page_num": 82,
      "company_id": "COMP:PG",
      "predicate": "OPERATES_SEGMENT",
      "period": null,
      "expected_value": "Grooming"
    },
    {
      "doc_id": "PG_10K_2026.pdf",
      "page_num": 82,
      "company_id": "COMP:PG",
      "predicate": "OPERATES_SEGMENT",
      "period": null,
      "expected_value": "Health Care"
    },
    {
      "doc_id": "PG_10K_2026.pdf",
      "page_num": 82,
      "company_id": "COMP:PG",
      "predicate": "OPERATES_SEGMENT",
      "period": null,
      "expected_value": "Fabric & Home Care"
    },
    {
      "doc_id": "PG_10K_2026.pdf",
      "page_num": 82,
      "company_id": "COMP:PG",
      "predicate": "OPERATES_SEGMENT",
      "period": null,
      "expected_value": "Baby, Feminine & Family Care"
    }
  ],
  "extra_facts": [
    {
      "fact_id": "FACT:9186e4cd4be69901932b",
      "source_doc": "PG_10K_2026.pdf",
      "page_num": 44,
      "company_id": "COMP:PG",
      "predicate": "OPERATES_SEGMENT",
      "period": null,
      "value": "Beauty",
      "snippet": "Global market share of the Beauty segment decreased 0.3 points."
    },
    {
      "fact_id": "FACT:6d52b3df90a4fe52db22",
      "source_doc": "PG_10K_2026.pdf",
      "page_num": 44,
      "company_id": "COMP:PG",
      "predicate": "OPERATES_SEGMENT",
      "period": null,
      "value": "Grooming",
      "snippet": "Grooming"
    },
    {
      "fact_id": "FACT:3706044ff2a543252120",
      "source_doc": "PG_10K_2026.pdf",
      "page_num": 60,
      "company_id": "COMP:PG",
      "predicate": "OPERATES_SEGMENT",
      "period": null,
      "value": "Health Care",
      "snippet": "Health Care                                           4 %                (3) %      \u2014 %             1 %"
    },
    {
      "fact_id": "FACT:a199f6f20e58855c5589",
      "source_doc": "PG_10K_2026.pdf",
      "page_num": 60,
      "company_id": "COMP:PG",
      "predicate": "OPERATES_SEGMENT",
      "period": null,
      "value": "Fabric & Home Care",
      "snippet": "Fabric & Home Care                                   2 %                (1) %      \u2014 %             1 %"
    },
    {
      "fact_id": "FACT:d6670f55e85fbb28251e",
      "source_doc": "PG_10K_2026.pdf",
      "page_num": 60,
      "company_id": "COMP:PG",
      "predicate": "OPERATES_SEGMENT",
      "period": null,
      "value": "Baby, Feminine & Family Care",
      "snippet": "Baby, Feminine & Family Care                           1 %                (2) %      \u2014 %               (1) %"
    },
    {
      "fact_id": "FACT:91bccfcc1597358700e0",
      "source_doc": "PG_10K_2026.pdf",
      "page_num": 83,
      "company_id": "COMP:PG",
      "predicate": "OPERATES_SEGMENT",
      "period": null,
      "value": "Fabric Care",
      "snippet": "Fabric Care                                             23%        23%        24%"
    },
    {
      "fact_id": "FACT:d848e6e01eb132dbaadd",
      "source_doc": "PG_10K_2026.pdf",
      "page_num": 83,
      "company_id": "COMP:PG",
      "predicate": "OPERATES_SEGMENT",
      "period": null,
      "value": "Home Care",
      "snippet": "Home Care                                              12%        13%        12%"
    },
    {
      "fact_id": "FACT:1f525e6d46e3a94f20ec",
      "source_doc": "PG_10K_2026.pdf",
      "page_num": 83,
      "company_id": "COMP:PG",
      "predicate": "OPERATES_SEGMENT",
      "period": null,
      "value": "Baby Care",
      "snippet": "Baby Care                                         9%        9%        9%"
    },
    {
      "fact_id": "FACT:f5c4697dc486e4553404",
      "source_doc": "PG_10K_2026.pdf",
      "page_num": 83,
      "company_id": "COMP:PG",
      "predicate": "OPERATES_SEGMENT",
      "period": null,
      "value": "Hair Care",
      "snippet": "Hair Care                                          9%        9%        9%"
    },
    {
      "fact_id": "FACT:bf1e73d8dfc1ae4df2e9",
      "source_doc": "PG_10K_2026.pdf",
      "page_num": 83,
      "company_id": "COMP:PG",
      "predicate": "OPERATES_SEGMENT",
      "period": null,
      "value": "Family Care",
      "snippet": "Family Care                                        8%        9%        9%"
    },
    {
      "fact_id": "FACT:f01f38d7a8a97d06812b",
      "source_doc": "PG_10K_2026.pdf",
      "page_num": 83,
      "company_id": "COMP:PG",
      "predicate": "OPERATES_SEGMENT",
      "period": null,
      "value": "Oral Care",
      "snippet": "Oral Care                                          8%        8%        8%"
    },
    {
      "fact_id": "FACT:9ea5c7e90799bc7ca93a",
      "source_doc": "PG_10K_2026.pdf",
      "page_num": 83,
      "company_id": "COMP:PG",
      "predicate": "OPERATES_SEGMENT",
      "period": null,
      "value": "Feminine Care",
      "snippet": "Feminine Care                                       7%        6%        6%"
    },
    {
      "fact_id": "FACT:2d638a15c1f6819040b2",
      "source_doc": "PG_10K_2026.pdf",
      "page_num": 83,
      "company_id": "COMP:PG",
      "predicate": "OPERATES_SEGMENT",
      "period": null,
      "value": "Personal Health Care",
      "snippet": "Personal Health Care                                    6%        6%        6%"
    },
    {
      "fact_id": "FACT:9506ba833420905c3b67",
      "source_doc": "PG_10K_2026.pdf",
      "page_num": 83,
      "company_id": "COMP:PG",
      "predicate": "OPERATES_SEGMENT",
      "period": null,
      "value": "Personal Care",
      "snippet": "Personal Care (1)                                      6%        6%        5%"
    },
    {
      "fact_id": "FACT:d33448e3ea85555329cf",
      "source_doc": "PG_10K_2026.pdf",
      "page_num": 83,
      "company_id": "COMP:PG",
      "predicate": "OPERATES_SEGMENT",
      "period": null,
      "value": "Skin Care",
      "snippet": "Skin Care (1)                                        4%        3%        4%"
    }
  ],
  "plan": {
    "steps": [
      {
        "output_var": "$members",
        "action": "traverse_relation",
        "relation_type": "OPERATES_SEGMENT",
        "direction": "out",
        "start_nodes": [
          "COMP:PG"
        ]
      }
    ]
  },
  "execution_trace": [
    {
      "action": "traverse_relation",
      "output_var": "$members",
      "rows": [
        {
          "node_id": "EXT:BEAUTY",
          "fact_ids": [
            "FACT:9186e4cd4be69901932b"
          ]
        },
        {
          "node_id": "EXT:GROOMING",
          "fact_ids": [
            "FACT:6d52b3df90a4fe52db22"
          ]
        },
        {
          "node_id": "EXT:HEALTH_CARE",
          "fact_ids": [
            "FACT:3706044ff2a543252120"
          ]
        },
        {
          "node_id": "EXT:FABRIC_HOME_CARE",
          "fact_ids": [
            "FACT:a199f6f20e58855c5589"
          ]
        },
        {
          "node_id": "EXT:BABY_FEMININE_FAMILY_CARE",
          "fact_ids": [
            "FACT:d6670f55e85fbb28251e"
          ]
        },
        {
          "node_id": "EXT:FABRIC_CARE",
          "fact_ids": [
            "FACT:91bccfcc1597358700e0"
          ]
        },
        {
          "node_id": "EXT:HOME_CARE",
          "fact_ids": [
            "FACT:d848e6e01eb132dbaadd"
          ]
        },
        {
          "node_id": "EXT:BABY_CARE",
          "fact_ids": [
            "FACT:1f525e6d46e3a94f20ec"
          ]
        },
        {
          "node_id": "EXT:HAIR_CARE",
          "fact_ids": [
            "FACT:f5c4697dc486e4553404"
          ]
        },
        {
          "node_id": "EXT:FAMILY_CARE",
          "fact_ids": [
            "FACT:bf1e73d8dfc1ae4df2e9"
          ]
        },
        {
          "node_id": "EXT:ORAL_CARE",
          "fact_ids": [
            "FACT:f01f38d7a8a97d06812b"
          ]
        },
        {
          "node_id": "EXT:FEMININE_CARE",
          "fact_ids": [
            "FACT:9ea5c7e90799bc7ca93a"
          ]
        },
        {
          "node_id": "EXT:PERSONAL_HEALTH_CARE",
          "fact_ids": [
            "FACT:2d638a15c1f6819040b2"
          ]
        },
        {
          "node_id": "EXT:PERSONAL_CARE",
          "fact_ids": [
            "FACT:9506ba833420905c3b67"
          ]
        },
        {
          "node_id": "EXT:SKIN_CARE",
          "fact_ids": [
            "FACT:d33448e3ea85555329cf"
          ]
        }
      ],
      "fact_ids": [
        "FACT:1f525e6d46e3a94f20ec",
        "FACT:2d638a15c1f6819040b2",
        "FACT:3706044ff2a543252120",
        "FACT:6d52b3df90a4fe52db22",
        "FACT:9186e4cd4be69901932b",
        "FACT:91bccfcc1597358700e0",
        "FACT:9506ba833420905c3b67",
        "FACT:9ea5c7e90799bc7ca93a",
        "FACT:a199f6f20e58855c5589",
        "FACT:bf1e73d8dfc1ae4df2e9",
        "FACT:d33448e3ea85555329cf",
        "FACT:d6670f55e85fbb28251e",
        "FACT:d848e6e01eb132dbaadd",
        "FACT:f01f38d7a8a97d06812b",
        "FACT:f5c4697dc486e4553404"
      ]
    }
  ]
}
```

### Q19 — multi-hop

Among Eli Lilly (LLY), Pfizer (PFE) and Merck (MRK), who is identified as CEO in the supplied filing of the company with the highest FY2025 research and development expense?

```json
{
  "gold": "Robert M. Davis",
  "predicted": null,
  "abstention_reason": "Unresolved qualifier(s): who is identified as CEO",
  "missed_facts": [
    {
      "doc_id": "LLY_10K_2025.pdf",
      "page_num": 86,
      "company_id": "COMP:LLY",
      "predicate": "METRIC:RD_EXPENSE",
      "period": "FY2025",
      "expected_value": "13337000000"
    },
    {
      "doc_id": "PFE_10K_2025.pdf",
      "page_num": 109,
      "company_id": "COMP:PFE",
      "predicate": "METRIC:RD_EXPENSE",
      "period": "FY2025",
      "expected_value": "10437000000"
    },
    {
      "doc_id": "MRK_10K_2025.pdf",
      "page_num": 144,
      "company_id": "COMP:MRK",
      "predicate": "METRIC:RD_EXPENSE",
      "period": "FY2025",
      "expected_value": "15789000000"
    },
    {
      "doc_id": "MRK_10K_2025.pdf",
      "page_num": 84,
      "company_id": "COMP:MRK",
      "predicate": "HAS_CEO",
      "period": null,
      "expected_value": "Robert M. Davis"
    }
  ],
  "extra_facts": [],
  "plan": {
    "steps": [
      {
        "output_var": "$abstain",
        "action": "abstain",
        "reason": "Unresolved qualifier(s): who is identified as CEO"
      }
    ]
  },
  "execution_trace": [
    {
      "action": "abstain",
      "output_var": "$abstain",
      "reason": "Unresolved qualifier(s): who is identified as CEO",
      "fact_ids": []
    }
  ]
}
```

### Q28 — cross-filing

Among JPMorgan Chase (JPM), Bank of America (BAC), Goldman Sachs (GS), Morgan Stanley (MS), Citigroup (C) and BlackRock (BLK), which had the lowest FY2025 diluted earnings per share?

```json
{
  "gold": "COMP:BAC",
  "predicted": null,
  "abstention_reason": "Missing METRIC:EPS_DILUTED for COMP:BAC FY2025",
  "missed_facts": [
    {
      "doc_id": "BAC_10K_2025.pdf",
      "page_num": 186,
      "company_id": "COMP:BAC",
      "predicate": "METRIC:EPS_DILUTED",
      "period": "FY2025",
      "expected_value": "3.81"
    },
    {
      "doc_id": "GS_10K_2025.pdf",
      "page_num": 318,
      "company_id": "COMP:GS",
      "predicate": "METRIC:EPS_DILUTED",
      "period": "FY2025",
      "expected_value": "51.32"
    },
    {
      "doc_id": "MS_10K_2025.pdf",
      "page_num": 208,
      "company_id": "COMP:MS",
      "predicate": "METRIC:EPS_DILUTED",
      "period": "FY2025",
      "expected_value": "10.21"
    },
    {
      "doc_id": "BLK_10K_2025.pdf",
      "page_num": 117,
      "company_id": "COMP:BLK",
      "predicate": "METRIC:EPS_DILUTED",
      "period": "FY2025",
      "expected_value": "35.31"
    }
  ],
  "extra_facts": [],
  "plan": {
    "steps": [
      {
        "output_var": "$values",
        "action": "lookup_metric",
        "company_ids": [
          "COMP:JPM",
          "COMP:C",
          "COMP:BAC",
          "COMP:GS",
          "COMP:MS",
          "COMP:BLK"
        ],
        "metric_id": "METRIC:EPS_DILUTED",
        "period_id": "FY2025"
      },
      {
        "output_var": "$answer",
        "action": "aggregate_compare",
        "input_var": "$values",
        "op": "min"
      }
    ]
  },
  "execution_trace": []
}
```

### Q30 — cross-filing

How many of the seven Financials companies in the corpus identify Delaware as their state of incorporation on the supplied 10-K cover?

```json
{
  "gold": 7,
  "predicted": 6.0,
  "abstention_reason": null,
  "missed_facts": [
    {
      "doc_id": "BAC_10K_2025.pdf",
      "page_num": 1,
      "company_id": "COMP:BAC",
      "predicate": "INCORPORATED_IN",
      "period": null,
      "expected_value": "Delaware"
    }
  ],
  "extra_facts": [],
  "plan": {
    "steps": [
      {
        "output_var": "$scope",
        "action": "filter_companies",
        "sector": "Financials"
      },
      {
        "output_var": "$members",
        "action": "traverse_relation",
        "relation_type": "INCORPORATED_IN",
        "direction": "in",
        "start_nodes": [
          "EXT:DELAWARE"
        ],
        "restrict_to": "$scope"
      },
      {
        "output_var": "$answer",
        "action": "aggregate_compare",
        "input_var": "$members",
        "op": "count"
      }
    ]
  },
  "execution_trace": [
    {
      "action": "filter_companies",
      "output_var": "$scope",
      "rows": [
        {
          "node_id": "COMP:JPM",
          "fact_ids": []
        },
        {
          "node_id": "COMP:BAC",
          "fact_ids": []
        },
        {
          "node_id": "COMP:GS",
          "fact_ids": []
        },
        {
          "node_id": "COMP:MS",
          "fact_ids": []
        },
        {
          "node_id": "COMP:WFC",
          "fact_ids": []
        },
        {
          "node_id": "COMP:C",
          "fact_ids": []
        },
        {
          "node_id": "COMP:BLK",
          "fact_ids": []
        }
      ],
      "fact_ids": []
    },
    {
      "action": "traverse_relation",
      "output_var": "$members",
      "rows": [
        {
          "node_id": "COMP:BLK",
          "fact_ids": [
            "FACT:5a1644aa2123625b0279"
          ]
        },
        {
          "node_id": "COMP:C",
          "fact_ids": [
            "FACT:8158d96e8baeb295c494"
          ]
        },
        {
          "node_id": "COMP:GS",
          "fact_ids": [
            "FACT:c2f80a8b8662baa84411"
          ]
        },
        {
          "node_id": "COMP:JPM",
          "fact_ids": [
            "FACT:7e1309b8fc42d61c2baa"
          ]
        },
        {
          "node_id": "COMP:MS",
          "fact_ids": [
            "FACT:3e6e7d3b89ffc2bc77f6"
          ]
        },
        {
          "node_id": "COMP:WFC",
          "fact_ids": [
            "FACT:61062f5e432492bfe82f"
          ]
        }
      ],
      "fact_ids": [
        "FACT:3e6e7d3b89ffc2bc77f6",
        "FACT:5a1644aa2123625b0279",
        "FACT:61062f5e432492bfe82f",
        "FACT:7e1309b8fc42d61c2baa",
        "FACT:8158d96e8baeb295c494",
        "FACT:c2f80a8b8662baa84411"
      ]
    },
    {
      "action": "aggregate_compare",
      "output_var": "$answer",
      "rows": [
        {
          "value": 6,
          "unit": "count",
          "fact_ids": [
            "FACT:3e6e7d3b89ffc2bc77f6",
            "FACT:5a1644aa2123625b0279",
            "FACT:61062f5e432492bfe82f",
            "FACT:7e1309b8fc42d61c2baa",
            "FACT:8158d96e8baeb295c494",
            "FACT:c2f80a8b8662baa84411"
          ]
        }
      ],
      "fact_ids": [
        "FACT:3e6e7d3b89ffc2bc77f6",
        "FACT:5a1644aa2123625b0279",
        "FACT:61062f5e432492bfe82f",
        "FACT:7e1309b8fc42d61c2baa",
        "FACT:8158d96e8baeb295c494",
        "FACT:c2f80a8b8662baa84411"
      ]
    }
  ]
}
```

## Abstentions

4 case(s).

### Q08 — single-fact

Which independent registered public accounting firm signed the financial-statement audit report in the supplied Goldman Sachs (GS) 10-K?

```json
{
  "gold": "EXT:PWC",
  "predicted": null,
  "abstention_reason": "The question asks for the independent registered public accounting firm (auditor) that signed the financial-statement audit report for Goldman Sachs, which is qualitative information not directly answerable via the graph query metrics/relations.",
  "missed_facts": [
    {
      "doc_id": "GS_10K_2025.pdf",
      "page_num": 317,
      "company_id": "COMP:GS",
      "predicate": "AUDITED_BY",
      "period": null,
      "expected_value": "PricewaterhouseCoopers LLP"
    }
  ],
  "extra_facts": [],
  "plan": {
    "steps": [
      {
        "output_var": "$answer",
        "action": "abstain",
        "reason": "The question asks for the independent registered public accounting firm (auditor) that signed the financial-statement audit report for Goldman Sachs, which is qualitative information not directly answerable via the graph query metrics/relations."
      }
    ]
  },
  "execution_trace": [
    {
      "action": "abstain",
      "output_var": "$answer",
      "reason": "The question asks for the independent registered public accounting firm (auditor) that signed the financial-statement audit report for Goldman Sachs, which is qualitative information not directly answerable via the graph query metrics/relations.",
      "fact_ids": []
    }
  ]
}
```

### Q09 — single-fact

In which city and state are Costco (COST) principal executive offices located, as printed on the supplied 10-K cover?

```json
{
  "gold": "Issaquah, WA",
  "predicted": null,
  "abstention_reason": "The question asks for the city and state of principal executive offices which is not a metric, relation-traversal, or derivable formula in the financial knowledge graph.",
  "missed_facts": [
    {
      "doc_id": "COST_10K_2026.pdf",
      "page_num": 1,
      "company_id": "COMP:COST",
      "predicate": "HEADQUARTERED_IN",
      "period": null,
      "expected_value": "Issaquah, WA"
    }
  ],
  "extra_facts": [],
  "plan": {
    "steps": [
      {
        "output_var": "$answer",
        "action": "abstain",
        "reason": "The question asks for the city and state of principal executive offices which is not a metric, relation-traversal, or derivable formula in the financial knowledge graph."
      }
    ]
  },
  "execution_trace": [
    {
      "action": "abstain",
      "output_var": "$answer",
      "reason": "The question asks for the city and state of principal executive offices which is not a metric, relation-traversal, or derivable formula in the financial knowledge graph.",
      "fact_ids": []
    }
  ]
}
```

### Q19 — multi-hop

Among Eli Lilly (LLY), Pfizer (PFE) and Merck (MRK), who is identified as CEO in the supplied filing of the company with the highest FY2025 research and development expense?

```json
{
  "gold": "Robert M. Davis",
  "predicted": null,
  "abstention_reason": "Unresolved qualifier(s): who is identified as CEO",
  "missed_facts": [
    {
      "doc_id": "LLY_10K_2025.pdf",
      "page_num": 86,
      "company_id": "COMP:LLY",
      "predicate": "METRIC:RD_EXPENSE",
      "period": "FY2025",
      "expected_value": "13337000000"
    },
    {
      "doc_id": "PFE_10K_2025.pdf",
      "page_num": 109,
      "company_id": "COMP:PFE",
      "predicate": "METRIC:RD_EXPENSE",
      "period": "FY2025",
      "expected_value": "10437000000"
    },
    {
      "doc_id": "MRK_10K_2025.pdf",
      "page_num": 144,
      "company_id": "COMP:MRK",
      "predicate": "METRIC:RD_EXPENSE",
      "period": "FY2025",
      "expected_value": "15789000000"
    },
    {
      "doc_id": "MRK_10K_2025.pdf",
      "page_num": 84,
      "company_id": "COMP:MRK",
      "predicate": "HAS_CEO",
      "period": null,
      "expected_value": "Robert M. Davis"
    }
  ],
  "extra_facts": [],
  "plan": {
    "steps": [
      {
        "output_var": "$abstain",
        "action": "abstain",
        "reason": "Unresolved qualifier(s): who is identified as CEO"
      }
    ]
  },
  "execution_trace": [
    {
      "action": "abstain",
      "output_var": "$abstain",
      "reason": "Unresolved qualifier(s): who is identified as CEO",
      "fact_ids": []
    }
  ]
}
```

### Q28 — cross-filing

Among JPMorgan Chase (JPM), Bank of America (BAC), Goldman Sachs (GS), Morgan Stanley (MS), Citigroup (C) and BlackRock (BLK), which had the lowest FY2025 diluted earnings per share?

```json
{
  "gold": "COMP:BAC",
  "predicted": null,
  "abstention_reason": "Missing METRIC:EPS_DILUTED for COMP:BAC FY2025",
  "missed_facts": [
    {
      "doc_id": "BAC_10K_2025.pdf",
      "page_num": 186,
      "company_id": "COMP:BAC",
      "predicate": "METRIC:EPS_DILUTED",
      "period": "FY2025",
      "expected_value": "3.81"
    },
    {
      "doc_id": "GS_10K_2025.pdf",
      "page_num": 318,
      "company_id": "COMP:GS",
      "predicate": "METRIC:EPS_DILUTED",
      "period": "FY2025",
      "expected_value": "51.32"
    },
    {
      "doc_id": "MS_10K_2025.pdf",
      "page_num": 208,
      "company_id": "COMP:MS",
      "predicate": "METRIC:EPS_DILUTED",
      "period": "FY2025",
      "expected_value": "10.21"
    },
    {
      "doc_id": "BLK_10K_2025.pdf",
      "page_num": 117,
      "company_id": "COMP:BLK",
      "predicate": "METRIC:EPS_DILUTED",
      "period": "FY2025",
      "expected_value": "35.31"
    }
  ],
  "extra_facts": [],
  "plan": {
    "steps": [
      {
        "output_var": "$values",
        "action": "lookup_metric",
        "company_ids": [
          "COMP:JPM",
          "COMP:C",
          "COMP:BAC",
          "COMP:GS",
          "COMP:MS",
          "COMP:BLK"
        ],
        "metric_id": "METRIC:EPS_DILUTED",
        "period_id": "FY2025"
      },
      {
        "output_var": "$answer",
        "action": "aggregate_compare",
        "input_var": "$values",
        "op": "min"
      }
    ]
  },
  "execution_trace": []
}
```

## Missing supporting facts

10 case(s).

### Q08 — single-fact

Which independent registered public accounting firm signed the financial-statement audit report in the supplied Goldman Sachs (GS) 10-K?

```json
{
  "gold": "EXT:PWC",
  "predicted": null,
  "abstention_reason": "The question asks for the independent registered public accounting firm (auditor) that signed the financial-statement audit report for Goldman Sachs, which is qualitative information not directly answerable via the graph query metrics/relations.",
  "missed_facts": [
    {
      "doc_id": "GS_10K_2025.pdf",
      "page_num": 317,
      "company_id": "COMP:GS",
      "predicate": "AUDITED_BY",
      "period": null,
      "expected_value": "PricewaterhouseCoopers LLP"
    }
  ],
  "extra_facts": [],
  "plan": {
    "steps": [
      {
        "output_var": "$answer",
        "action": "abstain",
        "reason": "The question asks for the independent registered public accounting firm (auditor) that signed the financial-statement audit report for Goldman Sachs, which is qualitative information not directly answerable via the graph query metrics/relations."
      }
    ]
  },
  "execution_trace": [
    {
      "action": "abstain",
      "output_var": "$answer",
      "reason": "The question asks for the independent registered public accounting firm (auditor) that signed the financial-statement audit report for Goldman Sachs, which is qualitative information not directly answerable via the graph query metrics/relations.",
      "fact_ids": []
    }
  ]
}
```

### Q09 — single-fact

In which city and state are Costco (COST) principal executive offices located, as printed on the supplied 10-K cover?

```json
{
  "gold": "Issaquah, WA",
  "predicted": null,
  "abstention_reason": "The question asks for the city and state of principal executive offices which is not a metric, relation-traversal, or derivable formula in the financial knowledge graph.",
  "missed_facts": [
    {
      "doc_id": "COST_10K_2026.pdf",
      "page_num": 1,
      "company_id": "COMP:COST",
      "predicate": "HEADQUARTERED_IN",
      "period": null,
      "expected_value": "Issaquah, WA"
    }
  ],
  "extra_facts": [],
  "plan": {
    "steps": [
      {
        "output_var": "$answer",
        "action": "abstain",
        "reason": "The question asks for the city and state of principal executive offices which is not a metric, relation-traversal, or derivable formula in the financial knowledge graph."
      }
    ]
  },
  "execution_trace": [
    {
      "action": "abstain",
      "output_var": "$answer",
      "reason": "The question asks for the city and state of principal executive offices which is not a metric, relation-traversal, or derivable formula in the financial knowledge graph.",
      "fact_ids": []
    }
  ]
}
```

### Q10 — single-fact

List the five US GAAP reportable segments of Procter & Gamble (PG) named in its supplied segment-information note.

```json
{
  "gold": [
    "Beauty",
    "Grooming",
    "Health Care",
    "Fabric & Home Care",
    "Baby, Feminine & Family Care"
  ],
  "predicted": [
    "EXT:BEAUTY",
    "EXT:GROOMING",
    "EXT:HEALTH_CARE",
    "EXT:FABRIC_HOME_CARE",
    "EXT:BABY_FEMININE_FAMILY_CARE",
    "EXT:FABRIC_CARE",
    "EXT:HOME_CARE",
    "EXT:BABY_CARE",
    "EXT:HAIR_CARE",
    "EXT:FAMILY_CARE",
    "EXT:ORAL_CARE",
    "EXT:FEMININE_CARE",
    "EXT:PERSONAL_HEALTH_CARE",
    "EXT:PERSONAL_CARE",
    "EXT:SKIN_CARE"
  ],
  "abstention_reason": null,
  "missed_facts": [
    {
      "doc_id": "PG_10K_2026.pdf",
      "page_num": 82,
      "company_id": "COMP:PG",
      "predicate": "OPERATES_SEGMENT",
      "period": null,
      "expected_value": "Beauty"
    },
    {
      "doc_id": "PG_10K_2026.pdf",
      "page_num": 82,
      "company_id": "COMP:PG",
      "predicate": "OPERATES_SEGMENT",
      "period": null,
      "expected_value": "Grooming"
    },
    {
      "doc_id": "PG_10K_2026.pdf",
      "page_num": 82,
      "company_id": "COMP:PG",
      "predicate": "OPERATES_SEGMENT",
      "period": null,
      "expected_value": "Health Care"
    },
    {
      "doc_id": "PG_10K_2026.pdf",
      "page_num": 82,
      "company_id": "COMP:PG",
      "predicate": "OPERATES_SEGMENT",
      "period": null,
      "expected_value": "Fabric & Home Care"
    },
    {
      "doc_id": "PG_10K_2026.pdf",
      "page_num": 82,
      "company_id": "COMP:PG",
      "predicate": "OPERATES_SEGMENT",
      "period": null,
      "expected_value": "Baby, Feminine & Family Care"
    }
  ],
  "extra_facts": [
    {
      "fact_id": "FACT:9186e4cd4be69901932b",
      "source_doc": "PG_10K_2026.pdf",
      "page_num": 44,
      "company_id": "COMP:PG",
      "predicate": "OPERATES_SEGMENT",
      "period": null,
      "value": "Beauty",
      "snippet": "Global market share of the Beauty segment decreased 0.3 points."
    },
    {
      "fact_id": "FACT:6d52b3df90a4fe52db22",
      "source_doc": "PG_10K_2026.pdf",
      "page_num": 44,
      "company_id": "COMP:PG",
      "predicate": "OPERATES_SEGMENT",
      "period": null,
      "value": "Grooming",
      "snippet": "Grooming"
    },
    {
      "fact_id": "FACT:3706044ff2a543252120",
      "source_doc": "PG_10K_2026.pdf",
      "page_num": 60,
      "company_id": "COMP:PG",
      "predicate": "OPERATES_SEGMENT",
      "period": null,
      "value": "Health Care",
      "snippet": "Health Care                                           4 %                (3) %      \u2014 %             1 %"
    },
    {
      "fact_id": "FACT:a199f6f20e58855c5589",
      "source_doc": "PG_10K_2026.pdf",
      "page_num": 60,
      "company_id": "COMP:PG",
      "predicate": "OPERATES_SEGMENT",
      "period": null,
      "value": "Fabric & Home Care",
      "snippet": "Fabric & Home Care                                   2 %                (1) %      \u2014 %             1 %"
    },
    {
      "fact_id": "FACT:d6670f55e85fbb28251e",
      "source_doc": "PG_10K_2026.pdf",
      "page_num": 60,
      "company_id": "COMP:PG",
      "predicate": "OPERATES_SEGMENT",
      "period": null,
      "value": "Baby, Feminine & Family Care",
      "snippet": "Baby, Feminine & Family Care                           1 %                (2) %      \u2014 %               (1) %"
    },
    {
      "fact_id": "FACT:91bccfcc1597358700e0",
      "source_doc": "PG_10K_2026.pdf",
      "page_num": 83,
      "company_id": "COMP:PG",
      "predicate": "OPERATES_SEGMENT",
      "period": null,
      "value": "Fabric Care",
      "snippet": "Fabric Care                                             23%        23%        24%"
    },
    {
      "fact_id": "FACT:d848e6e01eb132dbaadd",
      "source_doc": "PG_10K_2026.pdf",
      "page_num": 83,
      "company_id": "COMP:PG",
      "predicate": "OPERATES_SEGMENT",
      "period": null,
      "value": "Home Care",
      "snippet": "Home Care                                              12%        13%        12%"
    },
    {
      "fact_id": "FACT:1f525e6d46e3a94f20ec",
      "source_doc": "PG_10K_2026.pdf",
      "page_num": 83,
      "company_id": "COMP:PG",
      "predicate": "OPERATES_SEGMENT",
      "period": null,
      "value": "Baby Care",
      "snippet": "Baby Care                                         9%        9%        9%"
    },
    {
      "fact_id": "FACT:f5c4697dc486e4553404",
      "source_doc": "PG_10K_2026.pdf",
      "page_num": 83,
      "company_id": "COMP:PG",
      "predicate": "OPERATES_SEGMENT",
      "period": null,
      "value": "Hair Care",
      "snippet": "Hair Care                                          9%        9%        9%"
    },
    {
      "fact_id": "FACT:bf1e73d8dfc1ae4df2e9",
      "source_doc": "PG_10K_2026.pdf",
      "page_num": 83,
      "company_id": "COMP:PG",
      "predicate": "OPERATES_SEGMENT",
      "period": null,
      "value": "Family Care",
      "snippet": "Family Care                                        8%        9%        9%"
    },
    {
      "fact_id": "FACT:f01f38d7a8a97d06812b",
      "source_doc": "PG_10K_2026.pdf",
      "page_num": 83,
      "company_id": "COMP:PG",
      "predicate": "OPERATES_SEGMENT",
      "period": null,
      "value": "Oral Care",
      "snippet": "Oral Care                                          8%        8%        8%"
    },
    {
      "fact_id": "FACT:9ea5c7e90799bc7ca93a",
      "source_doc": "PG_10K_2026.pdf",
      "page_num": 83,
      "company_id": "COMP:PG",
      "predicate": "OPERATES_SEGMENT",
      "period": null,
      "value": "Feminine Care",
      "snippet": "Feminine Care                                       7%        6%        6%"
    },
    {
      "fact_id": "FACT:2d638a15c1f6819040b2",
      "source_doc": "PG_10K_2026.pdf",
      "page_num": 83,
      "company_id": "COMP:PG",
      "predicate": "OPERATES_SEGMENT",
      "period": null,
      "value": "Personal Health Care",
      "snippet": "Personal Health Care                                    6%        6%        6%"
    },
    {
      "fact_id": "FACT:9506ba833420905c3b67",
      "source_doc": "PG_10K_2026.pdf",
      "page_num": 83,
      "company_id": "COMP:PG",
      "predicate": "OPERATES_SEGMENT",
      "period": null,
      "value": "Personal Care",
      "snippet": "Personal Care (1)                                      6%        6%        5%"
    },
    {
      "fact_id": "FACT:d33448e3ea85555329cf",
      "source_doc": "PG_10K_2026.pdf",
      "page_num": 83,
      "company_id": "COMP:PG",
      "predicate": "OPERATES_SEGMENT",
      "period": null,
      "value": "Skin Care",
      "snippet": "Skin Care (1)                                        4%        3%        4%"
    }
  ],
  "plan": {
    "steps": [
      {
        "output_var": "$members",
        "action": "traverse_relation",
        "relation_type": "OPERATES_SEGMENT",
        "direction": "out",
        "start_nodes": [
          "COMP:PG"
        ]
      }
    ]
  },
  "execution_trace": [
    {
      "action": "traverse_relation",
      "output_var": "$members",
      "rows": [
        {
          "node_id": "EXT:BEAUTY",
          "fact_ids": [
            "FACT:9186e4cd4be69901932b"
          ]
        },
        {
          "node_id": "EXT:GROOMING",
          "fact_ids": [
            "FACT:6d52b3df90a4fe52db22"
          ]
        },
        {
          "node_id": "EXT:HEALTH_CARE",
          "fact_ids": [
            "FACT:3706044ff2a543252120"
          ]
        },
        {
          "node_id": "EXT:FABRIC_HOME_CARE",
          "fact_ids": [
            "FACT:a199f6f20e58855c5589"
          ]
        },
        {
          "node_id": "EXT:BABY_FEMININE_FAMILY_CARE",
          "fact_ids": [
            "FACT:d6670f55e85fbb28251e"
          ]
        },
        {
          "node_id": "EXT:FABRIC_CARE",
          "fact_ids": [
            "FACT:91bccfcc1597358700e0"
          ]
        },
        {
          "node_id": "EXT:HOME_CARE",
          "fact_ids": [
            "FACT:d848e6e01eb132dbaadd"
          ]
        },
        {
          "node_id": "EXT:BABY_CARE",
          "fact_ids": [
            "FACT:1f525e6d46e3a94f20ec"
          ]
        },
        {
          "node_id": "EXT:HAIR_CARE",
          "fact_ids": [
            "FACT:f5c4697dc486e4553404"
          ]
        },
        {
          "node_id": "EXT:FAMILY_CARE",
          "fact_ids": [
            "FACT:bf1e73d8dfc1ae4df2e9"
          ]
        },
        {
          "node_id": "EXT:ORAL_CARE",
          "fact_ids": [
            "FACT:f01f38d7a8a97d06812b"
          ]
        },
        {
          "node_id": "EXT:FEMININE_CARE",
          "fact_ids": [
            "FACT:9ea5c7e90799bc7ca93a"
          ]
        },
        {
          "node_id": "EXT:PERSONAL_HEALTH_CARE",
          "fact_ids": [
            "FACT:2d638a15c1f6819040b2"
          ]
        },
        {
          "node_id": "EXT:PERSONAL_CARE",
          "fact_ids": [
            "FACT:9506ba833420905c3b67"
          ]
        },
        {
          "node_id": "EXT:SKIN_CARE",
          "fact_ids": [
            "FACT:d33448e3ea85555329cf"
          ]
        }
      ],
      "fact_ids": [
        "FACT:1f525e6d46e3a94f20ec",
        "FACT:2d638a15c1f6819040b2",
        "FACT:3706044ff2a543252120",
        "FACT:6d52b3df90a4fe52db22",
        "FACT:9186e4cd4be69901932b",
        "FACT:91bccfcc1597358700e0",
        "FACT:9506ba833420905c3b67",
        "FACT:9ea5c7e90799bc7ca93a",
        "FACT:a199f6f20e58855c5589",
        "FACT:bf1e73d8dfc1ae4df2e9",
        "FACT:d33448e3ea85555329cf",
        "FACT:d6670f55e85fbb28251e",
        "FACT:d848e6e01eb132dbaadd",
        "FACT:f01f38d7a8a97d06812b",
        "FACT:f5c4697dc486e4553404"
      ]
    }
  ]
}
```

### Q17 — multi-hop

Among the seven Semiconductors companies in the corpus, using the auditor identified in each supplied filing, which PwC-audited company had the highest FY2025 consolidated net income?

```json
{
  "gold": "COMP:NVDA",
  "predicted": "COMP:NVDA",
  "abstention_reason": null,
  "missed_facts": [
    {
      "doc_id": "AMD_10K_2025.pdf",
      "page_num": 144,
      "company_id": "COMP:AMD",
      "predicate": "AUDITED_BY",
      "period": null,
      "expected_value": "Ernst & Young LLP"
    },
    {
      "doc_id": "INTC_10K_2025.pdf",
      "page_num": 99,
      "company_id": "COMP:INTC",
      "predicate": "AUDITED_BY",
      "period": null,
      "expected_value": "Ernst & Young LLP"
    },
    {
      "doc_id": "TXN_10K_2025.pdf",
      "page_num": 91,
      "company_id": "COMP:TXN",
      "predicate": "AUDITED_BY",
      "period": null,
      "expected_value": "Ernst & Young LLP"
    }
  ],
  "extra_facts": [],
  "plan": {
    "steps": [
      {
        "output_var": "$scope",
        "action": "filter_companies",
        "sector": "Semiconductors"
      },
      {
        "output_var": "$members",
        "action": "traverse_relation",
        "relation_type": "AUDITED_BY",
        "direction": "in",
        "start_nodes": [
          "EXT:PWC"
        ],
        "restrict_to": "$scope"
      },
      {
        "output_var": "$values",
        "action": "lookup_metric",
        "company_ids": "$members",
        "metric_id": "METRIC:NET_INCOME",
        "period_id": "FY2025"
      },
      {
        "output_var": "$answer",
        "action": "aggregate_compare",
        "input_var": "$values",
        "op": "max"
      }
    ]
  },
  "execution_trace": [
    {
      "action": "filter_companies",
      "output_var": "$scope",
      "rows": [
        {
          "node_id": "COMP:NVDA",
          "fact_ids": []
        },
        {
          "node_id": "COMP:AMD",
          "fact_ids": []
        },
        {
          "node_id": "COMP:INTC",
          "fact_ids": []
        },
        {
          "node_id": "COMP:QCOM",
          "fact_ids": []
        },
        {
          "node_id": "COMP:AVGO",
          "fact_ids": []
        },
        {
          "node_id": "COMP:TXN",
          "fact_ids": []
        },
        {
          "node_id": "COMP:MU",
          "fact_ids": []
        }
      ],
      "fact_ids": []
    },
    {
      "action": "traverse_relation",
      "output_var": "$members",
      "rows": [
        {
          "node_id": "COMP:AVGO",
          "fact_ids": [
            "FACT:b538edd8d60a7534973d"
          ]
        },
        {
          "node_id": "COMP:MU",
          "fact_ids": [
            "FACT:13ea680204c483d67029"
          ]
        },
        {
          "node_id": "COMP:NVDA",
          "fact_ids": [
            "FACT:e48d04c5f429fdb2b04d"
          ]
        },
        {
          "node_id": "COMP:QCOM",
          "fact_ids": [
            "FACT:478d12bbac59c268509f"
          ]
        }
      ],
      "fact_ids": [
        "FACT:13ea680204c483d67029",
        "FACT:478d12bbac59c268509f",
        "FACT:b538edd8d60a7534973d",
        "FACT:e48d04c5f429fdb2b04d"
      ]
    },
    {
      "action": "lookup_metric",
      "output_var": "$values",
      "rows": [
        {
          "node_id": "COMP:AVGO",
          "value": 23126000000.0,
          "unit": "USD",
          "fact_ids": [
            "FACT:b538edd8d60a7534973d",
            "FACT:289911772c61dfb8f545"
          ]
        },
        {
          "node_id": "COMP:MU",
          "value": 8539000000.0,
          "unit": "USD",
          "fact_ids": [
            "FACT:13ea680204c483d67029",
            "FACT:834567f83146af271d95"
          ]
        },
        {
          "node_id": "COMP:NVDA",
          "value": 72880000000.0,
          "unit": "USD",
          "fact_ids": [
            "FACT:e48d04c5f429fdb2b04d",
            "FACT:bdaf3ecc9cead4ad4850"
          ]
        },
        {
          "node_id": "COMP:QCOM",
          "value": 5541000000.0,
          "unit": "USD",
          "fact_ids": [
            "FACT:478d12bbac59c268509f",
            "FACT:d50d95c51a490a9f2457"
          ]
        }
      ],
      "fact_ids": [
        "FACT:13ea680204c483d67029",
        "FACT:289911772c61dfb8f545",
        "FACT:478d12bbac59c268509f",
        "FACT:834567f83146af271d95",
        "FACT:b538edd8d60a7534973d",
        "FACT:bdaf3ecc9cead4ad4850",
        "FACT:d50d95c51a490a9f2457",
        "FACT:e48d04c5f429fdb2b04d"
      ]
    },
    {
      "action": "aggregate_compare",
      "output_var": "$answer",
      "rows": [
        {
          "node_id": "COMP:NVDA",
          "value": 72880000000.0,
          "unit": "USD",
          "fact_ids": [
            "FACT:e48d04c5f429fdb2b04d",
            "FACT:bdaf3ecc9cead4ad4850"
          ]
        }
      ],
      "fact_ids": [
        "FACT:13ea680204c483d67029",
        "FACT:289911772c61dfb8f545",
        "FACT:478d12bbac59c268509f",
        "FACT:834567f83146af271d95",
        "FACT:b538edd8d60a7534973d",
        "FACT:bdaf3ecc9cead4ad4850",
        "FACT:d50d95c51a490a9f2457",
        "FACT:e48d04c5f429fdb2b04d"
      ]
    }
  ]
}
```

### Q18 — multi-hop

Among Costco (COST), Home Depot (HD) and Target (TGT), what was the FY2025 operating margin of the company whose supplied cover lists principal executive offices in Issaquah, WA? Give a percent using total revenue.

```json
{
  "gold": 3.7724126655403563,
  "predicted": 3.7724126655403563,
  "abstention_reason": null,
  "missed_facts": [
    {
      "doc_id": "HD_10K_2026.pdf",
      "page_num": 1,
      "company_id": "COMP:HD",
      "predicate": "HEADQUARTERED_IN",
      "period": null,
      "expected_value": "Atlanta, Georgia"
    },
    {
      "doc_id": "TGT_10K_2026.pdf",
      "page_num": 1,
      "company_id": "COMP:TGT",
      "predicate": "HEADQUARTERED_IN",
      "period": null,
      "expected_value": "Minneapolis, Minnesota"
    }
  ],
  "extra_facts": [],
  "plan": {
    "steps": [
      {
        "output_var": "$target_company",
        "action": "traverse_relation",
        "relation_type": "HEADQUARTERED_IN",
        "direction": "in",
        "start_nodes": [
          "EXT:ISSAQUAH_WASHINGTON"
        ],
        "restrict_to": [
          "COMP:COST",
          "COMP:HD",
          "COMP:TGT"
        ]
      },
      {
        "output_var": "$answer",
        "action": "compute_derived",
        "company_ids": "$target_company",
        "formula_id": "OPERATING_MARGIN",
        "period_id": "FY2025"
      }
    ]
  },
  "execution_trace": [
    {
      "action": "traverse_relation",
      "output_var": "$target_company",
      "rows": [
        {
          "node_id": "COMP:COST",
          "fact_ids": [
            "FACT:a0ccc629e0b0afcdfad3"
          ]
        }
      ],
      "fact_ids": [
        "FACT:a0ccc629e0b0afcdfad3"
      ]
    },
    {
      "action": "compute_derived",
      "output_var": "$answer",
      "rows": [
        {
          "node_id": "COMP:COST",
          "value": 3.7724126655403563,
          "unit": "percent",
          "fact_ids": [
            "FACT:a0ccc629e0b0afcdfad3",
            "FACT:9e5d5a2cbc10d11b0451",
            "FACT:8e3c8b76d23e41dbad39"
          ]
        }
      ],
      "fact_ids": [
        "FACT:8e3c8b76d23e41dbad39",
        "FACT:9e5d5a2cbc10d11b0451",
        "FACT:a0ccc629e0b0afcdfad3"
      ]
    }
  ]
}
```

### Q19 — multi-hop

Among Eli Lilly (LLY), Pfizer (PFE) and Merck (MRK), who is identified as CEO in the supplied filing of the company with the highest FY2025 research and development expense?

```json
{
  "gold": "Robert M. Davis",
  "predicted": null,
  "abstention_reason": "Unresolved qualifier(s): who is identified as CEO",
  "missed_facts": [
    {
      "doc_id": "LLY_10K_2025.pdf",
      "page_num": 86,
      "company_id": "COMP:LLY",
      "predicate": "METRIC:RD_EXPENSE",
      "period": "FY2025",
      "expected_value": "13337000000"
    },
    {
      "doc_id": "PFE_10K_2025.pdf",
      "page_num": 109,
      "company_id": "COMP:PFE",
      "predicate": "METRIC:RD_EXPENSE",
      "period": "FY2025",
      "expected_value": "10437000000"
    },
    {
      "doc_id": "MRK_10K_2025.pdf",
      "page_num": 144,
      "company_id": "COMP:MRK",
      "predicate": "METRIC:RD_EXPENSE",
      "period": "FY2025",
      "expected_value": "15789000000"
    },
    {
      "doc_id": "MRK_10K_2025.pdf",
      "page_num": 84,
      "company_id": "COMP:MRK",
      "predicate": "HAS_CEO",
      "period": null,
      "expected_value": "Robert M. Davis"
    }
  ],
  "extra_facts": [],
  "plan": {
    "steps": [
      {
        "output_var": "$abstain",
        "action": "abstain",
        "reason": "Unresolved qualifier(s): who is identified as CEO"
      }
    ]
  },
  "execution_trace": [
    {
      "action": "abstain",
      "output_var": "$abstain",
      "reason": "Unresolved qualifier(s): who is identified as CEO",
      "fact_ids": []
    }
  ]
}
```

### Q20 — multi-hop

Among Apple (AAPL), Microsoft (MSFT) and Alphabet (GOOGL), using the auditor identified in each supplied filing, which EY-audited company had the highest FY2025 free cash flow, defined as operating cash flow minus cash purchases of property, plant and equipment?

```json
{
  "gold": "COMP:AAPL",
  "predicted": "COMP:AAPL",
  "abstention_reason": null,
  "missed_facts": [
    {
      "doc_id": "MSFT_10K_2026.pdf",
      "page_num": 138,
      "company_id": "COMP:MSFT",
      "predicate": "AUDITED_BY",
      "period": null,
      "expected_value": "DELOITTE & TOUCHE LLP"
    }
  ],
  "extra_facts": [],
  "plan": {
    "steps": [
      {
        "output_var": "$ey_audited_companies",
        "action": "traverse_relation",
        "relation_type": "AUDITED_BY",
        "direction": "in",
        "start_nodes": [
          "EXT:EY"
        ],
        "restrict_to": [
          "COMP:AAPL",
          "COMP:MSFT",
          "COMP:GOOGL"
        ]
      },
      {
        "output_var": "$fcf_values",
        "action": "compute_derived",
        "company_ids": "$ey_audited_companies",
        "formula_id": "FREE_CASH_FLOW",
        "period_id": "FY2025",
        "metric_id": "METRIC:OPERATING_CASH_FLOW",
        "numerator_metric_id": "METRIC:OPERATING_CASH_FLOW",
        "denominator_metric_id": "METRIC:CAPEX"
      },
      {
        "output_var": "$answer",
        "action": "aggregate_compare",
        "input_var": "$fcf_values",
        "op": "max"
      }
    ]
  },
  "execution_trace": [
    {
      "action": "traverse_relation",
      "output_var": "$ey_audited_companies",
      "rows": [
        {
          "node_id": "COMP:AAPL",
          "fact_ids": [
            "FACT:0cdc0a014d6ab96442a9"
          ]
        },
        {
          "node_id": "COMP:GOOGL",
          "fact_ids": [
            "FACT:50ab0c63b3c596114663"
          ]
        }
      ],
      "fact_ids": [
        "FACT:0cdc0a014d6ab96442a9",
        "FACT:50ab0c63b3c596114663"
      ]
    },
    {
      "action": "compute_derived",
      "output_var": "$fcf_values",
      "rows": [
        {
          "node_id": "COMP:AAPL",
          "value": 98767000000.0,
          "unit": "USD",
          "fact_ids": [
            "FACT:0cdc0a014d6ab96442a9",
            "FACT:d47f4cae6d7d32e45009",
            "FACT:fa5dcdf0fa7a2c77c8b2"
          ]
        },
        {
          "node_id": "COMP:GOOGL",
          "value": 73266000000.0,
          "unit": "USD",
          "fact_ids": [
            "FACT:50ab0c63b3c596114663",
            "FACT:98142c842196adc145ff",
            "FACT:a34f034d9c18122bcd89"
          ]
        }
      ],
      "fact_ids": [
        "FACT:0cdc0a014d6ab96442a9",
        "FACT:50ab0c63b3c596114663",
        "FACT:98142c842196adc145ff",
        "FACT:a34f034d9c18122bcd89",
        "FACT:d47f4cae6d7d32e45009",
        "FACT:fa5dcdf0fa7a2c77c8b2"
      ]
    },
    {
      "action": "aggregate_compare",
      "output_var": "$answer",
      "rows": [
        {
          "node_id": "COMP:AAPL",
          "value": 98767000000.0,
          "unit": "USD",
          "fact_ids": [
            "FACT:0cdc0a014d6ab96442a9",
            "FACT:d47f4cae6d7d32e45009",
            "FACT:fa5dcdf0fa7a2c77c8b2"
          ]
        }
      ],
      "fact_ids": [
        "FACT:0cdc0a014d6ab96442a9",
        "FACT:50ab0c63b3c596114663",
        "FACT:98142c842196adc145ff",
        "FACT:a34f034d9c18122bcd89",
        "FACT:d47f4cae6d7d32e45009",
        "FACT:fa5dcdf0fa7a2c77c8b2"
      ]
    }
  ]
}
```

### Q28 — cross-filing

Among JPMorgan Chase (JPM), Bank of America (BAC), Goldman Sachs (GS), Morgan Stanley (MS), Citigroup (C) and BlackRock (BLK), which had the lowest FY2025 diluted earnings per share?

```json
{
  "gold": "COMP:BAC",
  "predicted": null,
  "abstention_reason": "Missing METRIC:EPS_DILUTED for COMP:BAC FY2025",
  "missed_facts": [
    {
      "doc_id": "BAC_10K_2025.pdf",
      "page_num": 186,
      "company_id": "COMP:BAC",
      "predicate": "METRIC:EPS_DILUTED",
      "period": "FY2025",
      "expected_value": "3.81"
    },
    {
      "doc_id": "GS_10K_2025.pdf",
      "page_num": 318,
      "company_id": "COMP:GS",
      "predicate": "METRIC:EPS_DILUTED",
      "period": "FY2025",
      "expected_value": "51.32"
    },
    {
      "doc_id": "MS_10K_2025.pdf",
      "page_num": 208,
      "company_id": "COMP:MS",
      "predicate": "METRIC:EPS_DILUTED",
      "period": "FY2025",
      "expected_value": "10.21"
    },
    {
      "doc_id": "BLK_10K_2025.pdf",
      "page_num": 117,
      "company_id": "COMP:BLK",
      "predicate": "METRIC:EPS_DILUTED",
      "period": "FY2025",
      "expected_value": "35.31"
    }
  ],
  "extra_facts": [],
  "plan": {
    "steps": [
      {
        "output_var": "$values",
        "action": "lookup_metric",
        "company_ids": [
          "COMP:JPM",
          "COMP:C",
          "COMP:BAC",
          "COMP:GS",
          "COMP:MS",
          "COMP:BLK"
        ],
        "metric_id": "METRIC:EPS_DILUTED",
        "period_id": "FY2025"
      },
      {
        "output_var": "$answer",
        "action": "aggregate_compare",
        "input_var": "$values",
        "op": "min"
      }
    ]
  },
  "execution_trace": []
}
```

### Q29 — cross-filing

List all companies in the corpus Semiconductors sector whose supplied financial-statement audit report is signed by Ernst & Young (EY).

```json
{
  "gold": [
    "COMP:AMD",
    "COMP:INTC",
    "COMP:TXN"
  ],
  "predicted": [
    "COMP:AMD",
    "COMP:INTC",
    "COMP:TXN"
  ],
  "abstention_reason": null,
  "missed_facts": [
    {
      "doc_id": "NVDA_10K_2026.pdf",
      "page_num": 86,
      "company_id": "COMP:NVDA",
      "predicate": "AUDITED_BY",
      "period": null,
      "expected_value": "PricewaterhouseCoopers LLP"
    },
    {
      "doc_id": "QCOM_10K_2026.pdf",
      "page_num": 93,
      "company_id": "COMP:QCOM",
      "predicate": "AUDITED_BY",
      "period": null,
      "expected_value": "PricewaterhouseCoopers LLP"
    },
    {
      "doc_id": "AVGO_10K_2025.pdf",
      "page_num": 84,
      "company_id": "COMP:AVGO",
      "predicate": "AUDITED_BY",
      "period": null,
      "expected_value": "PricewaterhouseCoopers LLP"
    },
    {
      "doc_id": "MU_10K_2026.pdf",
      "page_num": 162,
      "company_id": "COMP:MU",
      "predicate": "AUDITED_BY",
      "period": null,
      "expected_value": "PricewaterhouseCoopers LLP"
    }
  ],
  "extra_facts": [],
  "plan": {
    "steps": [
      {
        "output_var": "$scope",
        "action": "filter_companies",
        "sector": "Semiconductors"
      },
      {
        "output_var": "$members",
        "action": "traverse_relation",
        "relation_type": "AUDITED_BY",
        "direction": "in",
        "start_nodes": [
          "EXT:EY"
        ],
        "restrict_to": "$scope"
      }
    ]
  },
  "execution_trace": [
    {
      "action": "filter_companies",
      "output_var": "$scope",
      "rows": [
        {
          "node_id": "COMP:NVDA",
          "fact_ids": []
        },
        {
          "node_id": "COMP:AMD",
          "fact_ids": []
        },
        {
          "node_id": "COMP:INTC",
          "fact_ids": []
        },
        {
          "node_id": "COMP:QCOM",
          "fact_ids": []
        },
        {
          "node_id": "COMP:AVGO",
          "fact_ids": []
        },
        {
          "node_id": "COMP:TXN",
          "fact_ids": []
        },
        {
          "node_id": "COMP:MU",
          "fact_ids": []
        }
      ],
      "fact_ids": []
    },
    {
      "action": "traverse_relation",
      "output_var": "$members",
      "rows": [
        {
          "node_id": "COMP:AMD",
          "fact_ids": [
            "FACT:1201dc5c4c4a76ff21e9"
          ]
        },
        {
          "node_id": "COMP:INTC",
          "fact_ids": [
            "FACT:c75b44b67c0d3b99a913"
          ]
        },
        {
          "node_id": "COMP:TXN",
          "fact_ids": [
            "FACT:337b73f5fc24fdf08554"
          ]
        }
      ],
      "fact_ids": [
        "FACT:1201dc5c4c4a76ff21e9",
        "FACT:337b73f5fc24fdf08554",
        "FACT:c75b44b67c0d3b99a913"
      ]
    }
  ]
}
```

### Q30 — cross-filing

How many of the seven Financials companies in the corpus identify Delaware as their state of incorporation on the supplied 10-K cover?

```json
{
  "gold": 7,
  "predicted": 6.0,
  "abstention_reason": null,
  "missed_facts": [
    {
      "doc_id": "BAC_10K_2025.pdf",
      "page_num": 1,
      "company_id": "COMP:BAC",
      "predicate": "INCORPORATED_IN",
      "period": null,
      "expected_value": "Delaware"
    }
  ],
  "extra_facts": [],
  "plan": {
    "steps": [
      {
        "output_var": "$scope",
        "action": "filter_companies",
        "sector": "Financials"
      },
      {
        "output_var": "$members",
        "action": "traverse_relation",
        "relation_type": "INCORPORATED_IN",
        "direction": "in",
        "start_nodes": [
          "EXT:DELAWARE"
        ],
        "restrict_to": "$scope"
      },
      {
        "output_var": "$answer",
        "action": "aggregate_compare",
        "input_var": "$members",
        "op": "count"
      }
    ]
  },
  "execution_trace": [
    {
      "action": "filter_companies",
      "output_var": "$scope",
      "rows": [
        {
          "node_id": "COMP:JPM",
          "fact_ids": []
        },
        {
          "node_id": "COMP:BAC",
          "fact_ids": []
        },
        {
          "node_id": "COMP:GS",
          "fact_ids": []
        },
        {
          "node_id": "COMP:MS",
          "fact_ids": []
        },
        {
          "node_id": "COMP:WFC",
          "fact_ids": []
        },
        {
          "node_id": "COMP:C",
          "fact_ids": []
        },
        {
          "node_id": "COMP:BLK",
          "fact_ids": []
        }
      ],
      "fact_ids": []
    },
    {
      "action": "traverse_relation",
      "output_var": "$members",
      "rows": [
        {
          "node_id": "COMP:BLK",
          "fact_ids": [
            "FACT:5a1644aa2123625b0279"
          ]
        },
        {
          "node_id": "COMP:C",
          "fact_ids": [
            "FACT:8158d96e8baeb295c494"
          ]
        },
        {
          "node_id": "COMP:GS",
          "fact_ids": [
            "FACT:c2f80a8b8662baa84411"
          ]
        },
        {
          "node_id": "COMP:JPM",
          "fact_ids": [
            "FACT:7e1309b8fc42d61c2baa"
          ]
        },
        {
          "node_id": "COMP:MS",
          "fact_ids": [
            "FACT:3e6e7d3b89ffc2bc77f6"
          ]
        },
        {
          "node_id": "COMP:WFC",
          "fact_ids": [
            "FACT:61062f5e432492bfe82f"
          ]
        }
      ],
      "fact_ids": [
        "FACT:3e6e7d3b89ffc2bc77f6",
        "FACT:5a1644aa2123625b0279",
        "FACT:61062f5e432492bfe82f",
        "FACT:7e1309b8fc42d61c2baa",
        "FACT:8158d96e8baeb295c494",
        "FACT:c2f80a8b8662baa84411"
      ]
    },
    {
      "action": "aggregate_compare",
      "output_var": "$answer",
      "rows": [
        {
          "value": 6,
          "unit": "count",
          "fact_ids": [
            "FACT:3e6e7d3b89ffc2bc77f6",
            "FACT:5a1644aa2123625b0279",
            "FACT:61062f5e432492bfe82f",
            "FACT:7e1309b8fc42d61c2baa",
            "FACT:8158d96e8baeb295c494",
            "FACT:c2f80a8b8662baa84411"
          ]
        }
      ],
      "fact_ids": [
        "FACT:3e6e7d3b89ffc2bc77f6",
        "FACT:5a1644aa2123625b0279",
        "FACT:61062f5e432492bfe82f",
        "FACT:7e1309b8fc42d61c2baa",
        "FACT:8158d96e8baeb295c494",
        "FACT:c2f80a8b8662baa84411"
      ]
    }
  ]
}
```

## Extra or duplicate supporting facts

1 case(s).

### Q10 — single-fact

List the five US GAAP reportable segments of Procter & Gamble (PG) named in its supplied segment-information note.

```json
{
  "gold": [
    "Beauty",
    "Grooming",
    "Health Care",
    "Fabric & Home Care",
    "Baby, Feminine & Family Care"
  ],
  "predicted": [
    "EXT:BEAUTY",
    "EXT:GROOMING",
    "EXT:HEALTH_CARE",
    "EXT:FABRIC_HOME_CARE",
    "EXT:BABY_FEMININE_FAMILY_CARE",
    "EXT:FABRIC_CARE",
    "EXT:HOME_CARE",
    "EXT:BABY_CARE",
    "EXT:HAIR_CARE",
    "EXT:FAMILY_CARE",
    "EXT:ORAL_CARE",
    "EXT:FEMININE_CARE",
    "EXT:PERSONAL_HEALTH_CARE",
    "EXT:PERSONAL_CARE",
    "EXT:SKIN_CARE"
  ],
  "abstention_reason": null,
  "missed_facts": [
    {
      "doc_id": "PG_10K_2026.pdf",
      "page_num": 82,
      "company_id": "COMP:PG",
      "predicate": "OPERATES_SEGMENT",
      "period": null,
      "expected_value": "Beauty"
    },
    {
      "doc_id": "PG_10K_2026.pdf",
      "page_num": 82,
      "company_id": "COMP:PG",
      "predicate": "OPERATES_SEGMENT",
      "period": null,
      "expected_value": "Grooming"
    },
    {
      "doc_id": "PG_10K_2026.pdf",
      "page_num": 82,
      "company_id": "COMP:PG",
      "predicate": "OPERATES_SEGMENT",
      "period": null,
      "expected_value": "Health Care"
    },
    {
      "doc_id": "PG_10K_2026.pdf",
      "page_num": 82,
      "company_id": "COMP:PG",
      "predicate": "OPERATES_SEGMENT",
      "period": null,
      "expected_value": "Fabric & Home Care"
    },
    {
      "doc_id": "PG_10K_2026.pdf",
      "page_num": 82,
      "company_id": "COMP:PG",
      "predicate": "OPERATES_SEGMENT",
      "period": null,
      "expected_value": "Baby, Feminine & Family Care"
    }
  ],
  "extra_facts": [
    {
      "fact_id": "FACT:9186e4cd4be69901932b",
      "source_doc": "PG_10K_2026.pdf",
      "page_num": 44,
      "company_id": "COMP:PG",
      "predicate": "OPERATES_SEGMENT",
      "period": null,
      "value": "Beauty",
      "snippet": "Global market share of the Beauty segment decreased 0.3 points."
    },
    {
      "fact_id": "FACT:6d52b3df90a4fe52db22",
      "source_doc": "PG_10K_2026.pdf",
      "page_num": 44,
      "company_id": "COMP:PG",
      "predicate": "OPERATES_SEGMENT",
      "period": null,
      "value": "Grooming",
      "snippet": "Grooming"
    },
    {
      "fact_id": "FACT:3706044ff2a543252120",
      "source_doc": "PG_10K_2026.pdf",
      "page_num": 60,
      "company_id": "COMP:PG",
      "predicate": "OPERATES_SEGMENT",
      "period": null,
      "value": "Health Care",
      "snippet": "Health Care                                           4 %                (3) %      \u2014 %             1 %"
    },
    {
      "fact_id": "FACT:a199f6f20e58855c5589",
      "source_doc": "PG_10K_2026.pdf",
      "page_num": 60,
      "company_id": "COMP:PG",
      "predicate": "OPERATES_SEGMENT",
      "period": null,
      "value": "Fabric & Home Care",
      "snippet": "Fabric & Home Care                                   2 %                (1) %      \u2014 %             1 %"
    },
    {
      "fact_id": "FACT:d6670f55e85fbb28251e",
      "source_doc": "PG_10K_2026.pdf",
      "page_num": 60,
      "company_id": "COMP:PG",
      "predicate": "OPERATES_SEGMENT",
      "period": null,
      "value": "Baby, Feminine & Family Care",
      "snippet": "Baby, Feminine & Family Care                           1 %                (2) %      \u2014 %               (1) %"
    },
    {
      "fact_id": "FACT:91bccfcc1597358700e0",
      "source_doc": "PG_10K_2026.pdf",
      "page_num": 83,
      "company_id": "COMP:PG",
      "predicate": "OPERATES_SEGMENT",
      "period": null,
      "value": "Fabric Care",
      "snippet": "Fabric Care                                             23%        23%        24%"
    },
    {
      "fact_id": "FACT:d848e6e01eb132dbaadd",
      "source_doc": "PG_10K_2026.pdf",
      "page_num": 83,
      "company_id": "COMP:PG",
      "predicate": "OPERATES_SEGMENT",
      "period": null,
      "value": "Home Care",
      "snippet": "Home Care                                              12%        13%        12%"
    },
    {
      "fact_id": "FACT:1f525e6d46e3a94f20ec",
      "source_doc": "PG_10K_2026.pdf",
      "page_num": 83,
      "company_id": "COMP:PG",
      "predicate": "OPERATES_SEGMENT",
      "period": null,
      "value": "Baby Care",
      "snippet": "Baby Care                                         9%        9%        9%"
    },
    {
      "fact_id": "FACT:f5c4697dc486e4553404",
      "source_doc": "PG_10K_2026.pdf",
      "page_num": 83,
      "company_id": "COMP:PG",
      "predicate": "OPERATES_SEGMENT",
      "period": null,
      "value": "Hair Care",
      "snippet": "Hair Care                                          9%        9%        9%"
    },
    {
      "fact_id": "FACT:bf1e73d8dfc1ae4df2e9",
      "source_doc": "PG_10K_2026.pdf",
      "page_num": 83,
      "company_id": "COMP:PG",
      "predicate": "OPERATES_SEGMENT",
      "period": null,
      "value": "Family Care",
      "snippet": "Family Care                                        8%        9%        9%"
    },
    {
      "fact_id": "FACT:f01f38d7a8a97d06812b",
      "source_doc": "PG_10K_2026.pdf",
      "page_num": 83,
      "company_id": "COMP:PG",
      "predicate": "OPERATES_SEGMENT",
      "period": null,
      "value": "Oral Care",
      "snippet": "Oral Care                                          8%        8%        8%"
    },
    {
      "fact_id": "FACT:9ea5c7e90799bc7ca93a",
      "source_doc": "PG_10K_2026.pdf",
      "page_num": 83,
      "company_id": "COMP:PG",
      "predicate": "OPERATES_SEGMENT",
      "period": null,
      "value": "Feminine Care",
      "snippet": "Feminine Care                                       7%        6%        6%"
    },
    {
      "fact_id": "FACT:2d638a15c1f6819040b2",
      "source_doc": "PG_10K_2026.pdf",
      "page_num": 83,
      "company_id": "COMP:PG",
      "predicate": "OPERATES_SEGMENT",
      "period": null,
      "value": "Personal Health Care",
      "snippet": "Personal Health Care                                    6%        6%        6%"
    },
    {
      "fact_id": "FACT:9506ba833420905c3b67",
      "source_doc": "PG_10K_2026.pdf",
      "page_num": 83,
      "company_id": "COMP:PG",
      "predicate": "OPERATES_SEGMENT",
      "period": null,
      "value": "Personal Care",
      "snippet": "Personal Care (1)                                      6%        6%        5%"
    },
    {
      "fact_id": "FACT:d33448e3ea85555329cf",
      "source_doc": "PG_10K_2026.pdf",
      "page_num": 83,
      "company_id": "COMP:PG",
      "predicate": "OPERATES_SEGMENT",
      "period": null,
      "value": "Skin Care",
      "snippet": "Skin Care (1)                                        4%        3%        4%"
    }
  ],
  "plan": {
    "steps": [
      {
        "output_var": "$members",
        "action": "traverse_relation",
        "relation_type": "OPERATES_SEGMENT",
        "direction": "out",
        "start_nodes": [
          "COMP:PG"
        ]
      }
    ]
  },
  "execution_trace": [
    {
      "action": "traverse_relation",
      "output_var": "$members",
      "rows": [
        {
          "node_id": "EXT:BEAUTY",
          "fact_ids": [
            "FACT:9186e4cd4be69901932b"
          ]
        },
        {
          "node_id": "EXT:GROOMING",
          "fact_ids": [
            "FACT:6d52b3df90a4fe52db22"
          ]
        },
        {
          "node_id": "EXT:HEALTH_CARE",
          "fact_ids": [
            "FACT:3706044ff2a543252120"
          ]
        },
        {
          "node_id": "EXT:FABRIC_HOME_CARE",
          "fact_ids": [
            "FACT:a199f6f20e58855c5589"
          ]
        },
        {
          "node_id": "EXT:BABY_FEMININE_FAMILY_CARE",
          "fact_ids": [
            "FACT:d6670f55e85fbb28251e"
          ]
        },
        {
          "node_id": "EXT:FABRIC_CARE",
          "fact_ids": [
            "FACT:91bccfcc1597358700e0"
          ]
        },
        {
          "node_id": "EXT:HOME_CARE",
          "fact_ids": [
            "FACT:d848e6e01eb132dbaadd"
          ]
        },
        {
          "node_id": "EXT:BABY_CARE",
          "fact_ids": [
            "FACT:1f525e6d46e3a94f20ec"
          ]
        },
        {
          "node_id": "EXT:HAIR_CARE",
          "fact_ids": [
            "FACT:f5c4697dc486e4553404"
          ]
        },
        {
          "node_id": "EXT:FAMILY_CARE",
          "fact_ids": [
            "FACT:bf1e73d8dfc1ae4df2e9"
          ]
        },
        {
          "node_id": "EXT:ORAL_CARE",
          "fact_ids": [
            "FACT:f01f38d7a8a97d06812b"
          ]
        },
        {
          "node_id": "EXT:FEMININE_CARE",
          "fact_ids": [
            "FACT:9ea5c7e90799bc7ca93a"
          ]
        },
        {
          "node_id": "EXT:PERSONAL_HEALTH_CARE",
          "fact_ids": [
            "FACT:2d638a15c1f6819040b2"
          ]
        },
        {
          "node_id": "EXT:PERSONAL_CARE",
          "fact_ids": [
            "FACT:9506ba833420905c3b67"
          ]
        },
        {
          "node_id": "EXT:SKIN_CARE",
          "fact_ids": [
            "FACT:d33448e3ea85555329cf"
          ]
        }
      ],
      "fact_ids": [
        "FACT:1f525e6d46e3a94f20ec",
        "FACT:2d638a15c1f6819040b2",
        "FACT:3706044ff2a543252120",
        "FACT:6d52b3df90a4fe52db22",
        "FACT:9186e4cd4be69901932b",
        "FACT:91bccfcc1597358700e0",
        "FACT:9506ba833420905c3b67",
        "FACT:9ea5c7e90799bc7ca93a",
        "FACT:a199f6f20e58855c5589",
        "FACT:bf1e73d8dfc1ae4df2e9",
        "FACT:d33448e3ea85555329cf",
        "FACT:d6670f55e85fbb28251e",
        "FACT:d848e6e01eb132dbaadd",
        "FACT:f01f38d7a8a97d06812b",
        "FACT:f5c4697dc486e4553404"
      ]
    }
  ]
}
```

## Run metadata

Benchmark: `/Users/akarshjain/Desktop/genloop-th-assignment/benchmark/questions.json`
Questions: **30**
Frozen extraction digest: `d1cd573dffd1ad457748f377d98b45c160710ccb807ee9f2e89f7da6b2c4010e`
Benchmark SHA-256: `10c2422456a5efdb3b29cb6844e0a04daefde3a308f778cc9770d143e5454add`
Methodology: exact-page strict primary scoring; separate page +/- 1 diagnostic with relation-target matching.

## Design scope and future improvements

- **Graph completeness:** missing relations do not establish absence. Counts/rankings are over recorded graph evidence; future work needs extraction coverage and completeness certificates before exhaustive claims.
- **Historical audit scope:** auditor metadata is filing-level, without effective-period/audit-period modeling. Historical-year metrics do not independently prove that year's auditor. Add temporal relation scope before historical auditor comparisons.
- **Comparability:** revenue/debt definitions and CAPEX scope differ across issuers. Positive analytical CAPEX fixes signs, not definitions. Reported label differences are surfaced; future work needs definition/scope tags and comparison eligibility rules.
- **Entailment:** normalized quote matching proves original-page textual presence, not that a claimed relationship follows from the quote. Add human sampling, negative examples and semantic checks for live extraction.

## Interpretation

Strict primary fact matching requires exact document/page/company/predicate/period and preserves the original scoring definition (it does not compare expected_value). The separate page +/- 1 diagnostic relaxes only page distance for metrics; relation claims must additionally match the normalized gold expected_value against the retrieved target/value, including on the same page. The diagnostic never replaces primary scoring and can be lower when unrelated same-page relation targets would otherwise match. Duplicate retrieved facts consume precision denominator slots and cannot reuse a gold match. Empty retrieved/gold denominators score zero. Numeric tolerance is 1% relative (1e-12 absolute near zero); ratio/percent conversion requires explicit units. Unordered entity lists use sets; ranking questions preserve order. Entity answers normalize EXT IDs, punctuation and US postal state abbreviations.

Fallback guards cover recognized unsupported constraints and unresolved named qualifiers, not every possible modifier. Offline cache misses use deterministic planning; live failures remain closed unless PLANNER_ALLOW_LIVE_FALLBACK is explicitly enabled. Every prediction records its planner_source. Ingestion audits expose missing coverage and unavailable balance identities rather than inventing values. Run metadata identifies the benchmark, question count and active frozen-rule digest. Query-engine revisions do not change extraction.
