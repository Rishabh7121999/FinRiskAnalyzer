                         USER
                          │
                          ▼
                   ┌────────────┐
                   │Query Agent │
                   └─────┬──────┘
                         │
                  Understand intent
                         │
                         ▼
                    ┌─────────┐
                    │ Planner │
                    └────┬────┘
                         │
                  Decide required
                     specialist work
                         │
                         ▼
                Entity Resolution
                         │
                         ▼
                   Dynamic Fan-Out
              ┌──────────┼──────────┐
              ▼          ▼          ▼
          Financial     News     Research
             Agent      Agent      Agent
              │          │          │
              └──────────┼──────────┘
                         ▼
                    Aggregator
                         │
                         ▼
                  Intent Router
                         │
          ┌──────────────┼──────────────┐
          ▼              ▼              ▼
     Investment      Comparison     Company Info
       Analysis       Analysis
          │              │
          └──────────────┼──────────────┘
                         ▼
                    Risk Agent
                    (if needed)
                         │
                         ▼
                  Verification
                         │
                         ▼
                    Governance
                         │
                         ▼
                 Report Generator
                         │
                         ▼
                        END

