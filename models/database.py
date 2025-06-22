import sqlite3
from config import Config
import sys
import os
from collections import defaultdict

# This ensures that any script running this file can find the 'config' module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class Database:
    """Handles all database operations."""

    def _get_connection(self):
        """Gets a new database connection."""
        conn = sqlite3.connect(Config.DATABASE_PATH)
        conn.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))
        return conn

    # --- User Functions ---
    def get_user(self, username):
        with self._get_connection() as conn:
            return conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()

    def create_user(self, username):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO users (username) VALUES (?)', (username,))
            conn.commit()
            return cursor.lastrowid

    def get_user_bets(self, user_id):
        with self._get_connection() as conn:
            return conn.execute('SELECT * FROM bets WHERE user_id = ? ORDER BY created_at DESC', (user_id,)).fetchall()

    # --- Tournament & Course Functions ---
    def get_all_tournaments(self):
        """Gets all available tournaments."""
        with self._get_connection() as conn:
            return conn.execute('''
                SELECT t.*, c.name as course_name
                FROM tournaments t
                JOIN courses c ON t.course_id = c.id
                ORDER BY t.start_date DESC
            ''').fetchall()

    def get_tournament_by_id(self, tournament_id):
        with self._get_connection() as conn:
            return conn.execute('SELECT * FROM tournaments WHERE id = ?', (tournament_id,)).fetchone()

    def get_active_tournament(self):
        """Gets the currently active tournament, if any."""
        with self._get_connection() as conn:
            return conn.execute("SELECT * FROM tournaments WHERE status = 'active'").fetchone()

    def start_tournament(self, tournament_id):
        """Sets a tournament to active and populates its player list."""
        with self._get_connection() as conn:
            # Check if there's already an active tournament
            active_tournament = conn.execute("SELECT id FROM tournaments WHERE status = 'active'").fetchone()
            if active_tournament:
                raise ValueError(f"Tournament {active_tournament['id']} is already active. Only one tournament can run at a time.")
            
            # 1. Set status to active and reset progress
            conn.execute("UPDATE tournaments SET status = 'active' WHERE id = ?", (tournament_id,))
            conn.execute("UPDATE tournaments SET simulation_step = 0 WHERE id = ?", (tournament_id,))
            conn.execute("UPDATE tournaments SET current_round = 1 WHERE id = ?", (tournament_id,))

            # 2. Populate tournament_players
            players = self.get_all_players() # Assumes you want all players in every tournament
            
            # Clear existing players for this tournament just in case
            conn.execute("DELETE FROM tournament_players WHERE tournament_id = ?", (tournament_id,))

            # Assign players to tee groups (e.g., groups of 3)
            player_entries = []
            group_size = 3
            for i, player in enumerate(players):
                tee_group = (i // group_size) + 1
                player_entries.append((tournament_id, player['id'], tee_group))
            
            conn.executemany('''
                INSERT INTO tournament_players (tournament_id, player_id, tee_group)
                VALUES (?, ?, ?)
            ''', player_entries)
            
            conn.commit()

    def complete_tournament(self, tournament_id):
        """Sets a tournament to completed and saves the final results."""
        with self._get_connection() as conn:
            # 1. Set status to completed
            conn.execute("UPDATE tournaments SET status = 'completed' WHERE id = ?", (tournament_id,))

            # 2. Get the final leaderboard with correct scores and positions
            final_leaderboard = self.get_leaderboard_from_live_scores(tournament_id)
            
            results_to_save = []
            for result in final_leaderboard:
                results_to_save.append((
                    tournament_id,
                    result['player_id'],
                    result['total_strokes'],
                    result['score_to_par'],
                    result['position'],
                    result.get('r1_score_strokes'),
                    result.get('r2_score_strokes'),
                    result.get('r3_score_strokes'),
                    result.get('r4_score_strokes')
                ))

            # Clear old results and save new ones
            conn.execute("DELETE FROM tournament_results WHERE tournament_id = ?", (tournament_id,))
            conn.executemany('''
                INSERT INTO tournament_results (tournament_id, player_id, total_strokes, score_to_par, position, r1_score, r2_score, r3_score, r4_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', results_to_save)
            conn.commit()

    def get_tournament_results(self, tournament_id):
        """Gets the final results for a completed tournament."""
        with self._get_connection() as conn:
            return conn.execute('''
                SELECT r.*, p.name as player_name
                FROM tournament_results r
                JOIN players p ON r.player_id = p.id
                WHERE r.tournament_id = ?
                ORDER BY r.position, p.name
            ''', (tournament_id,)).fetchall()

    def get_player_by_id(self, player_id):
        """Gets a player by their ID."""
        with self._get_connection() as conn:
            return conn.execute('SELECT * FROM players WHERE id = ?', (player_id,)).fetchone()

    def is_cut_applied(self, tournament_id):
        """Check if the cut has been applied to a tournament."""
        with self._get_connection() as conn:
            result = conn.execute('SELECT cut_applied FROM tournaments WHERE id = ?', (tournament_id,)).fetchone()
            return result and result['cut_applied']

    def apply_cut(self, tournament_id, players_made_cut_ids):
        """
        Updates player statuses based on the cut and marks the cut as applied for the tournament.
        """
        with self._get_connection() as conn:
            # First, set all players in the tournament to 'cut'
            conn.execute("UPDATE tournament_players SET status = 'cut' WHERE tournament_id = ?", (tournament_id,))

            # Then, set the players who made the cut back to 'active'
            # This is safer than looping through players to cut, especially with large rosters.
            if players_made_cut_ids:
                # Create a placeholder string for the IN clause, e.g., (?, ?, ?)
                placeholders = ', '.join('?' for _ in players_made_cut_ids)
                query = f"UPDATE tournament_players SET status = 'active' WHERE tournament_id = ? AND player_id IN ({placeholders})"
                
                # The parameters must be a single tuple: (tournament_id, player_id1, player_id2, ...)
                params = (tournament_id,) + tuple(players_made_cut_ids)
                conn.execute(query, params)

            # Finally, mark the cut as applied for the tournament
            conn.execute("UPDATE tournaments SET cut_applied = 1 WHERE id = ?", (tournament_id,))
            conn.commit()

    def is_regrouped_for_round4(self, tournament_id):
        """Check if players have been regrouped for round 4."""
        with self._get_connection() as conn:
            result = conn.execute('SELECT regrouped_round4 FROM tournaments WHERE id = ?', (tournament_id,)).fetchone()
            return result and result['regrouped_round4']

    def get_round_groups(self, tournament_id, round_num):
        """Get the group assignments for a specific round."""
        with self._get_connection() as conn:
            if round_num <= 2:
                # For rounds 1-2, use original tournament_players groupings
                results = conn.execute('''
                    SELECT tp.tee_group as group_num, tp.player_id
                    FROM tournament_players tp
                    WHERE tp.tournament_id = ?
                    ORDER BY tp.tee_group, tp.player_id
                ''', (tournament_id,)).fetchall()
            else:
                # For rounds 3-4, use round_groups table
                results = conn.execute('''
                    SELECT rg.group_num, rg.player_id
                    FROM round_groups rg
                    WHERE rg.tournament_id = ? AND rg.round_num = ?
                    ORDER BY rg.group_num, rg.player_id
                ''', (tournament_id, round_num)).fetchall()
            
            # Group by group_num
            groups = {}
            for row in results:
                group_num = row['group_num']
                if group_num not in groups:
                    groups[group_num] = []
                groups[group_num].append(row['player_id'])
            
            # Convert to list of tuples
            return [(group_num, player_ids) for group_num, player_ids in groups.items()]

    def save_round_groups(self, tournament_id, round_num, groups):
        """Save group assignments for a specific round."""
        with self._get_connection() as conn:
            # Clear existing groups for this round
            conn.execute('DELETE FROM round_groups WHERE tournament_id = ? AND round_num = ?', 
                        (tournament_id, round_num))
            
            # Save new groups
            for group_num, player_ids in groups:
                for player_id in player_ids:
                    conn.execute('''
                        INSERT INTO round_groups (tournament_id, round_num, group_num, player_id)
                        VALUES (?, ?, ?, ?)
                    ''', (tournament_id, round_num, group_num, player_id))
            
            # Mark round 4 as regrouped if applicable
            if round_num == 4:
                conn.execute('UPDATE tournaments SET regrouped_round4 = 1 WHERE id = ?', (tournament_id,))
            
            conn.commit()

    def get_course_by_id(self, course_id):
        with self._get_connection() as conn:
            return conn.execute('SELECT * FROM courses WHERE id = ?', (course_id,)).fetchone()
            
    def get_holes_for_course(self, course_id):
        with self._get_connection() as conn:
            return conn.execute('SELECT * FROM holes WHERE course_id = ? ORDER BY hole_number', (course_id,)).fetchall()

    # --- Player Functions ---
    def get_all_players(self):
        with self._get_connection() as conn:
            return conn.execute('SELECT * FROM players ORDER BY overall_skill DESC').fetchall()

    def get_tournament_players(self, tournament_id, round_num=None):
        """
        Gets all players for a given tournament.
        If round_num is provided, it fetches the tee_group for that specific round.
        Otherwise, it defaults to the initial tee_group.
        """
        with self._get_connection() as conn:
            if round_num:
                # Get players and their group for a specific round
                return conn.execute('''
                    SELECT p.*, rg.group_num as tee_group, tp.status
                    FROM players p
                    JOIN round_groups rg ON p.id = rg.player_id
                    JOIN tournament_players tp ON p.id = tp.player_id AND tp.tournament_id = rg.tournament_id
                    WHERE rg.tournament_id = ? AND rg.round_num = ?
                    ORDER BY rg.group_num
                ''', (tournament_id, round_num)).fetchall()
            else:
                # Get players with their initial tee_group
                return conn.execute('''
                    SELECT p.*, tp.tee_group, tp.status
                    FROM players p
                    JOIN tournament_players tp ON p.id = tp.player_id
                    WHERE tp.tournament_id = ?
                    ORDER BY tp.tee_group
                ''', (tournament_id,)).fetchall()

    def get_live_scores_for_tournament(self, tournament_id):
        """Gets all raw live scores for a given tournament."""
        with self._get_connection() as conn:
            return conn.execute('''
                SELECT * FROM live_scores
                WHERE tournament_id = ?
            ''', (tournament_id,)).fetchall()

    def get_live_scores_for_hole(self, tournament_id, round_num, hole_num):
        """Gets all raw live scores for a specific hole in a tournament."""
        with self._get_connection() as conn:
            return conn.execute('''
                SELECT * FROM live_scores
                WHERE tournament_id = ? AND round = ? AND hole = ?
            ''', (tournament_id, round_num, hole_num)).fetchall()

    # --- Live Score & Leaderboard Functions ---
    def get_leaderboard_from_live_scores(self, tournament_id):
        """
        Constructs a leaderboard with detailed live scoring.
        - For rounds in progress, it shows the "to par" score for that round.
        - For completed rounds, it shows the final stroke count.
        """
        with self._get_connection() as conn:
            tournament = conn.execute('SELECT * FROM tournaments WHERE id = ?', (tournament_id,)).fetchone()
            if not tournament: return []

            # Fetch players based on the current round's grouping
            players = self.get_tournament_players(tournament_id, tournament['current_round'])
            if not players:
                # Fallback to initial groups if round-specific groups don't exist
                players = self.get_tournament_players(tournament_id)

            if not players: return []

            holes = conn.execute('SELECT hole_number, par FROM holes WHERE course_id = ? ORDER BY hole_number', (tournament['course_id'],)).fetchall()
            hole_pars = {hole['hole_number']: hole['par'] for hole in holes}
            
            live_scores = self.get_live_scores_for_tournament(tournament_id)
            scores_by_player = defaultdict(list)
            for score in live_scores:
                scores_by_player[score['player_id']].append(score)

            leaderboard = []
            for player in players:
                player_scores = scores_by_player.get(player['id'], [])
                
                total_strokes = sum(s['score'] for s in player_scores)
                holes_played_total = len(player_scores)
                
                par_for_holes_played = sum(hole_pars.get(s['hole'], 4) for s in player_scores)
                score_to_par_total = total_strokes - par_for_holes_played

                # Calculate round scores
                round_scores = {}
                for i in range(1, 5):
                    round_scores[i] = self._calculate_round_score(player_scores, i, hole_pars)
                
                if player['status'] == 'cut':
                    round_scores[3]['display'] = 'CUT'
                    round_scores[4]['display'] = 'CUT'

                # Determine THRU value for the current round
                holes_in_current_round = len([s for s in player_scores if s['round'] == tournament['current_round']])

                leaderboard.append({
                    'player_id': player['id'],
                    'player_name': player['name'],
                    'tee_group': player['tee_group'],
                    'status': player['status'],
                    'total_strokes': total_strokes,
                    'score_to_par': score_to_par_total,
                    'holes_played': holes_in_current_round,
                    'tee_time': self.get_player_tee_time(player['tee_group'], tournament['current_round'], tournament),
                    'r1_score_display': round_scores[1]['display'],
                    'r1_score_strokes': round_scores[1]['strokes'],
                    'r2_score_display': round_scores[2]['display'],
                    'r2_score_strokes': round_scores[2]['strokes'],
                    'r3_score_display': round_scores[3]['display'],
                    'r3_score_strokes': round_scores[3]['strokes'],
                    'r4_score_display': round_scores[4]['display'],
                    'r4_score_strokes': round_scores[4]['strokes'],
                })
            
            # --- Leaderboard Sorting ---
            # Determine the sorting key for each player.
            # This complex key ensures players are grouped correctly:
            # 1. Active players, sorted by score.
            # 2. Cut players, sorted by score.
            # 3. (In R1 only) Players yet to tee off, sorted by tee time.
            def get_sort_key(p):
                if p['status'] == 'cut':
                    return (1, p['score_to_par'], p['total_strokes']) # Group 1: Cut players
                if tournament['current_round'] == 1 and p['holes_played'] == 0:
                    return (2, p['tee_time']) # Group 2: Waiting players (only in R1)
                return (0, p['score_to_par'], p['total_strokes']) # Group 0: Active players

            leaderboard.sort(key=get_sort_key)

            # Recalculate positions after sorting
            if leaderboard:
                last_pos = 0
                last_score = -999
                for i, player in enumerate(leaderboard):
                    # Only assign position to non-cut players
                    if player['status'] != 'cut':
                        current_score = (player['score_to_par'], player['total_strokes'])
                        if current_score == last_score:
                            player['position'] = last_pos
                        else:
                            player['position'] = i + 1
                            last_pos = player['position']
                        last_score = current_score
                    else:
                        player['position'] = '' # No position for cut players
            return leaderboard

    def _calculate_round_score(self, player_scores, round_num, hole_pars):
        """
        Calculates the score for a single round. Returns to-par if in progress,
        or total strokes if complete.
        """
        scores_in_round = [s for s in player_scores if s['round'] == round_num]
        if not scores_in_round:
            return {'display': None, 'strokes': None}

        strokes = sum(s['score'] for s in scores_in_round)
        holes_played_in_round = len(scores_in_round)

        if holes_played_in_round < 18:
            # Round in progress, calculate to_par
            par_for_round = sum(hole_pars.get(s['hole'], 4) for s in scores_in_round)
            to_par = strokes - par_for_round
            
            display_score = "E" if to_par == 0 else f"+{to_par}" if to_par > 0 else str(to_par)
            return {'display': display_score, 'strokes': None} # Strokes are not final yet
        else:
            # Round complete, return total strokes
            return {'display': str(strokes), 'strokes': strokes}

    def save_live_score(self, tournament_id, player_id, round_num, hole_num, score):
        """Saves a single score for a player on a specific hole."""
        with self._get_connection() as conn:
            conn.execute('''
                INSERT OR REPLACE INTO live_scores (tournament_id, player_id, round, hole, score)
                VALUES (?, ?, ?, ?, ?)
            ''', (tournament_id, player_id, round_num, hole_num, score))
            conn.commit()

    def get_player_scores_in_round(self, tournament_id, player_id, round_num):
        """Get all scores for a player in a specific round."""
        with self._get_connection() as conn:
            return conn.execute('''
                SELECT * FROM live_scores 
                WHERE tournament_id = ? AND player_id = ? AND round = ?
                ORDER BY hole
            ''', (tournament_id, player_id, round_num)).fetchall()
            
    def count_players_finished_round(self, tournament_id, round_num):
        """Counts how many players have finished all 18 holes in a given round."""
        with self._get_connection() as conn:
            result = conn.execute('''
                SELECT COUNT(player_id)
                FROM (
                    SELECT player_id
                    FROM live_scores
                    WHERE tournament_id = ? AND round = ?
                    GROUP BY player_id
                    HAVING COUNT(hole) >= 18
                )
            ''', (tournament_id, round_num)).fetchone()
            return result[0] if result else 0

    # --- Betting Functions (Placeholder) ---
    def place_bet(self, user_id, tournament_id, player_id, bet_amount, odds):
        # This is a simplified version. A real implementation would be more complex.
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Deduct from balance
            cursor.execute('UPDATE users SET virtual_balance = virtual_balance - ? WHERE id = ?', (bet_amount, user_id))
            # Place bet
            cursor.execute('''
                INSERT INTO bets (user_id, tournament_id, player_id, bet_amount, odds)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, tournament_id, player_id, bet_amount, odds))
            conn.commit()
            return cursor.lastrowid

    def get_simulation_step(self, tournament_id):
        """Gets the current simulation step for a tournament."""
        with self._get_connection() as conn:
            result = conn.execute('SELECT simulation_step FROM tournaments WHERE id = ?', (tournament_id,)).fetchone()
            return result['simulation_step'] if result else 0

    def set_simulation_step(self, tournament_id, step):
        """Sets the simulation step for a tournament."""
        with self._get_connection() as conn:
            conn.execute('UPDATE tournaments SET simulation_step = ? WHERE id = ?', (step, tournament_id))
            conn.commit()

    def set_current_round(self, tournament_id, round_num):
        """Sets the current round for a tournament."""
        with self._get_connection() as conn:
            conn.execute('UPDATE tournaments SET current_round = ? WHERE id = ?', (round_num, tournament_id))
            conn.commit()

    def get_player_tee_time(self, player_tee_group, current_round, tournament_data):
        """
        Calculate the simulation step when a player's group will tee off.
        """
        round_start_step = tournament_data.get(f'r{current_round}_start_step', 0)
        # In this simulation, group interval is 1 step.
        # Group N tees off N-1 steps after the round starts.
        group_interval = 1 
        tee_time = round_start_step + (player_tee_group - 1) * group_interval
        return tee_time

    def set_round_start_step(self, tournament_id, round_num, step):
        """Sets the simulation step at which a round started."""
        with self._get_connection() as conn:
            # It's safer to use a whitelist of column names than to format it directly
            # to prevent SQL injection, though in this case it's internally controlled.
            if round_num in [2, 3, 4]:
                col_name = f'r{round_num}_start_step'
                conn.execute(f'UPDATE tournaments SET {col_name} = ? WHERE id = ?', (step, tournament_id))
                conn.commit()

    def get_players_in_group(self, tournament_id, round_num, group_num):
        """Gets all player data for a specific group in a specific round."""
        with self._get_connection() as conn:
            return conn.execute('''
                SELECT p.*, tp.status
                FROM players p
                JOIN round_groups rg ON p.id = rg.player_id
                JOIN tournament_players tp ON p.id = tp.player_id AND tp.tournament_id = rg.tournament_id
                WHERE rg.tournament_id = ? AND rg.round_num = ? AND rg.group_num = ?
            ''', (tournament_id, round_num, group_num)).fetchall()

    def get_hole_info(self, course_id, hole_number):
        """Gets the par and difficulty for a specific hole."""
        with self._get_connection() as conn:
            return conn.execute('SELECT par, difficulty_modifier FROM holes WHERE course_id = ? AND hole_number = ?', (course_id, hole_number)).fetchone()

# Instantiate the database handler
db = Database()

def init_db():
    """Initialize the database with the new, detailed schema for the golf simulator."""
    conn = sqlite3.connect(Config.DATABASE_PATH)
    c = conn.cursor()

    # Drop old tables to ensure a clean slate
    c.execute("DROP TABLE IF EXISTS users")
    c.execute("DROP TABLE IF EXISTS bets")
    c.execute("DROP TABLE IF EXISTS tournaments")
    c.execute("DROP TABLE IF EXISTS tournament_results")
    c.execute("DROP TABLE IF EXISTS live_scores")
    c.execute("DROP TABLE IF EXISTS tournament_players")
    c.execute("DROP TABLE IF EXISTS players")
    c.execute("DROP TABLE IF EXISTS courses")
    c.execute("DROP TABLE IF EXISTS holes")
    
    # --- User Management ---
    c.execute('''
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            virtual_balance REAL NOT NULL DEFAULT 10000.0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # --- Fictional League Schema ---
    c.execute('''
        CREATE TABLE players (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            country TEXT,
            overall_skill REAL NOT NULL,
            consistency REAL NOT NULL
        )
    ''')

    c.execute('''
        CREATE TABLE courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            architecture_style TEXT NOT NULL, -- e.g., 'Penal', 'Strategic'
            green_speed REAL NOT NULL, -- A modifier, e.g., 0.8 (slow) to 1.2 (fast)
            rough_height REAL NOT NULL -- A modifier, e.g., 0.9 (low) to 1.1 (high)
        )
    ''')
    
    c.execute('''
        CREATE TABLE holes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_id INTEGER NOT NULL,
            hole_number INTEGER NOT NULL,
            par INTEGER NOT NULL,
            difficulty_modifier REAL NOT NULL, -- e.g., 0.8 (easy) to 1.2 (hard)
            UNIQUE(course_id, hole_number),
            FOREIGN KEY(course_id) REFERENCES courses(id)
        )
    ''')
    
    c.execute('''
        CREATE TABLE tournaments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            course_id INTEGER,
            start_date TEXT,
            end_date TEXT,
            status TEXT DEFAULT 'pending', -- pending, active, completed, cancelled
            current_round INTEGER DEFAULT 1,
            simulation_step INTEGER DEFAULT 0,
            cut_applied BOOLEAN DEFAULT 0,
            r2_start_step INTEGER DEFAULT 0,
            r3_start_step INTEGER DEFAULT 0,
            r4_start_step INTEGER DEFAULT 0,
            regrouped_round4 BOOLEAN DEFAULT 0
        )
    ''')

    # New table to track which players are in which tournament and their tee group
    c.execute('''
        CREATE TABLE tournament_players (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tournament_id INTEGER NOT NULL,
            player_id INTEGER NOT NULL,
            tee_group INTEGER NOT NULL, -- To stagger starts
            status TEXT DEFAULT 'active', -- 'active' or 'cut'
            UNIQUE(tournament_id, player_id),
            FOREIGN KEY(tournament_id) REFERENCES tournaments(id),
            FOREIGN KEY(player_id) REFERENCES players(id)
        )
    ''')

    # Table to track which players made the cut
    c.execute('''
        CREATE TABLE tournament_cuts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tournament_id INTEGER NOT NULL,
            player_id INTEGER NOT NULL,
            made_cut INTEGER NOT NULL DEFAULT 0, -- 0 = missed cut, 1 = made cut
            FOREIGN KEY(tournament_id) REFERENCES tournaments(id),
            FOREIGN KEY(player_id) REFERENCES players(id)
        )
    ''')

    # Table to track group assignments for rounds 3 and 4
    c.execute('''
        CREATE TABLE round_groups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tournament_id INTEGER NOT NULL,
            round_num INTEGER NOT NULL, -- 3 or 4
            group_num INTEGER NOT NULL,
            player_id INTEGER NOT NULL,
            UNIQUE(tournament_id, round_num, group_num, player_id),
            FOREIGN KEY(tournament_id) REFERENCES tournaments(id),
            FOREIGN KEY(player_id) REFERENCES players(id)
        )
    ''')

    # Renamed from 'leaderboard' to reflect its new purpose for live, hole-by-hole scores
    c.execute('''
        CREATE TABLE live_scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tournament_id INTEGER NOT NULL,
            player_id INTEGER NOT NULL,
            round INTEGER NOT NULL,
            hole INTEGER NOT NULL,
            score INTEGER NOT NULL,
            UNIQUE(tournament_id, player_id, round, hole),
            FOREIGN KEY(tournament_id) REFERENCES tournaments(id),
            FOREIGN KEY(player_id) REFERENCES players(id)
        )
    ''')

    # This table will store the final, summarized results once a tournament is over
    c.execute('''
        CREATE TABLE tournament_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tournament_id INTEGER NOT NULL,
            player_id INTEGER NOT NULL,
            total_strokes INTEGER,
            score_to_par REAL,
            position INTEGER,
            r1_score INTEGER,
            r2_score INTEGER,
            r3_score INTEGER,
            r4_score INTEGER,
            FOREIGN KEY(tournament_id) REFERENCES tournaments(id),
            FOREIGN KEY(player_id) REFERENCES players(id)
        )
    ''')
    
    c.execute('''
        CREATE TABLE bets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            tournament_id INTEGER NOT NULL,
            player_id INTEGER NOT NULL,
            bet_amount REAL NOT NULL,
            odds REAL NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending', -- pending, won, lost
            payout REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(tournament_id) REFERENCES tournaments(id),
            FOREIGN KEY(player_id) REFERENCES players(id)
        )
    ''')

    conn.commit()
    conn.close()
    print("Database initialized with new simulator schema.")

if __name__ == '__main__':
    init_db() 