import random
from models.database import db
from collections import defaultdict
import datetime

class SimulationService:
    """Handles the logic for simulating golf tournaments."""

    def _calculate_hole_score(self, player_skills, hole_par, hole_difficulty):
        """
        Calculates a player's score for a single hole using the new detailed skill system.
        """
        # Extract skills from the player data
        overall_skill = player_skills['overall_skill']
        driving_skill = player_skills['driving_skill']
        approach_skill = player_skills['approach_skill']
        short_game_skill = player_skills['short_game_skill']
        putting_skill = player_skills['putting_skill']
        
        # Calculate a weighted skill score based on hole type
        # For simplicity, we'll use a weighted average of all skills
        weighted_skill = (overall_skill * 0.3 + driving_skill * 0.25 + approach_skill * 0.25 + 
                         short_game_skill * 0.15 + putting_skill * 0.05)
        
        # Base score tendency (lower is better)
        # Higher skill means a score closer to par, but not dramatically better
        skill_bonus = (weighted_skill - 75) / 100.0  # e.g. skill 85 -> +0.1, skill 95 -> +0.2
        base_tendency = hole_par - skill_bonus

        # Use overall skill as a consistency factor (higher skill = more consistent)
        consistency_factor = (100 - weighted_skill) / 100.0  # e.g. skill 90 -> 0.1
        
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

        current_round = tournament['current_round']
        players = db.get_tournament_players(tournament_id, current_round)
        if not players: 
            return

        all_groups = sorted(list(set(p['tee_group'] for p in players)))
        if not all_groups: return
        
        step = db.get_simulation_step(tournament_id)
        
        # The total number of steps for a round to complete
        block_length = len(all_groups) + 18 - 1 

        # Get the actual start step for the current round from the DB
        round_start_step = tournament.get(f'r{current_round}_start_step', 0)
        
        # Calculate steps elapsed *in this round*
        steps_this_round = step - round_start_step
        
        # Check if the current round is over. If so, pause simulation.
        if steps_this_round >= block_length:
            # Now check if all players have finished the current round
            total_players = len(db.get_tournament_players(tournament_id, current_round))
            finished_players = db.count_players_finished_round(tournament_id, current_round)
            if finished_players >= total_players:
                # If Round 4 is over, the tournament is complete
                if current_round == 4:
                    print(f"Tournament {tournament['name']} is fully complete!")
                    db.complete_tournament(tournament_id)
                    return # Stop simulation permanently
                
                # Special handling for Round 2 - apply cut if not already applied
                if current_round == 2 and not tournament['cut_applied']:
                    self._check_and_apply_cut(tournament_id)
                return  # Stop simulation, wait for user to start next round
            else:
                return  # Wait for all players to finish

        for group_num in all_groups:
            # Calculate hole to play based on steps *in this round*
            hole_to_play = steps_this_round - (group_num - 1) + 1
            
            group_players = [p for p in players if p['tee_group'] == group_num]

            if 1 <= hole_to_play <= 18:
                self._simulate_group_on_hole(tournament_id, group_num, current_round, hole_to_play, group_players)

        # Increment the master step counter
        db.set_simulation_step(tournament_id, step + 1)
        
    def _simulate_group_on_hole(self, tournament_id, group_num, round_num, hole_num, group_players):
        """Simulates a single group playing a specific hole."""
        
        live_scores_for_hole = db.get_live_scores_for_hole(tournament_id, round_num, hole_num)
        players_with_scores = {score['player_id'] for score in live_scores_for_hole}
        
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
                player,
                hole_info['par'],
                hole_info['difficulty_modifier']
            )
        return 4  # Default fallback

    def regroup_players(self, tournament_id, round_num, players_to_group, conn=None):
        """
        Regroups players based on score for a given round.
        - Sorts players by score (best to worst).
        - Creates groups of 2.
        - Assigns tee times in reverse order (worst scores first).
        """
        # 1. Sort players by score (lowest to highest)
        sorted_players = sorted(players_to_group, key=lambda p: p['score_to_par'])
        
        # 2. Create logical pairings (groups of 2)
        logical_groups = []
        for i in range(0, len(sorted_players), 2):
            logical_groups.append(sorted_players[i:i + 2])
        
        # 3. Invert the groups to set tee time order (worst scores first)
        # The database uses the group number as the tee time, so we reverse the
        # list of groups, and the new index + 1 becomes the group number.
        groups_for_tee_times = list(reversed(logical_groups))

        # 4. Format for saving to the database
        groups_to_save = {}
        for i, group in enumerate(groups_for_tee_times):
            group_num = i + 1  # This is the new tee group number
            player_ids = [p['player_id'] for p in group]
            groups_to_save[group_num] = player_ids
            
        # 5. Save the new groups for the upcoming rounds
        db.save_round_groups(tournament_id, round_num, groups_to_save, conn=conn)
        
        # Also save for Round 4, as pairings are typically the same
        if round_num == 3:
            db.save_round_groups(tournament_id, 4, groups_to_save, conn=conn)

    def _check_and_apply_cut(self, tournament_id):
        """
        Checks if the conditions are met to apply the tournament cut, and if so,
        applies the cut and regroups players for the next round using a single
        database connection to prevent deadlocks.
        """
        with db._get_connection() as conn:
            tournament = db.get_tournament_by_id(tournament_id, conn=conn)
            
            # Only apply the cut once, at the end of round 2
            if tournament['current_round'] != 2 or tournament['cut_applied']:
                return

            # Check if all active players have finished the round
            total_players = len(db.get_tournament_players(tournament_id, 2, conn=conn))
            finished_players = db.count_players_finished_round(tournament_id, 2, conn=conn)
            
            if finished_players < total_players:
                return

            print(f"Round 2 has completed. Applying cut for tournament {tournament_id}...")
            
            leaderboard = db.get_leaderboard_from_live_scores(tournament_id, conn=conn)
            # --- APPLY THE CUT (Top 65 and ties) ---
            if len(leaderboard) > 65:
                cut_line_score = leaderboard[64]['score_to_par']
                players_made_cut = [p for p in leaderboard if p['score_to_par'] <= cut_line_score]
            else:
                players_made_cut = leaderboard
                
            player_ids_made_cut = [p['player_id'] for p in players_made_cut]
            db.apply_cut(tournament_id, player_ids_made_cut, conn=conn)
            print(f"Cut applied. {len(player_ids_made_cut)} players made the cut.")

            # --- REGROUP PLAYERS FOR ROUND 3 ---
            self.regroup_players(tournament_id, 3, players_made_cut, conn=conn)
            print("Players regrouped for Round 3.")

            conn.commit() 