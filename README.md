# Virtual Golf Betting Simulator

This is a full-stack Flask web application designed to simulate professional golf tournaments. It provides a platform for users to watch realistic, play-by-play tournament simulations and practice sports betting with virtual currency.

The core of the project is a sophisticated simulation engine that models a 4-round golf tournament with a high degree of realism.

## Key Features

- **Realistic Tournament Simulation:** The engine simulates tournaments on a play-by-play basis with a staggered start, where groups tee off sequentially.
- **Live Leaderboard:** A dynamic, auto-refreshing leaderboard provides a real-time view of the tournament as it unfolds, with color-coded scores and player statuses.
- **Multi-Round Tournaments:** The simulation supports full 4-round tournaments, with the ability to manually advance between rounds.
- **PGA-Style Cut:** After Round 2, a "cut" is automatically applied, with only the top 65 players (and ties) advancing to the final rounds.
- **Score-Based Re-Grouping:** For Rounds 3 and 4, players who make the cut are re-grouped based on their scores, with the leaders teeing off last.
- **Dynamic UI:** The frontend, built with Bootstrap and Jinja2, provides a clean and intuitive interface for viewing the tournament schedule and live leaderboard.

## Technology Stack

- **Backend:** Flask (Python)
- **Database:** SQLite
- **Frontend:** Jinja2, HTML, Bootstrap
- **Simulation:** Custom Python-based simulation engine

## Setup & Installation

To get the application running locally, follow these steps:

1.  **Clone the Repository**
    ```bash
    git clone <your-repository-url>
    cd golf_bet
    ```

2.  **Create and Activate a Virtual Environment**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure Environment Variables**
    This project uses a `.env` file for configuration. An example is provided.
    ```bash
    cp env_example.txt .env
    ```
    *You can edit the `.env` file if you need to change the default settings, but the defaults should work out-of-the-box.*

## How to Run the Application

A convenience script is provided to handle resetting the database and starting the application.

1.  **Make the script executable:**
    ```bash
    chmod +x reset_and_start.sh
    ```

2.  **Run the script:**
    ```bash
    ./reset_and_start.sh
    ```

This script will:
- 🗑️ Remove the old database file.
- 🌱 Seed the database with a fresh set of players, courses, and a 20-tournament season.
- 🚀 Start the Flask development server.

Once running, you can access the application at `http://127.0.0.1:5000` in your web browser. 