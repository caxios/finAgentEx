# SKILL.md: Portfolio News Dashboard Implementation

## 🎯 Project Objective
Collect the latest news for all tickers included in the portfolio and implement a visually structured **Card-style Dashboard UI**. Specifically, apply a **Ticker Badge System** to intuitively identify which stock each news article is associated with.

---

## 🛠 1. Backend: Data Aggregation & Tagging

### 1.1 Multi-Ticker News Fetching
- [ ] **Iterative Search Strategy**:
    - Iterate through the `portfolio_list` to fetch news for each `ticker`.
    - Search Query Examples: `"{ticker} stock news"`, `"{ticker} earnings analysis"`

- [ ] **Source Tagging Logic (Critical)**:
    - Ensure a `related_tickers` field is added to the collected news object (Dictionary) as a **List**.
    - **Why List?**: A single news article may relate to multiple tickers (e.g., competitor comparisons, sector-wide issues), so it must be managed as a list rather than a single string. (e.g., `["AAPL", "INTC"]`)
    - *Logic:*
        1. Add the ticker used for the search by default.
        2. (Advanced) If the symbol of another stock in the portfolio appears in the news title or body, append that symbol to the `related_tickers` list.

### 1.2 Data Normalization (JSON Structure)
Collected news must be delivered to the frontend in a standardized JSON format as shown below:

```json
{
  "id": "news_unique_id_001",
  "title": "Intel Stock Surges to 4-Year High Ahead of Earnings",
  "published_date": "2026-01-22",
  "source": "MarketWatch",
  "summary": "Intel stock gained again on Wednesday ahead of the chip company's earnings report...",
  "url": "https://...",
  "related_tickers": ["AAPL", "INTC"]
}
```

---

## 🎨 2. Frontend: UI/UX Implementation
Construct components based on the reference image.

### 2.1 Control Bar (Top Header)
- [ ] **Filters**:
    - Date Picker: Dropdown for filtering by date.
    - Category: Select news category (All Categories, Earnings, M&A, etc.).
    - Ticker Filter: Functionality to filter news for a specific stock.

- [ ] **Action**:
    - Refresh Button: A refresh button styled in blue (`btn-primary`).

### 2.2 News Card Component (Core UI)
Each news item is rendered as an individual card (`div` or `article` tag) with the following hierarchy:

- [ ] **Card Header (Title)**:
    - Display the news title in **bold** font with blue link text.
    - Open the original article in a new tab upon clicking (`target="_blank"`).

- [ ] **Meta Info Row (Date & Badges)**:
    - Place the date and ticker badges in a single row immediately below the title.
    - Date: Display in `YYYY-MM-DD` format with gray text.
    - **Ticker Badges (Req-Spec)**:
        - Render by iterating through the `related_tickers` list data.
        - Style: Rounded pill-shaped chips.
        - Color: Bright blue background (`bg-blue-500`) with white text (`text-white`) or a Cyan/Blue gradient.
        - Layout: If there are multiple tickers, align them horizontally with a gap.
        - Example: `[ AMZN ] [ GOOG ] [ META ]`

- [ ] **Card Body (Content)**:
    - Display the news summary in grayscale text.
    - Apply an ellipsis (`...`) after 2–3 lines to maintain consistent card height.

---

## 🚀 3. Workflow Integration
**User Action**:
- User requests "Show portfolio news" or accesses the dashboard.

**System Action**:
1. Execute `fetch_portfolio_news()` → Collect news for each ticker.
2. Deduplicate collected news (based on URL or Title).
3. Merge `related_tickers` tags (if the same news is found in searches for multiple tickers, combine the ticker lists).

**Display**:
- Sort by date (Latest first / Descending).
- Map to the defined UI Components for rendering.
