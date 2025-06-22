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
                SELECT t.*, c.name as course_name, c.city, c.state_country
                FROM tournaments t
                JOIN courses c ON t.course_id = c.id
                ORDER BY t.start_date ASC
            ''').fetchall()

    def get_tournament_by_id(self, tournament_id, conn=None):
        db_conn = conn or self._get_connection()
        try:
            return db_conn.execute('SELECT * FROM tournaments WHERE id = ?', (tournament_id,)).fetchone()
        finally:
            if not conn:
                db_conn.close()

    def get_active_tournament(self):
        """Gets the currently active tournament, if any."""
        with self._get_connection() as conn:
            return conn.execute("SELECT * FROM tournaments WHERE status = 'active'").fetchone()

    def get_next_available_tournament(self):
        """Gets the next tournament that can be started (first pending tournament in chronological order)."""
        with self._get_connection() as conn:
            return conn.execute('''
                SELECT t.*, c.name as course_name, c.city, c.state_country
                FROM tournaments t
                JOIN courses c ON t.course_id = c.id
                WHERE t.status = 'pending'
                ORDER BY t.start_date ASC
                LIMIT 1
            ''').fetchone()

    def can_start_tournament(self, tournament_id):
        """Checks if a specific tournament can be started (it's the next in sequence)."""
        next_tournament = self.get_next_available_tournament()
        return next_tournament and next_tournament['id'] == tournament_id

    def start_tournament(self, tournament_id):
        """Sets a tournament to active and populates its player list."""
        with self._get_connection() as conn:
            # Check if any tournament is already active
            active_tournament = conn.execute("SELECT id FROM tournaments WHERE status = 'active'").fetchone()
            if active_tournament:
                raise ValueError(f"Tournament {active_tournament['id']} is already active. Only one tournament can run at a time.")
            
            # Check if this is the next tournament in sequence
            if not self.can_start_tournament(tournament_id):
                next_tournament = self.get_next_available_tournament()
                if next_tournament:
                    raise ValueError(f"Cannot start tournament {tournament_id}. The next tournament in sequence is {next_tournament['id']} ({next_tournament['name']}).")
                else:
                    raise ValueError("No tournaments are available to start.")
            
            conn.execute("UPDATE tournaments SET status = 'active', simulation_step = 0, current_round = 1 WHERE id = ?", (tournament_id,))

            players = self.get_all_players(conn=conn)
            
            conn.execute("DELETE FROM tournament_players WHERE tournament_id = ?", (tournament_id,))

            player_entries = []
            group_size = 3
            for i, player in enumerate(players):
                tee_group = (i // group_size) + 1
                player_entries.append((tournament_id, player['id'], tee_group))
            
            conn.executemany('INSERT INTO tournament_players (tournament_id, player_id, tee_group) VALUES (?, ?, ?)', player_entries)
            
            round_groups = {}
            for _, player_id, tee_group in player_entries:
                if tee_group not in round_groups:
                    round_groups[tee_group] = []
                round_groups[tee_group].append(player_id)
            
            self.save_round_groups(tournament_id, 1, round_groups, conn)
            self.save_round_groups(tournament_id, 2, round_groups, conn)
            
            conn.commit()

    def complete_tournament(self, tournament_id):
        """Sets a tournament to completed and saves the final results."""
        with self._get_connection() as conn:
            conn.execute("UPDATE tournaments SET status = 'completed' WHERE id = ?", (tournament_id,))
            final_leaderboard = self.get_leaderboard_from_live_scores(tournament_id, conn=conn)
            
            results_to_save = []
            for result in final_leaderboard:
                results_to_save.append((
                    tournament_id, result['player_id'], result['total_strokes'], result['score_to_par'],
                    result['position'], result.get('r1_score_strokes'), result.get('r2_score_strokes'),
                    result.get('r3_score_strokes'), result.get('r4_score_strokes')
                ))

            conn.execute("DELETE FROM tournament_results WHERE tournament_id = ?", (tournament_id,))
            conn.executemany('''
                INSERT INTO tournament_results (tournament_id, player_id, total_strokes, score_to_par, position, r1_score, r2_score, r3_score, r4_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', results_to_save)
            conn.commit()

    def get_tournament_results(self, tournament_id):
        with self._get_connection() as conn:
            return conn.execute('''
                SELECT r.*, p.name as player_name FROM tournament_results r
                JOIN players p ON r.player_id = p.id WHERE r.tournament_id = ?
                ORDER BY r.position, p.name
            ''', (tournament_id,)).fetchall()

    def get_player_by_id(self, player_id):
        with self._get_connection() as conn:
            return conn.execute('SELECT * FROM players WHERE id = ?', (player_id,)).fetchone()

    def is_cut_applied(self, tournament_id):
        with self._get_connection() as conn:
            result = conn.execute('SELECT cut_applied FROM tournaments WHERE id = ?', (tournament_id,)).fetchone()
            return result and result['cut_applied']

    def apply_cut(self, tournament_id, players_made_cut_ids, conn=None):
        db_conn = conn or self._get_connection()
        try:
            db_conn.execute("UPDATE tournament_players SET status = 'cut' WHERE tournament_id = ?", (tournament_id,))
            if players_made_cut_ids:
                placeholders = ', '.join('?' for _ in players_made_cut_ids)
                query = f"UPDATE tournament_players SET status = 'active' WHERE tournament_id = ? AND player_id IN ({placeholders})"
                params = (tournament_id,) + tuple(players_made_cut_ids)
                db_conn.execute(query, params)
            db_conn.execute("UPDATE tournaments SET cut_applied = 1 WHERE id = ?", (tournament_id,))
            if not conn:
                db_conn.commit()
        finally:
            if not conn:
                db_conn.close()

    def is_regrouped_for_round4(self, tournament_id):
        with self._get_connection() as conn:
            result = conn.execute('SELECT regrouped_round4 FROM tournaments WHERE id = ?', (tournament_id,)).fetchone()
            return result and result['regrouped_round4']

    def get_round_groups(self, tournament_id, round_num):
        with self._get_connection() as conn:
            if round_num <= 2:
                results = conn.execute('SELECT tp.tee_group as group_num, tp.player_id FROM tournament_players tp WHERE tp.tournament_id = ? ORDER BY tp.tee_group, tp.player_id', (tournament_id,)).fetchall()
            else:
                results = conn.execute('SELECT rg.group_num, rg.player_id FROM round_groups rg WHERE rg.tournament_id = ? AND rg.round_num = ? ORDER BY rg.group_num, rg.player_id', (tournament_id, round_num)).fetchall()
            
            groups = defaultdict(list)
            for row in results:
                groups[row['group_num']].append(row['player_id'])
            return list(groups.items())

    def save_round_groups(self, tournament_id, round_num, groups, conn=None):
        db_conn = conn or self._get_connection()
        try:
            db_conn.execute('DELETE FROM round_groups WHERE tournament_id = ? AND round_num = ?', (tournament_id, round_num))
            to_insert = []
            for group_num, player_ids in groups.items():
                for player_id in player_ids:
                    to_insert.append((tournament_id, round_num, group_num, player_id))
            db_conn.executemany('INSERT INTO round_groups (tournament_id, round_num, group_num, player_id) VALUES (?, ?, ?, ?)', to_insert)
            if round_num == 4:
                db_conn.execute('UPDATE tournaments SET regrouped_round4 = 1 WHERE id = ?', (tournament_id,))
            if not conn:
                db_conn.commit()
        finally:
            if not conn:
                db_conn.close()

    def get_course_by_id(self, course_id, conn=None):
        db_conn = conn or self._get_connection()
        try:
            return db_conn.execute('SELECT * FROM courses WHERE id = ?', (course_id,)).fetchone()
        finally:
            if not conn:
                db_conn.close()
            
    def get_holes_for_course(self, course_id, conn=None):
        db_conn = conn or self._get_connection()
        try:
            return db_conn.execute('SELECT * FROM holes WHERE course_id = ? ORDER BY hole_number', (course_id,)).fetchall()
        finally:
            if not conn:
                db_conn.close()

    def get_all_players(self, conn=None):
        db_conn = conn or self._get_connection()
        try:
            return db_conn.execute('SELECT * FROM players ORDER BY overall_skill DESC').fetchall()
        finally:
            if not conn:
                db_conn.close()

    def get_tournament_players(self, tournament_id, round_num=None, conn=None):
        db_conn = conn or self._get_connection()
        try:
            if round_num and round_num > 2:
                # For rounds 3 & 4, use round_groups which has been re-sorted
                return db_conn.execute('''
                    SELECT p.*, rg.group_num as tee_group, tp.status FROM players p
                    JOIN round_groups rg ON p.id = rg.player_id
                    JOIN tournament_players tp ON p.id = tp.player_id AND tp.tournament_id = rg.tournament_id
                    WHERE rg.tournament_id = ? AND rg.round_num = ? ORDER BY rg.group_num
                ''', (tournament_id, round_num)).fetchall()
            else:
                # For rounds 1 & 2 (or if no round specified), use the original tee_group
                return db_conn.execute('''
                    SELECT p.*, tp.tee_group, tp.status FROM players p
                    JOIN tournament_players tp ON p.id = tp.player_id
                    WHERE tp.tournament_id = ? ORDER BY tp.tee_group
                ''', (tournament_id,)).fetchall()
        finally:
            if not conn:
                db_conn.close()

    def get_live_scores_for_tournament(self, tournament_id, conn=None):
        db_conn = conn or self._get_connection()
        try:
            return db_conn.execute('SELECT * FROM live_scores WHERE tournament_id = ?', (tournament_id,)).fetchall()
        finally:
            if not conn:
                db_conn.close()

    def get_live_scores_for_hole(self, tournament_id, round_num, hole_num):
        with self._get_connection() as conn:
            return conn.execute('SELECT * FROM live_scores WHERE tournament_id = ? AND round = ? AND hole = ?',
                                (tournament_id, round_num, hole_num)).fetchall()

    def get_leaderboard_from_live_scores(self, tournament_id, conn=None):
        db_conn = conn or self._get_connection()
        try:
            tournament_info = self.get_tournament_by_id(tournament_id, conn=db_conn)
            current_round = tournament_info['current_round'] if tournament_info else 1
            
            players = self.get_tournament_players(tournament_id, current_round, conn=db_conn)
            if not players: return []

            scores = self.get_live_scores_for_tournament(tournament_id, conn=db_conn)
            holes = self.get_holes_for_course(tournament_info['course_id'], conn=db_conn)
            
            hole_pars = {h['hole_number']: h['par'] for h in holes}
            scores_by_player = defaultdict(list)
            for s in scores:
                scores_by_player[s['player_id']].append(s)

            leaderboard = []
            for p in players:
                player_scores = scores_by_player[p['id']]
                total_strokes = sum(s['score'] for s in player_scores)
                par_for_holes_played = sum(hole_pars.get(s['hole'], 4) for s in player_scores)
                
                # Calculate round scores relative to par
                round_scores = {}
                for i in range(1, 5):
                    round_player_scores = [s for s in player_scores if s['round'] == i]
                    is_finished = len(round_player_scores) >= 18
                    
                    if round_player_scores:
                        round_strokes = sum(s['score'] for s in round_player_scores)
                        round_par = sum(hole_pars.get(s['hole'], 4) for s in round_player_scores)
                        round_score_to_par = round_strokes - round_par
                        
                        display_val = round_score_to_par
                        if not is_finished:
                            if round_score_to_par == 0:
                                display_val = 'E'
                        
                        round_scores[i] = {
                            'strokes': round_strokes, 
                            'score_to_par': round_score_to_par,
                            'display': display_val,
                            'finished': is_finished
                        }
                    else:
                        round_scores[i] = {'strokes': None, 'score_to_par': None, 'display': None, 'finished': False}

                # Calculate current round holes played
                current_round_holes = len([s for s in player_scores if s['round'] == current_round])
                
                # Determine if player has teed off IN THIS ROUND (for THRU column)
                has_teed_off = current_round_holes > 0

                # Determine if player has started THE TOURNAMENT (for Pos and To Par)
                has_started_tournament = len(player_scores) > 0
                
                # Calculate tee time, adjusted for the start step of the current round
                round_start_step = 0
                if current_round > 1:
                    round_start_step = tournament_info.get(f'r{current_round}_start_step', 0)
                tee_time_step = round_start_step + (p['tee_group'] - 1)
                
                leaderboard.append({
                    'player_id': p['id'], 'player_name': p['name'], 'status': p['status'],
                    'total_strokes': total_strokes, 'score_to_par': total_strokes - par_for_holes_played,
                    'holes_played': current_round_holes,
                    'tee_group': p['tee_group'],
                    'has_teed_off': has_teed_off,
                    'has_started_tournament': has_started_tournament,
                    'tee_time_step': tee_time_step,
                    'r1_info': round_scores[1],
                    'r2_info': round_scores[2],
                    'r3_info': round_scores[3],
                    'r4_info': round_scores[4],
                })

            # Sort players based on status and score.
            # 1. Players who haven't started are sent to the bottom.
            # 2. Cut players are sorted below active players.
            # 3. Active players are sorted by score (to_par, then total_strokes).
            leaderboard.sort(key=lambda x: (
                not x['has_started_tournament'],  # False (0) comes before True (1)
                1 if x['status'] == 'cut' else 0,
                x['score_to_par'],
                x['total_strokes']
            ))
            
            pos = 0
            last_score = None
            for i, player in enumerate(leaderboard):
                # Assign position only to players who are active and have started
                if player['status'] != 'cut' and player['has_started_tournament']:
                    current_score = player['score_to_par']
                    if current_score != last_score:
                        pos = i + 1
                        last_score = current_score
                    player['position'] = pos
                else:
                    # No position for cut players or those who haven't started
                    player['position'] = None
                
            return leaderboard
        finally:
            if not conn:
                db_conn.close()

    def count_players_finished_round(self, tournament_id, round_num, conn=None):
        db_conn = conn or self._get_connection()
        try:
            active_players = db_conn.execute("SELECT player_id FROM tournament_players WHERE tournament_id = ? AND status = 'active'", (tournament_id,)).fetchall()
            if not active_players: return 0
            player_ids = [p['player_id'] for p in active_players]
            placeholders = ','.join('?' for _ in player_ids)
            query = f'SELECT player_id, COUNT(hole) as holes_played FROM live_scores WHERE tournament_id = ? AND round = ? AND player_id IN ({placeholders}) GROUP BY player_id'
            params = (tournament_id, round_num) + tuple(player_ids)
            results = db_conn.execute(query, params).fetchall()
            return sum(1 for r in results if r['holes_played'] >= 18)
        finally:
            if not conn:
                db_conn.close()

    def save_live_score(self, tournament_id, player_id, round_num, hole_num, score):
        with self._get_connection() as conn:
            conn.execute('INSERT OR REPLACE INTO live_scores (tournament_id, player_id, round, hole, score) VALUES (?, ?, ?, ?, ?)',
                         (tournament_id, player_id, round_num, hole_num, score))
            conn.commit()

    def get_simulation_step(self, tournament_id):
        with self._get_connection() as conn:
            result = conn.execute('SELECT simulation_step FROM tournaments WHERE id = ?', (tournament_id,)).fetchone()
            return result['simulation_step'] if result else 0

    def set_simulation_step(self, tournament_id, step):
        with self._get_connection() as conn:
            conn.execute('UPDATE tournaments SET simulation_step = ? WHERE id = ?', (step, tournament_id))
            conn.commit()

    def set_round_start_step(self, tournament_id, round_num, step):
        with self._get_connection() as conn:
            col_name = f'r{round_num}_start_step'
            if col_name in ['r2_start_step', 'r3_start_step', 'r4_start_step']:
                conn.execute(f'UPDATE tournaments SET {col_name} = ? WHERE id = ?', (step, tournament_id))
                conn.commit()

    def set_current_round(self, tournament_id, round_num):
        with self._get_connection() as conn:
            conn.execute('UPDATE tournaments SET current_round = ? WHERE id = ?', (round_num, tournament_id))
            conn.commit()
            
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
            driving_skill REAL NOT NULL,
            approach_skill REAL NOT NULL,
            short_game_skill REAL NOT NULL,
            putting_skill REAL NOT NULL,
            season_points INTEGER DEFAULT 0,
            season_money REAL DEFAULT 0.0
        )
    ''')

    c.execute('''
        CREATE TABLE courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            type TEXT NOT NULL,
            par REAL NOT NULL,
            difficulty REAL NOT NULL,
            city TEXT NOT NULL,
            state_country TEXT NOT NULL
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
            course_id INTEGER NOT NULL,
            start_date TIMESTAMP NOT NULL,
            end_date TIMESTAMP NOT NULL,
            purse REAL NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending', -- pending, active, completed, cancelled
            current_round INTEGER DEFAULT 1,
            simulation_step INTEGER DEFAULT 0,
            r2_start_step INTEGER DEFAULT 0,
            r3_start_step INTEGER DEFAULT 0,
            r4_start_step INTEGER DEFAULT 0,
            cut_applied INTEGER DEFAULT 0,
            FOREIGN KEY(course_id) REFERENCES courses(id)
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