import os
import datetime
import pandas as pd
import streamlit as st
import bracket_logic as bl


# --- INITIAL SETUP ---
st.set_page_config(layout="wide", page_title="Levy Bros NBA Bracket")

# CSS to force wide layout and center elements
st.markdown("""
    <style>
    .block-container { max-width: 100%; padding: 2rem 1rem; }
    
    [data-testid="stHorizontalBlock"] { align-items: center; }
    .stButton button { display: block; margin: 0 auto; }
    [data-testid="stVerticalBlock"] > div { gap: 0.5rem; }

    /* Center text and headers in the Leaderboard Dataframe */
    div[data-testid="stDataFrame"] div[role="gridcell"] > div {
        justify-content: center !important;
        text-align: center !important;
    }
    div[data-testid="stDataFrame"] div[role="columnheader"] > div {
        justify-content: center !important;
    }
    [data-testid="stTable"] {
        margin: 0 auto;
        width: 100%;
    }
    [data-testid="stTable"] th, [data-testid="stTable"] td {
        text-align: center !important;
        vertical-align: middle !important;
    }
    
    /* Reduce horizontal gap between all columns */
    [data-testid="column"] {
        padding-left: 0.5rem !important;
        padding-right: 0.5rem !important;
    }
            
    /* Target the center column (NBA Finals) to pull adjacent columns inward */
    /* This makes the space between Conf Finals and Finals 'less big' */
    div[data-testid="column"]:nth-of-type(4) {
        margin-left: -50px !important;
        margin-right: -50px !important;
        z-index: 10; /* Ensures Finals stays on top if they overlap */
    }
    
    /* Vertical centering for the vs text */
    .vs-text {
        display: flex;
        align-items: center;
        justify-content: center;
        height: 100%;
        font-weight: bold;
        color: #888;
    }
    </style>
    """, unsafe_allow_html=True)

# --- SESSION STATE INITIALIZATION ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

# --- INITIALIZE STATE ---
if 'points_config' not in st.session_state:
    st.session_state.point_config = bl.load_settings()

if 'playin_dates' not in st.session_state:
    st.session_state.playin_dates = bl.DEFAULT_PLAYIN

if 'my_bracket' not in st.session_state:
    st.session_state.my_bracket = bl.reset_bracket()

if 'bracket_version' not in st.session_state:
    st.session_state.bracket_version = 0

def render_series_input(game_id, bracket, disabled=False, prefix=""):
    home, away, h_score, a_score = bracket.get(game_id, ["TBD", "TBD", 0, 0])
    
    version = st.session_state.get('bracket_version', 0)

    col_h_logo, col_h_score, col_vs, col_a_score, col_a_logo = st.columns([1, 1.2, 0.4, 1.2, 1], vertical_alignment="center")

    col_h_logo.image(f"logos/{home}.svg", width=50)

    new_h_score = col_h_score.number_input(
        "H",
        min_value=0,
        max_value=4,
        value=int(h_score),
        key=f"{prefix}h_{game_id}_v{version}",
        label_visibility="collapsed",
        disabled=disabled
    )

    col_vs.write(":")

    new_a_score = col_a_score.number_input(
        "A",
        min_value=0,
        max_value=4,
        value=int(a_score),
        key=f"{prefix}a_{game_id}_v{version}",
        label_visibility="collapsed",
        disabled=disabled
    )

    col_a_logo.image(f"logos/{away}.svg", width=50)

    if not disabled and (new_h_score != h_score or new_a_score != a_score):
        bracket[game_id][2] = new_h_score
        bracket[game_id][3] = new_a_score
        st.session_state.my_bracket = bl.propagate_all_winners(bracket)
        st.rerun()

    ## In case of future edits
    # # UI Box
    # with st.container():
    #     # Layout [Logo] [Score] vs [Score] [Logo]
    #     col_h_logo, col_h_score, col_vs, col_a_score, col_a_logo = st.columns([1, 1.2, 0.3, 1.2, 1], vertical_alignment="center")

    #     with col_h_logo:
    #       st.image(f"logos/{home}.svg", width=60)
        
    #     with col_h_score:
    #         new_h_score = st.number_input(
    #             "H",
    #             min_value=0,
    #             max_value=4,
    #             value=int(h_score),
    #             key=f"h_{game_id}",
    #             label_visibility="collapsed",
    #             disabled=disabled
    #         )
        
    #     with col_vs:
    #         st.write(":")
        
    #     with col_a_score:
    #         new_a_score = st.number_input(
    #             "A",
    #             min_value=0,
    #             max_value=4,
    #             value=int(a_score),
    #             key=f"a_{game_id}",
    #             label_visibility="collapsed",
    #             disabled=disabled
    #         )
        
    #     with col_a_logo:
    #         st.image(f"logos/{away}.svg", width=60)

    #     if not disabled:
    #         if new_h_score != h_score or new_a_score != a_score:
    #             # Update local data
    #             bracket[game_id][2] = new_h_score
    #             bracket[game_id][3] = new_a_score

    #             st.session_state.my_bracket = bl.propagate_all_winners(st.session_state.my_bracket)
    #             st.rerun()


def draw_bracket(bracket_data, disabled=False, prefix=""):
    col_w1, col_w2, col_wf, col_fin, col_ef, col_e2, col_e1 = st.columns([2, 2, 2, 3, 2, 2, 2])

    with col_w1:
        render_series_input("W_R1_1v8", bracket_data, disabled, prefix=prefix)
        st.markdown("<div style='height: 100px;'></div>", unsafe_allow_html=True)
        render_series_input("W_R1_4v5", bracket_data, disabled, prefix=prefix)
        st.markdown("<div style='height: 100px;'></div>", unsafe_allow_html=True)
        render_series_input("W_R1_3v6", bracket_data, disabled, prefix=prefix)
        st.markdown("<div style='height: 100px;'></div>", unsafe_allow_html=True)
        render_series_input("W_R1_2v7", bracket_data, disabled, prefix=prefix)

    with col_w2:
        render_series_input("W_R2_1v4", bracket_data, disabled, prefix=prefix)
        st.markdown("<div style='height: 250px;'></div>", unsafe_allow_html=True)
        render_series_input("W_R2_2v3", bracket_data, disabled, prefix=prefix)

    with col_wf:
        render_series_input("W_CF", bracket_data, disabled, prefix=prefix)

    with col_fin:
        with st.container(border=True):
            render_series_input("NBA_Finals", bracket_data, disabled, prefix=prefix)
        st.markdown("<div style='height: 250px;'></div>", unsafe_allow_html=True)
    
    with col_ef:
        render_series_input("E_CF", bracket_data, disabled, prefix=prefix)

    with col_e2:
        render_series_input("E_R2_1v4", bracket_data, disabled, prefix=prefix)
        st.markdown("<div style='height: 250px;'></div>", unsafe_allow_html=True)
        render_series_input("E_R2_2v3", bracket_data, disabled, prefix=prefix)

    with col_e1:
        render_series_input("E_R1_1v8", bracket_data, disabled, prefix=prefix)
        st.markdown("<div style='height: 100px;'></div>", unsafe_allow_html=True)
        render_series_input("E_R1_4v5", bracket_data, disabled, prefix=prefix)
        st.markdown("<div style='height: 100px;'></div>", unsafe_allow_html=True)
        render_series_input("E_R1_3v6", bracket_data, disabled, prefix=prefix)
        st.markdown("<div style='height: 100px;'></div>", unsafe_allow_html=True)
        render_series_input("E_R1_2v7", bracket_data, disabled, prefix=prefix)
    
    st.divider()

    # PLAY-IN SECTION
    with st.expander("Play-In Tournament", expanded=True):
        pi_col1, pi_col2, _, pi_col3, pi_col4 = st.columns(5)
        with pi_col1:
            render_series_input("PI_W_7v8", bracket_data, disabled, prefix=prefix)
            st.markdown("<div style='height: 50px;'></div>", unsafe_allow_html=True)
            render_series_input("PI_W_9v10", bracket_data, disabled, prefix=prefix)

        with pi_col2:
            render_series_input("PI_W_ELIM", bracket_data, disabled, prefix=prefix)

        with pi_col3:
            render_series_input("PI_E_ELIM", bracket_data, disabled, prefix=prefix)

        with pi_col4:
            render_series_input("PI_E_7v8", bracket_data, disabled, prefix=prefix)
            st.markdown("<div style='height: 50px;'></div>", unsafe_allow_html=True)
            render_series_input("PI_E_9v10", bracket_data, disabled, prefix=prefix)


# --- LOGIN PAGE ---
def login_page():
    st.markdown("<div style='height: 100px;'></div>", unsafe_allow_html=True)
    st.markdown("<h1 style='text-align: center;'>🏀 Levy Bros NBA Bracket</h1>", unsafe_allow_html=True)

    # Center the login box
    _, col, _ = st.columns([1, 1, 1])

    with col:
        with st.form("login_form"):
            name = st.text_input("Enter Your Name")
            entered_password = st.text_input("Enter Password", type="password")

            _, center_btn_col, _ = st.columns([1, 1, 1])
            with center_btn_col:
                submit = st.form_submit_button("Enter Bracket")

        if submit:
            if not name:
                st.error("Please enter your name.")
            elif entered_password != bl.USER_PASSWORD:
                st.error("Incorrect bracket password. Ask the admin for access!")
            else:
                st.session_state.user_name = name
                st.session_state.logged_in = True
                # Load existing prediction if they already started one
                existing_data = bl.load_prediction(name)
                if existing_data:
                    st.session_state.my_bracket = existing_data
                
                st.rerun()

if not st.session_state.logged_in:
    login_page()
else:
    with st.sidebar:
        st.write(f"Logged in as: **{st.session_state.user_name}**")
        if st.button("Logout"):
            st.session_state.logged_in = False
            # st.session_state.user_name = ""
            st.rerun()

        st.divider()

        st.header ("Admin Settings")
        password = st.text_input("Enter Admin Password", type="password")

        if password == st.secrets["ADMIN_PASSWORD"]:
            st.subheader("Adjust Rewards Points")
            st.session_state.point_config['correct_team'] = st.slider("Correct Team", 0, 5, 1)
            st.session_state.point_config['score_only'] = st.slider("Score Only", 0, 5, 2)
            st.session_state.point_config['perfect'] = st.slider("Perfect Match", 0, 10, 3)

            st.divider()
            
            st.subheader("Play-In Schedule")
            pi_val = (st.session_state.point_config['playin_dates'][0], 
                    st.session_state.point_config['playin_dates'][-1])
            pi_range = st.date_input("Play-In Dates", value=pi_val)

            p_start = st.date_input("Playoff Start Date",
                                    value=st.session_state.point_config['playoff_start'])

            if st.button("Save All Settings & Dates"):
                # Update session state with new dates
                st.session_state.point_config['playoff_start'] = p_start
                
                if isinstance(pi_range, tuple) and len(pi_range) == 2:
                    start, end = pi_range
                    new_pi_list = [start + datetime.timedelta(days=x) for x in range((end-start).days + 1)]
                    st.session_state.point_config['playin_dates'] = new_pi_list
                
                # Save to JSON
                bl.save_settings(st.session_state.point_config)
                bl.fetch_from_nba_api.clear() # Reset cache to use new dates
                st.success("Configuration saved to disk!")
    
    # st.title(f"NBA Playoff {datetime.datetime.now().year}")
    playoff_year = st.session_state.point_config['playoff_start'].year
    st.markdown(f"<h1 style='text-align: center;'>NBA Playoff {playoff_year}</h1>", unsafe_allow_html=True)
    if not bl.is_locked():
        
        draw_bracket(st.session_state.my_bracket, disabled=False)

        st.markdown("<div style='height: 50px;'></div>", unsafe_allow_html=True)
        _, center_btn_col, _ = st.columns([1, 1, 1])
        with center_btn_col:
            col_save, col_reset = st.columns(2)
        
            with col_save:
                if st.button("Finalize & Save Bracket", width='stretch'):
                    st.session_state.my_bracket = bl.propagate_all_winners(st.session_state.my_bracket)
                    bl.save_prediction(st.session_state.user_name, st.session_state.my_bracket)
                    st.success("Bracket saved")
        
            with col_reset:
                # Use type="secondary" or leave default for a less 'loud' button
                if st.button("Reset Entire Bracket", use_container_width=True):
                    # Apply the reset
                    st.session_state.my_bracket = bl.reset_bracket()
                    st.session_state.bracket_version += 1
                    # Save the reset state so it persists
                    bl.save_prediction(st.session_state.user_name, st.session_state.my_bracket)
                    st.rerun()

    else:
        # 1. Load Actual Results (Actual scores)
        actual_data = bl.get_actual_results(st.session_state.playin_dates)

        if not actual_data:
            st.warning("Tournament hasn't started yet. Waiting for NBA API to populate scores...")

        draw_bracket(actual_data, disabled=True, prefix="official_")

        st.divider()

        _, center_col, _ = st.columns([1.5, 1, 1.5])
        with center_col:
            st.markdown("<h3 style='text-align: center;'>🏆 Leaderboard</h3>", unsafe_allow_html=True)

            if not os.path.exists("data/"):
                os.makedirs("data/")

            user_files = [f for f in os.listdir("data/") if f.endswith("_bracket.json")]
            leaderboard = []

            all_predictions = {}

            for file in user_files:
                uname = file.replace("_bracket.json", "")

                if uname == "actual_results":
                    continue

                upred = bl.load_prediction(uname)
                all_predictions[uname] = upred

                # Calculate score
                total_pts = 0
                for game_id, act_list in actual_data.items():
                    if game_id in upred:
                        pred_list = upred[game_id]

                        score_limit = 1 if "PI_" in game_id else 4
                        if (pred_list[2] < score_limit and pred_list[3] < score_limit) or (act_list[2] < score_limit and act_list[3] < score_limit):
                            continue
                        
                        total_pts += bl.calculate_score(pred_list, act_list, st.session_state.point_config)
                
                leaderboard.append(({"Name": uname, "Points": total_pts}))

            # Show Leaderboard Table
            if leaderboard:
                df = pd.DataFrame(leaderboard).sort_values("Points", ascending=False)
                st.table(df, hide_index=True)
            else:
                st.info("No prediction found yet.")
        
        st.divider()

        with st.expander("Inspect other predictions", expanded=False):
            st.markdown("<h3 style='text-align: center;'> Inspect Predictions</h3>", unsafe_allow_html=True)

            viewer_names = list(all_predictions.keys())
            selected_user = st.selectbox("Whose bracket do you want to see?", viewer_names)

            if selected_user:
                st.markdown(f"<h4 style='text-align: center;'>{selected_user}'s Prediction</h4>", unsafe_allow_html=True)
                draw_bracket(all_predictions[selected_user], disabled=True, prefix=f"{selected_user}_")

