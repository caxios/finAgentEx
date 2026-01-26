---
name: SEC EDGAR Financial Data Backend Logic Optimization
description: This skill covers advanced backend techniques for parsing, validating, and aggregating SEC EDGAR financial data with a strong focus on **data integrity**, **time-period correctness**, and **production-grade robustness**.  
It emphasizes preventing common financial data pitfalls such as cumulative-vs-discrete overwrites, incorrect quarter labeling, and unreliable YoY calculations—**without modifying frontend contracts**.
---


## 1. Role & Context

You are a **Python backend engineer** and **SEC EDGAR data processing specialist**.

You are fully familiar with the following documents located in the `multi_fundamentals` directory:

- bussiness_overview_datasource.md  
- company_facts.md  
- company_group_test.md  
- filing.md  
- filings.md  
- multi_year_findata.md  
- xbrls.md  

Your mission is to solve the business requirements below **by modifying only `fundamentals.py` and related backend logic**.  
**No frontend code or response schema may be changed.**

---

## 2. Key Objectives

### A. Time Horizon Expansion

#### Single Ticker
- Retrieve both **Annual** and **Quarterly** data
- Cover **at least the most recent 5 years**

#### Portfolio / Batch Requests
- Support multiple tickers in parallel
- Return the same 5-year annual + quarterly coverage for each ticker

---

### B. Data Integrity (Core Requirement)

#### 1) Discrete Quarterly Data Enforcement

Quarterly data must represent **pure 3‑month performance only**.

**Problem**
- SEC 10-Q filings contain both:
  - Discrete 3‑month results
  - Year‑to‑Date (YTD) cumulative results
- Existing logic overwrites discrete data with cumulative values when `endDate` matches

**Solution**
- Validate reporting duration using `startDate` and `endDate`
- Accept only ~90‑day periods as true quarters

```python
from datetime import datetime

def is_discrete_quarter(start_date: datetime, end_date: datetime) -> bool:
    days = (end_date - start_date).days
    return 80 <= days <= 100
```

```python
# During DataFrame parsing
if not is_annual:
    if not is_discrete_quarter(row["start_date"], row["end_date"]):
        continue  # Filter out YTD data
```

---

#### 2) Accurate Quarter Labeling (date_to_label)

Some companies close fiscal quarters at the **beginning of a month**.

**Requirement**
- If a filing date falls within the first 7 days of a month,
  treat it as belonging to the **previous month’s quarter**.

**Example**
```
2024-10-02 → 2024Q4 ❌
2024-10-02 → 2024Q3 ✅
```

```python
from datetime import timedelta

if date.day <= 7:
    date = date - timedelta(days=7)
```

---

#### 3) YoY (Year-over-Year) Calculation

- YoY must be computed **only after** quarterly data has been cleaned
- Formula:
```
YoY = (Current Quarter - Same Quarter Last Year) / Last Year Quarter
```

---

## 3. Implementation Guidelines

### Step 1. Duration Validation During XBRL Parsing
- Reference `xbrls.md` and `filing.md`
- Enforce duration checks before storing quarterly values

---

### Step 2. date_to_label Buffer Logic
- Apply month-start buffering
- Ensure Apple, Walmart, retail companies map correctly to fiscal quarters

---

### Step 3. merge_fundamentals_data Conflict Resolution

❌ Do NOT use:
```python
dict.update()
```

✅ Required logic:
- Prefer **latest filing**
- If the same period (e.g., 2024Q3) conflicts:
  - Prefer the **shorter duration (3‑month)** record
  - Treat abnormally large differences as cumulative data

---

### Step 4. Ensure 5-Year Coverage

Increase filing fetch limits:

| Type | Minimum |
|---|---|
| Annual | 5 |
| Quarterly | 20 |

Adjust SEC API `count` / `limit` parameters accordingly.

---

## 4. Constraints

- ❌ No frontend changes
- ✅ FundamentalsResponse JSON schema must remain **100% identical**
- Allowed libraries:
  - pandas
  - asyncio
  - httpx
  - existing project dependencies only

---

## 5. Definition of Done

- 2024Q3 returns **only discrete 3‑month results**
- No YTD or cumulative overwrites
- YoY correctly computed as:
```
(2024Q3 - 2023Q3) / 2023Q3
```
- Continuous data coverage from **2020 → present**
- Correct quarter mapping for non‑standard fiscal calendars (Apple, Walmart, etc.)

---

## 6. Summary

This skill focuses on **trustworthy financial data pipelines**.

> In financial systems,  
> **correct time alignment matters more than clever calculations.**
