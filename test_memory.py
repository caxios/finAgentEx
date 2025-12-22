from modules.memory import store_event, retrieve_similar_events

print("Testing Memory Module...")
store_event("TEST", "Test Summary", "BUY", "Test Reasoning")
mems = retrieve_similar_events("Test Summary")
print(f"Retrieved {len(mems)} memories.")
print("Memory Test Complete.")
