from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_apscheduler import APScheduler
from models.database import db
from services.simulation_service import SimulationService
from config import Config
import json

app = Flask(__name__)
app.secret_key = Config.SECRET_KEY

# Scheduler setup
scheduler = APScheduler()

# Initialize Simulation Service
sim_service = SimulationService()

def advance_simulation():
    """
    This function will be called by the scheduler to advance the simulation
    by one step (e.g., one group playing one hole).
    """
    with app.app_context():
        active_tournament = db.get_active_tournament()
        if active_tournament:
            sim_service.advance_staggered_simulation(active_tournament['id'])
        else:
            # No need to print this every 2 seconds
            pass

@app.route('/')
def home():
    """Home page showing available tournaments from the database"""
    try:
        tournaments = db.get_all_tournaments()
        return render_template('home.html', tournaments=tournaments)
    except Exception as e:
        return render_template('home.html', tournaments=[], error=f"Error loading data: {str(e)}")

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Simple login for virtual betting"""
    if request.method == 'POST':
        username = request.form.get('username')
        
        if not username:
            flash('Please enter a username')
            return redirect(url_for('login'))
        
        # Get or create user
        user = db.get_user(username)
        if not user:
            user_id = db.create_user(username)
            if user_id:
                user = db.get_user(username)
            else:
                flash('Error creating user')
                return redirect(url_for('login'))
        
        session['user_id'] = user['id']
        session['username'] = user['username']
        flash(f'Welcome back, {username}!')
        return redirect(url_for('dashboard'))
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Logout user"""
    session.clear()
    flash('You have been logged out')
    return redirect(url_for('home'))

@app.route('/dashboard')
def dashboard():
    """User dashboard with balance and betting history"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    user = db.get_user(session['username'])
    bets = db.get_user_bets(user_id)
    tournaments = db.get_all_tournaments()
    
    return render_template('dashboard.html', 
                         user=user, 
                         bets=bets,
                         tournaments=tournaments)

@app.route('/place_bet', methods=['POST'])
def place_bet():
    """This route will need to be updated to handle bets on simulated players/tournaments"""
    flash("Betting on simulated tournaments is not yet implemented.")
    return redirect(url_for('home'))

@app.route('/leaderboard/<int:tournament_id>')
def leaderboard(tournament_id):
    """Show tournament leaderboard from the database"""
    try:
        tournament = db.get_tournament_by_id(tournament_id)
        if not tournament:
            return "Tournament not found", 404

        leaderboard_data = db.get_leaderboard_from_live_scores(tournament_id)
        
        # Determine if the current round is over to show the "Next Round" button
        round_is_over = False
        if tournament['status'] == 'active' and leaderboard_data:
            min_holes_this_round = min(p['holes_played'] for p in leaderboard_data)
            if min_holes_this_round >= 18:
                round_is_over = True

        # After R2, the button should only appear AFTER the cut is applied.
        if tournament['current_round'] == 2 and not tournament['cut_applied']:
            round_is_over = False

        return render_template('leaderboard.html',
                             players=leaderboard_data,
                             tournament_name=tournament['name'],
                             tournament_id=tournament_id,
                             status=tournament['status'],
                             current_round=tournament['current_round'],
                             simulation_step=tournament['simulation_step'],
                             cut_applied=tournament['cut_applied'],
                             round_is_over=round_is_over)
    except Exception as e:
        # Simplified error handling for brevity
        return f"Error loading leaderboard: {str(e)}"

@app.route('/next_round/<int:tournament_id>', methods=['GET', 'POST'])
def next_round(tournament_id):
    tournament = db.get_tournament_by_id(tournament_id)
    if not tournament:
        return "Tournament not found", 404

    current_round = tournament['current_round']
    next_round_num = current_round + 1

    if next_round_num > 4:
        # End of tournament
        return redirect(url_for('leaderboard', tournament_id=tournament_id))
    
    # Note: If moving to R3, the cut and regrouping have already been applied automatically
    # by the simulation service as soon as R2 was complete.

    # Record the simulation step when the next round is starting
    current_step = db.get_simulation_step(tournament_id)
    db.set_round_start_step(tournament_id, next_round_num, current_step)

    # Advance the round
    db.set_current_round(tournament_id, next_round_num)
    
    return redirect(url_for('leaderboard', tournament_id=tournament_id))

@app.route('/start_tournament/<int:tournament_id>')
def start_tournament(tournament_id):
    """
    Sets a tournament's status to 'active' to begin the live simulation.
    """
    try:
        db.start_tournament(tournament_id)
        tournament = db.get_tournament_by_id(tournament_id)
        flash(f"Tournament {tournament['name']} has started!")
    except Exception as e:
        flash(f'Error starting tournament: {str(e)}')
    return redirect(url_for('home'))

@app.route('/api/tournaments')
def api_tournaments():
    """API endpoint to get tournaments from the database"""
    try:
        tournaments = db.get_all_tournaments()
        return jsonify(tournaments or [])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/players/<int:tournament_id>')
def api_players(tournament_id):
    """API endpoint to get players for a given tournament"""
    try:
        # For now, we assume all players are available for all tournaments.
        # A future enhancement would be to have specific player fields for each tournament.
        players = db.get_all_players()
        return jsonify(players or [])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    scheduler.add_job(id='Live Simulation Job', func=advance_simulation, trigger='interval', seconds=1)
    scheduler.start()
    app.run(debug=True, use_reloader=False)
