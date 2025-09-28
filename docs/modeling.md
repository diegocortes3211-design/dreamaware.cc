---
id: modeling
title: Modeling Strategy
---

Stage 1 - fine tune with adapters where possible.
Use open weights when available.
Keep cost low and iterate fast.

Stage 2 - connect RAG and prompt chaining for domain tasks.
Use the ingestion index as primary context.

Stage 3 - pretrain a compact domain model once corpus size and budget justify it.

Zero slop gate
- All training text passes through a filter that strips emojis and fancy dashes.
- Keep logs to justify every transform.

Run locally
```
python scripts/train_model.py --epochs 1
```

Artifacts land in `artifacts/model`.