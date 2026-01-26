from typing import List, Dict, Any, Union, Tuple
from datetime import datetime, timedelta
import re

def date_to_label(date_str: Union[str, datetime], is_annual: bool = False) -> str:
    """Convert date string (2025-09-30) to display label."""
    try:
        if isinstance(date_str, str):
            # Handle different date formats
            if re.match(r'^\d{4}$', date_str):
                return date_str  # Already just a year
            date = datetime.strptime(date_str, "%Y-%m-%d")
        else:
            date = date_str
        
        # Fiscal Year Handling: 
        # If a period ends at the beginning of a month (e.g. Oct 2), 
        # it typically belongs to the PREVIOUS quarter/month.
        if date.day <= 7:
            date -= timedelta(days=7)
        
        if is_annual:
            return str(date.year)
        
        # For quarterly, return 2025Q3 format
        month = date.month
        if month <= 3:
            quarter = "Q1"
        elif month <= 6:
            quarter = "Q2"
        elif month <= 9:
            quarter = "Q3"
        else:
            quarter = "Q4"
        
        return f"{date.year}{quarter}"
    except Exception as e:
        print(f"[WARN] date_to_label failed: {e}")
        return str(date_str)


def parse_period_sort_key(period_str: str) -> Tuple[int, int]:
    """
    Helper to parse period string into (year, quarter) tuple for sorting.
    "2025" -> (2025, 4) (Assumes annual represents full year end for sorting)
    "2025Q3" -> (2025, 3)
    """
    try:
        if not isinstance(period_str, str):
            return (0, 0)
            
        m_q = re.match(r'^(\d{4})Q(\d)$', period_str)
        if m_q:
            return int(m_q.group(1)), int(m_q.group(2))
        
        m_y = re.match(r'^(\d{4})$', period_str)
        if m_y:
            return int(m_y.group(1)), 4 
            
        return (0, 0)
    except:
        return (0, 0)


def calculate_yoy(values: Dict[str, Any], periods: List[str]) -> Dict[str, Dict[str, Any]]:
    """Calculate YoY % change for each period."""
    result = {}
    # Robust sorting using numeric tuple key
    sorted_periods = sorted(periods, key=parse_period_sort_key, reverse=True)  # Most recent first
    
    # helper to parse period string
    def parse_period(p_str):
        # returns (year, quarter) or (year, None)
        # format: "2024" or "2024Q3"
        m_q = re.match(r'^(\d{4})Q(\d)$', p_str)
        if m_q:
            return int(m_q.group(1)), int(m_q.group(2))
        
        m_y = re.match(r'^(\d{4})$', p_str)
        if m_y:
            return int(m_y.group(1)), None
        return None, None

    for period in sorted_periods:
        current_data = values.get(period, {})
        val = current_data.get("value") if isinstance(current_data, dict) else current_data
        
        yoy = None
        
        if val is not None:
            year, quarter = parse_period(period)
            if year:
                prev_period_str = ""
                if quarter:
                    prev_period_str = f"{year-1}Q{quarter}"
                else:
                    prev_period_str = str(year-1)
                
                prev_data = values.get(prev_period_str, {})
                prev_val = prev_data.get("value") if isinstance(prev_data, dict) else prev_data
                
                if prev_val is not None and prev_val != 0:
                     yoy = round((val - prev_val) / abs(prev_val) * 100, 2)

        result[period] = {
            "value": val,
            "yoy": yoy
        }
    
    return result


def merge_fundamentals_data(all_data: List[List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    """
    Merge multiple lists of rows (from different filings) into one.
    Uses 'concept' (XBRL tag) as the primary key if available to handle label changes.
    Prioritizes labels from newer filings.
    """
    # Key can be concept (if valid) or label (fallback)
    # merged_map: key -> { 'label': ..., 'concept': ..., 'values': { period: {value: ...} } }
    merged_map = {} 
    
    # Iterate chunks in REVERSE order (Oldest -> Newest)
    # This ensures that the Latest filing (which comes last in this loop) overwrites older data
    # AND updates the label to the newest version.
    for chunk in reversed(all_data):
        for row in chunk:
            concept = row.get('concept')
            label = row['label']
            
            # Determine unique key: Prefer concept if it's a standard gaap/ifrs tag
            # Some concepts are 'us-gaap_Revenue...' which is good.
            # Avoid using 'concept' if it's None or generic for custom rows (rare in standard view)
            if concept and isinstance(concept, str) and (concept.startswith('us-gaap') or concept.startswith('ifrs')):
                key = concept
            else:
                key = label  # Fallback to label merging
            
            if key not in merged_map:
                merged_map[key] = {
                    'label': label, 
                    'concept': concept,
                    'values': {}
                }
            else:
                # Update label to the newer one (since we iterate Old -> New)
                merged_map[key]['label'] = label
                # Update concept if previously missing (unlikely but safe)
                if concept:
                    merged_map[key]['concept'] = concept
            
            # Merge values (Newer overwrites Older)
            merged_map[key]['values'].update(row['values'])
            
    # Convert back to list
    return list(merged_map.values())


def cache_to_response_format(cached_stmt_data: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Convert cached data {period: {label: value_obj}} back to response format.
    """
    if not cached_stmt_data:
        return []
    
    # Map label -> {period: value_obj, 'concept': ...}
    label_map = {}
    
    for period, content in cached_stmt_data.items():
        if not isinstance(content, dict):
            continue
        for label, val_obj in content.items():
            if label not in label_map:
                label_map[label] = {'values': {}}
            
            # Restore concept if present in the cached value object
            if isinstance(val_obj, dict) and 'concept' in val_obj:
                label_map[label]['concept'] = val_obj['concept']
                # Remove concept from the value/yoy dict to keep it clean (optional, but good for frontend)
                # But wait, keeping it in values might be harmless. Let's just create a clean copy for values.
                clean_val = val_obj.copy()
                del clean_val['concept']
                label_map[label]['values'][period] = clean_val
            else:
                label_map[label]['values'][period] = val_obj
            
    # Convert to list
    result = []
    for label, item in label_map.items():
        row = {
            "label": label,
            "values": item['values']
        }
        if 'concept' in item:
            row['concept'] = item['concept']
        result.append(row)
        
    return result
