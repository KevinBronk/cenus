from .fatigue import detect_fatigue


# Fake 8-day history
sample_data = [
    {"CTR": 1.5, "ROAS": 3.0, "CPM": 10, "CPC": 2.0, "Results": 20, "Frequency": 1.1},
    {"CTR": 1.6, "ROAS": 3.1, "CPM": 11, "CPC": 2.1, "Results": 21, "Frequency": 1.2},
    {"CTR": 1.7, "ROAS": 3.2, "CPM": 12, "CPC": 2.2, "Results": 19, "Frequency": 1.2},
    {"CTR": 1.5, "ROAS": 3.0, "CPM": 10, "CPC": 2.0, "Results": 20, "Frequency": 1.3},
    {"CTR": 1.6, "ROAS": 3.1, "CPM": 11, "CPC": 2.1, "Results": 19, "Frequency": 1.3},
    {"CTR": 1.4, "ROAS": 2.9, "CPM": 12, "CPC": 2.3, "Results": 18, "Frequency": 1.2},
    {"CTR": 1.5, "ROAS": 3.0, "CPM": 10, "CPC": 2.0, "Results": 20, "Frequency": 1.2},
    {"CTR": 0.9, "ROAS": 1.5, "CPM": 18, "CPC": 3.5, "Results": 10, "Frequency": 2.5},
]

if __name__ == "__main__":
    flag, reason, actions = detect_fatigue(sample_data)
    print("Fatigue Flag:", flag)
    print("Reason:", reason)
    print("Actions:", actions)
