import json
import datetime
import pandas as pd
import streamlit as st

from nba_api.stats.endpoints import leaguestandings, playoffpicture, scoreboardv2


USER_PASSWORD = st.secrets["USER_PASSWORD"]


## CHANGE THIS FOR UPDATING TO NEXT SEASON (TODO: ADD THIS TO THE SIDE PANEL)
DEFAULT_PLAYIN = [
    datetime.date(2026, 4, 14), 
    datetime.date(2026, 4, 15), 
    datetime.date(2026, 4, 16), 
    datetime.date(2026, 4, 17)
]

# --- MAPPING THE TOURNAMENT FLOW ---
BRACKET_MAP = {
    # Play-In -> Playoff Seeds
    "PI_W_7v8": {"winner_to": "W_R1_1v8", "slot": "away", "loser_to": "PI_W_ELIM", "loser_slot": "home"},
    "PI_W_9v10": {"winner_to": "PI_W_ELIM", "slot": "away"},
    "PI_W_ELIM": {"winner_to": "W_R1_2v7", "slot": "away"},

    "PI_E_7v8": {"winner_to": "E_R1_1v8", "slot": "away", "loser_to": "PI_E_ELIM", "loser_slot": "home"},
    "PI_E_9v10": {"winner_to": "PI_E_ELIM", "slot": "away"},
    "PI_E_ELIM": {"winner_to": "E_R1_2v7", "slot": "away"},

    # Playoff Round 1 -> Round 2
    "W_R1_1v8": {"winner_to": "W_R2_1v4", "slot": "home"},
    "W_R1_4v5": {"winner_to": "W_R2_1v4", "slot": "away"},
    "W_R1_2v7": {"winner_to": "W_R2_2v3", "slot": "home"},
    "W_R1_3v6": {"winner_to": "W_R2_2v3", "slot": "away"},

    "E_R1_1v8": {"winner_to": "E_R2_1v4", "slot": "home"},
    "E_R1_4v5": {"winner_to": "E_R2_1v4", "slot": "away"},
    "E_R1_2v7": {"winner_to": "E_R2_2v3", "slot": "home"},
    "E_R1_3v6": {"winner_to": "E_R2_2v3", "slot": "away"},

    # Playoff Round 2 -> Conferece Finals
    "W_R2_1v4": {"winner_to": "W_CF", "slot": "home"},
    "W_R2_2v3": {"winner_to": "W_CF", "slot": "away"},

    "E_R2_1v4": {"winner_to": "E_CF", "slot": "home"},
    "E_R2_2v3": {"winner_to": "E_CF", "slot": "away"},

    # Playeoff Conference Finals -> NBA Finals
    "W_CF": {"winner_to": "NBA_Finals", "slot": "home"},
    "E_CF": {"winner_to": "NBA_Finals", "slot": "away"}
}

TEAM_MAP = {
    "Thunder": "OKC", "Timberwolves": "MIN", "Nuggets": "DEN", "Clippers": "LAC",
    "Mavericks": "DAL", "Suns": "PHX", "Lakers": "LAL", "Pelicans": "NOP",
    "Kings": "SAC", "Warriors": "GSW", "Celtics": "BOS", "Knicks": "NYK",
    "Bucks": "MIL", "Cavaliers": "CLE", "Magic": "ORL", "Pacers": "IND", "Wizards": "WAS",
    "76ers": "PHI", "Heat": "MIA", "Bulls": "CHI", "Hawks": "ATL", "Nets": "BKN",
    "Rockets": "HOU", "Pistons": "DET", "Raptors": "TOR", "Spurs": "SAS",
    "Trail Blazers": "POR", "Grizzlies": "MEM", "Jazz": "UTA", "Hornets": "CHA",
}

TEAM_ID_MAP = {
    1610612760: "OKC",
    1610612759: "SAS",
    1610612747: "LAL",
    1610612743: "DEN",
    1610612745: "HOU",
    1610612750: "MIN",
    1610612756: "PHX",
    1610612746: "LAC",
    1610612757: "POR",
    1610612744: "GSW",
    1610612740: "NOP",
    1610612763: "MEM",
    1610612742: "DAL",
    1610612762: "UTA",
    1610612758: "SAC",
    1610612765: "DET",
    1610612738: "BOS",
    1610612752: "NYK",
    1610612739: "CLE",
    1610612737: "ATL",
    1610612755: "PHI",
    1610612761: "TOR",
    1610612766: "CHA",
    1610612753: "ORL",
    1610612748: "MIA",
    1610612749: "MIL",
    1610612741: "CHI",
    1610612754: "IND",
    1610612751: "BKN",
    1610612764: "WAS"
}

@st.cache_data(ttl=3600)
def get_nba_seeds():
    try:
        """ Fetch current 1-10 seeds for East and West """
        data = leaguestandings.LeagueStandings().get_data_frames()[0]

        def extract_conf(name):
            conf_df = data[data['Conference'] == name].sort_values('PlayoffRank')

            seeds = {}
            for _, row in conf_df.iterrows():
                rank = int(row['PlayoffRank'])
                full_name = row['TeamName']
                seeds[rank] = TEAM_MAP.get(full_name, "TBD")
            
            return seeds
        
        return {"Western": extract_conf("West"), "Eastern": extract_conf("East")}
    except Exception as e:
        st.error(f"NBA API Error: {e}")
        return {"Western": {i: "TBD" for i in range (1, 11)}, "Eastern": {i: "TBD" for i in range (1, 11)}}

def calculate_score(pred, act, config):
    """
    pred_list/act_list format: [HomeTeam, AwayTeam, HomeScore, AwayScore]
    """
    
    p_win = pred[0] if pred[2] > pred[3] else pred[1]
    a_win = act[0] if act[2] > act[3] else act[1]

    score_match = (pred[2] == act[2] and pred[3] == act[3])

    if p_win == a_win:
        return config['perfect'] if score_match else config['correct_team']

    return config['score_only'] if score_match else 0

def propagate_all_winners(bracket):
    changed = True
    while changed:
        changed = False
        for game_id, mapping in BRACKET_MAP.items():
            home, away, h_score, a_score = bracket.get(game_id, ["TBD", "TBD", 0, 0])
            
            limit = 1 if "PI_" in game_id else 4
            
            target_w = mapping["winner_to"]
            slot_w = 0 if mapping["slot"] == "home" else 1

            if h_score == limit or a_score == limit:
                winner = home if h_score > a_score else away
                loser = away if h_score > a_score else home

                if bracket[target_w][slot_w] != winner:
                    bracket[target_w][slot_w] = winner
                    changed = True

                if "loser_to" in mapping:
                    target_l = mapping["loser_to"]
                    slot_l = 0 if mapping["loser_slot"] == "home" else 1
                    if bracket[target_l][slot_l] != loser:
                        bracket[target_l][slot_l] = loser
                        changed = True
            
            else:
                if bracket[target_w][slot_w] != "TBD":
                    bracket[target_w][slot_w] = "TBD"
                    changed = True

                if "loser_to" in mapping:
                    target_l = mapping["loser_to"]
                    slot_l = 0 if mapping["loser_slot"] == "home" else 1
                    if bracket[target_l][slot_l] != "TBD":
                        bracket[target_l][slot_l] = "TBD"
                        changed = True

    
    return bracket

def get_actual_playin_data(date_str):
    """
    Fetches single-game results for Play-In games.
    Returns a dict: { 'PI_W_7v8': [home_id, away_id, home_score, away_score] }
    """
    try:
        sb = scoreboardv2.ScoreboardV2(game_date=date_str)
        df = sb.get_data_frames()[1]

        results = {}
        for i in range(0, len(df), 2):
            team1 = df.iloc[i]
            team2 = df.iloc[i + 1]

            game_id = find_game_key_by_ids(team1['TEAM_ID'], team2['TEAM_ID'], is_playin=True)
            
            if game_id:
                team1_pts = int(team1['PTS'] or 0)
                team2_pts = int(team2['PTS'] or 0)

                h_abbr = st.session_state.my_bracket[game_id][0]
                team1_abbr = TEAM_ID_MAP.get(team1['TEAM_ID'], "TBD")
                team2_abbr = TEAM_ID_MAP.get(team2['TEAM_ID'], "TBD")

                if team1_abbr == h_abbr:
                    results[game_id] = [h_abbr, team2_abbr, 1 if team1_pts > team2_pts else 0, 0 if team1_pts > team2_pts else 1]
                else:
                    results[game_id] = [team2_abbr, h_abbr, 1 if team2_pts > team1_pts else 0, 0 if team2_pts > team1_pts else 1]

        return results
    except Exception as e:
        st.error(f"Issue with retrieving data: {e}")
        return {}

def get_actual_playoff_data():
    """
    Fetches current 4-win series status (e.g. 2-1).
    """
    try:
        data = playoffpicture.PlayoffPicture(league_id='00').get_data_frames()
        # Combine East (0) and West (2) tables
        df = pd.concat([data[0], data[2]])
        
        results = {}
        for _, row in df.iterrows():
            high_id = row['HIGH_SEED_TEAM_ID']
            low_id = row['LOW_SEED_TEAM_ID']
            
            game_id = find_game_key_by_ids(high_id, low_id, is_playin=False)
            
            if game_id:
                # We trust the High Seed wins vs Low Seed wins columns
                high_wins = int(row['HIGH_SEED_SERIES_W'] or 0)
                low_wins = int(row['HIGH_SEED_SERIES_L'] or 0)
                
                # In your Round 1/2 mapping, High Seed is always the Home (index 0) slot
                results[game_id] = [TEAM_ID_MAP.get(high_id, "TBD"), TEAM_ID_MAP.get(low_id, "TBD"), high_wins, low_wins]
                
        return results
    except Exception as e:
        st.error(f"Playoff API Error: {e}")
        return {}

@st.cache_data(ttl=3600)
def fetch_from_nba_api(dates_to_check):
    results = {}
    
    for date in dates_to_check:
        date_str = date.strftime('%Y-%m-%d')
        day_results = get_actual_playin_data(date_str)
        if day_results:
            results.update(day_results)
    
    playoff_data = get_actual_playoff_data()
    if playoff_data:
        results.update(playoff_data)
    
    if results:
        save_prediction("actual_results", results)

    return results 

def get_actual_results(playin_dates, force_local=False):
    if force_local:
        return load_prediction("actual_results")

    results = fetch_from_nba_api(playin_dates)

    if not results:
        return load_prediction("actual_results")

    return results

def find_game_key_by_teams(team_a, team_b):
    """
    Looks through st.session_state.my_bracket to find which game 
    matches these two teams.
    """
    for game_id, teams in st.session_state.my_bracket.items():
        if team_a in teams[:2] and team_b in teams[:2]:
            return game_id
    return None

def find_game_key_by_ids(id_1, id_2, is_playin=False):
    """
    Searches your bracket for the game containing these two teams.
    """
    abbr_1 = TEAM_ID_MAP.get(id_1, "TBD")
    abbr_2 = TEAM_ID_MAP.get(id_2, "TBD")


    for game_id, data in st.session_state.my_bracket.items():
        if is_playin and "PI_" not in game_id:
            continue
            
        if not is_playin and "PI_" in game_id:
            continue

        if abbr_1 == "TBD" or abbr_2 == "TBD":
            continue

        if abbr_1 in data[:2] and abbr_2 in data[:2]:
            return game_id
    
    return None


def map_nba_id_to_key(series_id):
    """
    NBA Series ID Structure (Example 0042500111)
    004: NBA
    25: Year (2025-26 season)
    0: Season Type
    01: Round (01=R1, 02=Semis, 03=Finals, 04=NBA Finals)
    1: Conference (1=East, 2=West)
    1: Matchup Number
    """
    if not series_id or len(series_id) < 10:
        return None
    
    round_num = series_id[6:8]
    conf_id = series_id[8]
    matchup = series_id[9]
    conf_prefix = "E" if conf_id == "1" else "W"

    mapping = {
        "01": {
            "1": f"{conf_prefix}_R1_1v8",
            "2": f"{conf_prefix}_R1_4v5",
            "3": f"{conf_prefix}_R1_3v6",
            "4": f"{conf_prefix}_R1_2v7"
        },
        "02": {
            "1": f"{conf_prefix}_R2_1v4",
            "2": f"{conf_prefix}_R2_2v3"
        },
        "03": {
            "1": f"{conf_prefix}_CF"
        },
        "04": {
            "1": "NBA_Finals"
        }
    }
    
    return mapping.get(round_num, {}).get(matchup)

def get_todays_test_scores():
    try:
        today = "2026-03-01"
        sb = scoreboardv2.ScoreboardV2(game_date=today)
        line_score = sb.get_data_frames()[1]

        games = []
        for i in range(0, len(line_score), 2):
            team1 = line_score.iloc[i]
            team2 = line_score.iloc[i + 1]

            t1_name = TEAM_MAP.get(team1['TEAM_NAME'], team1['TEAM_NAME'])
            t2_name = TEAM_MAP.get(team2['TEAM_NAME'], team2['TEAM_NAME'])

            t1_pts = team1['PTS'] if team1['PTS'] is not None else "0"
            t2_pts = team2['PTS'] if team2['PTS'] is not None else "0"

            games.append(f"{t1_name} {int(t1_pts)} - {int(t2_pts)} {t2_name}")
            
        return games
    except Exception as e:
        return [f"Error fetching scores: {e}"]

def reset_bracket():
    seeds = get_nba_seeds()
    w = seeds["Western"]
    e = seeds["Eastern"]
    
    fresh = {
        # WEST PLAY-IN
        "PI_W_7v8": [w.get(7, "TBD"), w.get(8, "TBD"), 0, 0],
        "PI_W_9v10": [w.get(9, "TBD"), w.get(10, "TBD"), 0, 0],
        "PI_W_ELIM": ["TBD", "TBD", 0, 0],

        # EAST PLAY-IN
        "PI_E_7v8": [e.get(7, "TBD"), e.get(8, "TBD"), 0, 0],
        "PI_E_9v10": [e.get(9, "TBD"), e.get(10, "TBD"), 0, 0],
        "PI_E_ELIM": ["TBD", "TBD", 0, 0],

        # WEST ROUND 1
        "W_R1_1v8": [w.get(1, "TBD"), "TBD", 0, 0],
        "W_R1_4v5": [w.get(4, "TBD"), w.get(5, "TBD"), 0, 0],
        "W_R1_3v6": [w.get(3, "TBD"), w.get(6, "TBD"), 0, 0],
        "W_R1_2v7": [w.get(2, "TBD"), "TBD", 0, 0],

        # EAST ROUND 1
        "E_R1_1v8": [e.get(1, "TBD"), "TBD", 0, 0],
        "E_R1_4v5": [e.get(4, "TBD"), e.get(5, "TBD"), 0, 0],
        "E_R1_3v6": [e.get(3, "TBD"), e.get(6, "TBD"), 0, 0],
        "E_R1_2v7": [e.get(2, "TBD"), "TBD", 0, 0],

        # WEST ROUND 2
        "W_R2_1v4": ["TBD", "TBD", 0, 0],
        "W_R2_2v3": ["TBD", "TBD", 0, 0],

        # EAST ROUND 2
        "E_R2_1v4": ["TBD", "TBD", 0, 0],
        "E_R2_2v3": ["TBD", "TBD", 0, 0],

        # CONFERENCE FINALS
        "W_CF": ["TBD", "TBD", 0, 0],
        "E_CF": ["TBD", "TBD", 0, 0],

        # FINALS
        "NBA_Finals": ["TBD", "TBD", 0, 0],
    }
    
    return fresh

# --- CONFIG ---
LOCK_DATE = datetime.datetime(2026, 4, 14, 19, 0, 0)

def is_locked():
    # return True  # FOR DEBUGGING
    settings = load_settings()
    lock_date = datetime.datetime.combine(settings['playoff_start'], datetime.time(19, 0))
    return datetime.datetime.now() > lock_date

def save_prediction(user_name, data):
    with open(f"data/{user_name}_bracket.json", "w") as f:
        json.dump(data, f)

def load_prediction(user_name):
    try:
        with open(f"data/{user_name}_bracket.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_settings(settings):
    serializable_settings = settings.copy()
    if 'playoff_start' in settings:
        serializable_settings['playoff_start'] = settings['playoff_start'].isoformat()
    if 'playin_dates' in settings:
        serializable_settings['playin_dates'] = [d.isoformat() for d in settings['playin_dates']]
    
    with open("data/settings.json", "w") as f:
        json.dump(serializable_settings, f)

def load_settings():
    try:
        with open("data/settings.json", "r") as f:
            data = json.load(f)
            # Convert strings back to date objects
            if 'playoff_start' in data:
                data['playoff_start'] = datetime.date.fromisoformat(data['playoff_start'])
            if 'playin_dates' in data:
                data['playin_dates'] = [datetime.date.fromisoformat(d) for d in data['playin_dates']]
            return data
    except:
        # Default 2026 Fallback
        return {
            "correct_team": 1, "score_only": 2, "perfect": 3,
            "playoff_start": datetime.date(2026, 4, 18),
            "playin_dates": [datetime.date(2026, 4, 14), datetime.date(2026, 4, 17)]
        }
