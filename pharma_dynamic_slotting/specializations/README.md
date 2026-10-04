# Specialization Python Modules

Each file represents a focused warehouse-operations specialization that can be imported independently or run through `run_specializations.py`.

| Module | Responsibility |
|---|---|
| `demand_analytics.py` | Pick frequency, units, active days, velocity, and ABC classification |
| `storage_safety.py` | Temperature/zone compatibility, blocked locations, capacity, and weight checks |
| `travel_analytics.py` | Distance, weighted picker travel, and baseline comparison |
| `replenishment_workload.py` | Worker-minute limits and location congestion limits |
| `governance.py` | Confidence labels, low-confidence review queue, and authorised override audit records |
| `operations_monitoring.py` | Release guardrails and pilot KPI checks |
| `run_specializations.py` | End-to-end demonstration over the generated project dataset |
| `core_engine/` | Copy of the main optimiser engine and CLI |

Run from the repository root:

```bash
python src/generate_data.py
python src/main.py
python specializations/run_specializations.py
python -m pytest -q
```

The modules are deliberately small and composable so they can be adapted to real extracts in VS Code. Production use still requires quality approval, validated temperature mapping, real aisle distances, and an auditable change-control workflow.
