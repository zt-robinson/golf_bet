import random
from models.database import db
from collections import defaultdict
import datetime

class SimulationService:
    """Handles the logic for simulating golf tournaments."""

    def _calculate_hole_score(self, player_skill, player_consistency, hole_par, hole_difficulty):
        """
        Calculates a player's score for a single hole.
        Fixed scoring algorithm for realistic golf scores.
        """
        # Base score tendency (lower is better)
        # Higher skill means a score closer to par, but not dramatically better
        skill_bonus = (player_skill - 75) / 100.0  # e.g. skill 85 -> +0.1, skill 95 -> +0.2
        base_tendency = hole_par - skill_bonus

        # Consistency defines the variance
        # Higher consistency means less variance from the base tendency
        consistency_factor = (100 - player_consistency) / 100.0  # e.g. consistency 90 -> 0.1
        
        # Introduce more randomness to allow for bogeys and worse
        random_factor = random.uniform(-3.0, 3.0) * consistency_factor
        
        # Difficulty modifier of the hole
        difficulty_factor = (hole_difficulty - 1.0) * 2.0  # e.g. 1.1 -> +0.2, 0.9 -> -0.2
        
        # Final score calculation
        raw_score = base_tendency + random_factor + difficulty_factor
        
        # Round to nearest integer
        final_score = round(raw_score)
        
        # Cap scores to avoid extreme outliers (e.g., nothing worse than triple bogey)
        return max(hole_par - 2, min(final_score, hole_par + 3))

    def advance_staggered_simulation(self, tournament_id):
        """
        Advances the simulation by one time-step, simulating the correct hole
        for every group currently on the course for the current round.
        """
        tournament = db.get_tournament_by_id(tournament_id)
        if not tournament or tournament['status'] in ['completed', 'cancelled']:
            return

        players = db.get_tournament_players(tournament_id)
        if not players: return

        all_groups = sorted(list(set(p['tee_group'] for p in players)))
        if not all_groups: return
        
        current_round = tournament['current_round']
        step = db.get_simulation_step(tournament_id)
        
        # A "block" is one full round for all groups.
        # It takes (num_groups + 18 - 1) steps to complete one block.
        block_length = len(all_groups) + 18 - 1
        
        # Check if the current round is over. If so, pause simulation.
        steps_this_round = step - ((current_round - 1) * block_length)
        if steps_this_round >= block_length:
            return # Do nothing, wait for user to start next round.

        # If we have completed all steps for all 4 rounds, tournament is over
        if current_round > 4:
            if tournament['status'] != 'completed':
                print(f"Tournament {tournament['name']} is fully complete!")
                db.complete_tournament(tournament_id)
            return
        
        print(f"--- Round {current_round}, Step {step + 1} ---")

        # In each step, iterate through all groups and see if they should play a hole
        for group_num in all_groups:
            # The hole to play is relative to the start of the current round's block
            hole_to_play = (step - ((current_round - 1) * block_length)) + 1 - group_num + 1

            if 1 <= hole_to_play <= 18:
                self._simulate_group_on_hole(tournament_id, group_num, current_round, hole_to_play)

        # Increment the master step counter
        db.set_simulation_step(tournament_id, step + 1)
        
    def _simulate_group_on_hole(self, tournament_id, group_num, round_num, hole_num):
        """Simulates a single group playing a specific hole."""
        
        live_scores_for_hole = db.get_live_scores_for_hole(tournament_id, round_num, hole_num)
        players_with_scores = {score['player_id'] for score in live_scores_for_hole}
        
        group_players = [p for p in db.get_tournament_players(tournament_id) if p['tee_group'] == group_num]
        
        # Check if the whole group is already done
        if all(p['id'] in players_with_scores for p in group_players):
            return

        print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Simulating R{round_num}, Hole {hole_num} (Par {self._get_hole_par(tournament_id, hole_num)}) for Group {group_num}...")
        
        for player in group_players:
            # Only simulate players who haven't already got a score for this hole
            if player['id'] not in players_with_scores:
                score = self._simulate_hole_score(player, tournament_id, hole_num)
                db.save_live_score(tournament_id, player['id'], round_num, hole_num, score)
                print(f"  - {player['name']} scores a {score}")
        print()

    def _get_hole_par(self, tournament_id, hole_num):
        """Get the par for a specific hole."""
        tournament = db.get_tournament_by_id(tournament_id)
        holes = db.get_holes_for_course(tournament['course_id'])
        if hole_num <= len(holes):
            return holes[hole_num - 1]['par']
        return 4  # Default fallback

    def _simulate_hole_score(self, player, tournament_id, hole_num):
        """Simulate a player's score for a specific hole."""
        tournament = db.get_tournament_by_id(tournament_id)
        holes = db.get_holes_for_course(tournament['course_id'])
        
        if hole_num <= len(holes):
            hole_info = holes[hole_num - 1]
            return self._calculate_hole_score(
                player['overall_skill'],
                player['consistency'],
                hole_info['par'],
                hole_info['difficulty_modifier']
            )
        return 4  # Default fallback 

    def run_simulation_step(self, tournament_id):
        tournament = db.get_tournament_by_id(tournament_id)
        if not tournament or tournament['status'] in ['completed', 'cancelled']:
            return

        players = db.get_tournament_players(tournament_id)
        if not players: return

        all_groups = sorted(list(set(p['tee_group'] for p in players)))
        if not all_groups: return
        
        current_step = db.get_simulation_step(tournament_id)
        current_round = tournament['current_round']
        round_start_step = tournament.get(f'r{current_round}_start_step', 0)

        # Determine which groups should play a hole in this step
        for group_num in all_groups:
            group_tee_off_step = round_start_step + (group_num - 1) * self.group_interval

            if current_step >= group_tee_off_step:
                self._simulate_hole_for_group(tournament_id, group_num)

        # After processing all groups for this step, advance the simulation step
        db.set_simulation_step(tournament_id, current_step + 1)

        # After advancing the step, check if the round is over and the cut needs to be applied.
        self._check_and_apply_cut(tournament_id)

    def start_tournament(self, tournament_id):
        """Initializes a tournament, creating initial player groups."""
        players = db.get_all_players() # Or some subset
        # For simplicity, we'll use all players.
        initial_groups = self.create_initial_groups(players)
        db.save_tournament_players(tournament_id, initial_groups)

        # Save the same groups for Round 1 and Round 2 for consistent lookup
        db.save_round_groups(tournament_id, 1, initial_groups)
        db.save_round_groups(tournament_id, 2, initial_groups)

        db.start_tournament(tournament_id)

    def regroup_players(self, tournament_id, round_num, players_to_group):
        """Regroups players based on score for a given round."""
        # Sort players by score (lowest to highest)
        sorted_players = sorted(players_to_group, key=lambda p: p['score_to_par'])
        
        # Create new groups of 3 (or whatever size is desired)
        new_groups = [sorted_players[i:i + 3] for i in range(0, len(sorted_players), 3)]
        
        # Format for saving
        groups_to_save = {}
        for i, group in enumerate(new_groups):
            group_num = i + 1
            player_ids = [p['player_id'] for p in group]
            groups_to_save[group_num] = player_ids
            
        db.save_round_groups(tournament_id, round_num, groups_to_save)
        # Also save for Round 4, as pairings are typically the same
        if round_num == 3:
            db.save_round_groups(tournament_id, 4, groups_to_save)

    def _check_and_apply_cut(self, tournament_id):
        """
        Checks if the conditions are met to apply the tournament cut, and if so,
        applies the cut and regroups players for the next round.
        """
        tournament = db.get_tournament_by_id(tournament_id)
        
        # Only apply the cut once, at the end of round 2
        if tournament['current_round'] != 2 or tournament['cut_applied']:
            return

        # Check if all active players have finished the round
        total_players = len(db.get_tournament_players(tournament_id, 2))
        finished_players = db.count_players_finished_round(tournament_id, 2)
        
        # Only apply the cut once all players have finished.
        if finished_players < total_players:
            # This log will now correctly track progress towards the cut.
            if tournament['simulation_step'] % 10 == 0:
                print(f"[Cut Check] Waiting for players to finish R2. Progress: {finished_players}/{total_players}")
            return

        print(f"Round 2 has completed. Applying cut for tournament {tournament_id}...")
        
        leaderboard = db.get_leaderboard_from_live_scores(tournament_id)
        # --- APPLY THE CUT (Top 65 and ties) ---
        if len(leaderboard) > 65:
            cut_line_score = leaderboard[64]['score_to_par']
            players_made_cut = [p for p in leaderboard if p['score_to_par'] <= cut_line_score]
        else:
            players_made_cut = leaderboard
            
        player_ids_made_cut = [p['player_id'] for p in players_made_cut]
        db.apply_cut(tournament_id, player_ids_made_cut)
        print(f"Cut applied. {len(player_ids_made_cut)} players made the cut.")

        # --- REGROUP PLAYERS FOR ROUND 3 ---
        self.regroup_players(tournament_id, 3, players_made_cut)
        print("Players regrouped for Round 3.")

    def _simulate_hole_for_group(self, tournament_id, group_num):
        tournament = db.get_tournament_by_id(tournament_id)
        current_round = tournament['current_round']

        players_in_group = db.get_players_in_group(tournament_id, current_round, group_num)
        if not players_in_group or players_in_group[0]['status'] == 'cut':
            return # Skip cut players or empty groups

        # Determine the current hole for this group IN THIS ROUND by checking the first player
        scores_in_round = db.get_player_scores_in_round(tournament_id, players_in_group[0]['id'], current_round)
        current_hole = len(scores_in_round) + 1

        if current_hole > 18:
            return # This group has finished the round

        hole_info = db.get_hole_info(tournament['course_id'], current_hole)
        if not hole_info: return 

        hole_par = hole_info['par']
        hole_difficulty = hole_info['difficulty_modifier']

        print(f"[{datetime.now().strftime('%H:%M:%S')}] Simulating R{current_round}, Hole {current_hole} (Par {hole_par}) for Group {group_num}...")

        for player in players_in_group:
            score = self._calculate_hole_score(
                player['overall_skill'],
                player['consistency'],
                hole_par,
                hole_difficulty
            )
            db.save_live_score(tournament_id, player['id'], current_round, current_hole, score)
            print(f"  - {player['name']} scores a {score}")
        print()

        # After processing the hole, check if the round is over and the cut needs to be applied.
        self._check_and_apply_cut(tournament_id) 