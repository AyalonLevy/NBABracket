import json
import os

def create_dummies():
    if not os.path.exists("data"):
        os.makedirs("data")
        
    # Dummy Brother 1: Very accurate
    brother_1 = {
        "W_R1_1v8": ["OKC", "LAL", 4, 2],
        "W_R1_4v5": ["DEN", "MIN", 4, 3],
        "NBA_Finals": ["BOS", "OKC", 4, 2]
    }
    
    # Dummy Brother 2: Nailed the rhythm (Rule 3c) but wrong teams
    brother_2 = {
        "W_R1_1v8": ["GSW", "OKC", 4, 3], # Predicted 7 games
        "W_R1_4v5": ["MIN", "DEN", 4, 1],
    }

    with open("data/Brother_1_bracket.json", "w") as f: json.dump(brother_1, f)
    with open("data/Brother_2_bracket.json", "w") as f: json.dump(brother_2, f)
    
    print("Dummy data created in /data/")

create_dummies()