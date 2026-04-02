🏀 NBA Playoff Prediction Tournament

A live, interactive NBA Playoff bracket application built with Streamlit and nba_api. This app allows users to predict tournament outcomes, tracks live scores automatically, and maintains a competitive leaderboard.

### Key Features
* **Dynamic Bracketing**: Interactive UI for entering series predictions (4-win series and single-game Play-In).
* **Automated Results**: Integrates with `nba_api` to fetch live series standings and Play-In scores.
* **Winner Propagation**: Logic-driven advancement; updating a series score automatically pushes the winner to the next round (and resets it if the score is cleared).
* **Leaderboard**: Automated scoring based on correct team picks and perfect series score matches.
* **Admin Controls**: A password-protected sidebar to adjust point values and tournament dates without touching the code.
* **Persistent Storage**: Saves user predictions and admin settings as JSON files for continuity across sessions.

### Project Structure
* `app.py`: The main Streamlit interface. Handles the visual layout, user authentication, and the "Spectator" view for comparing brackets.
* `bracket_logic.py`: The engine of the app. Contains the API fetching logic, scoring algorithms, and the `TBD` propagation state machine.
* `logos/`: A directory containing NBA team logos (`.svg`) named by team abbreviation (e.g., `BOS.svg`).
* `data/`: Storage for user predictions and tournament configuration.

### Quick Start
1. Install dependencies:
    ```Bash
    pip install streamlit pandas nba_api
    ```
2. Setup Secrets: Create a `.streamlit/secrets.toml` file with your `ADMIN_PASSWORD` and `USER_PASSWORD`.
3. Run the App:
    ```Bash
    streamlit run app.py
    ```