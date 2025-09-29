# Mission Control API Queries

This document contains the SQL queries used to populate the Mission Control dashboard.

### Queue Depth
```sql
-- queue depth
SELECT count(*) AS queue_depth FROM videogen.jobs WHERE status IN ('queued','processing');
```

### Renders Per Hour
```sql
-- renders per hour
SELECT count(*) AS renders_per_hour FROM videogen.jobs WHERE status='completed' AND completed_at >= now() - '1 hour'::interval;
```

### Hourly Cost
```sql
-- hourly cost
SELECT coalesce(sum(actual_cost_usd),0) AS hourly_cost FROM videogen.jobs WHERE completed_at >= now() - '1 hour'::interval;
```

### Success Rate (Last 24h)
```sql
-- success rate last 24h
SELECT 100.0 * sum(CASE WHEN status='completed' THEN 1 ELSE 0 END) / NULLIF(count(*),0) AS success_rate FROM videogen.jobs WHERE created_at >= now() - '24 hours'::interval;
```
