#!/usr/bin/env python3
"""
Test script to demonstrate the new course characteristics system.
Shows how different course variables affect player performance.
"""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from models.database import db, init_db
from services.seeder import seed_database, generate_course_characteristics
from services.simulation_service import SimulationService
import random

def test_course_characteristics():
    """Test the course characteristics system."""
    print("=== Course Characteristics Test ===\n")
    
    # Initialize database
    print("Initializing database...")
    init_db()
    seed_database()
    
    # Get a sample course with characteristics
    courses = db.get_all_courses()
    if not courses:
        print("No courses found!")
        return
    
    sample_course = courses[0]
    course_id = sample_course['id']
    
    # Get course characteristics
    characteristics = db.get_course_characteristics(course_id)
    
    print(f"Course: {sample_course['name']}")
    print(f"Location: {sample_course['city']}, {sample_course['state_country']}")
    print(f"Par: {sample_course['par']}")
    print("\nCourse Characteristics:")
    print("-" * 50)
    
    if characteristics:
        print(f"Weather Conditions:")
        print(f"  - Average Temperature: {characteristics['avg_temperature']:.2f} (0=50°F, 1=95°F)")
        print(f"  - Humidity Level: {characteristics['humidity_level']:.2f} (0=dry, 1=very humid)")
        print(f"  - Wind Factor: {characteristics['wind_factor']:.2f} (0=calm, 1=very windy)")
        print(f"  - Rain Probability: {characteristics['rain_probability']:.2f} (0=no rain, 1=heavy rain)")
        
        print(f"\nCourse Design:")
        print(f"  - Design Strategy: {characteristics['design_strategy']:.2f} (0=strategic, 1=penal)")
        print(f"  - Course Length: {characteristics['course_length']:.2f} (0=short, 1=very long)")
        print(f"  - Narrowness Factor: {characteristics['narrowness_factor']:.2f} (0=wide, 1=very narrow)")
        print(f"  - Hazard Density: {characteristics['hazard_density']:.2f} (0=few hazards, 1=many hazards)")
        
        print(f"\nCourse Conditions:")
        print(f"  - Green Speed: {characteristics['green_speed']:.2f} (0=slow, 1=very fast)")
        print(f"  - Turf Firmness: {characteristics['turf_firmness']:.2f} (0=soft, 1=very firm)")
        print(f"  - Rough Length: {characteristics['rough_length']:.2f} (0=short, 1=very long)")
        
        print(f"\nMental Factors:")
        print(f"  - Prestige Level: {characteristics['prestige_level']:.2f} (0=local, 1=major championship)")
        print(f"  - Course Age: {characteristics['course_age']:.2f} (0=new, 1=historic)")
        print(f"  - Crowd Factor: {characteristics['crowd_factor']:.2f} (0=small crowds, 1=large crowds)")
        
        print(f"\nPhysical Factors:")
        print(f"  - Elevation Factor: {characteristics['elevation_factor']:.2f} (0=sea level, 1=high altitude)")
        print(f"  - Terrain Difficulty: {characteristics['terrain_difficulty']:.2f} (0=flat, 1=very hilly)")
    else:
        print("No characteristics found for this course.")
    
    # Test player performance simulation
    print("\n" + "=" * 60)
    print("PLAYER PERFORMANCE SIMULATION")
    print("=" * 60)
    
    # Create sample players with different skill profiles
    sample_players = [
        {
            'name': 'Long Driver',
            'overall_skill': 85,
            'driving_skill': 95,
            'approach_skill': 80,
            'short_game_skill': 75,
            'putting_skill': 80
        },
        {
            'name': 'Accurate Player',
            'overall_skill': 85,
            'driving_skill': 75,
            'approach_skill': 95,
            'short_game_skill': 90,
            'putting_skill': 85
        },
        {
            'name': 'Putting Specialist',
            'overall_skill': 85,
            'driving_skill': 80,
            'approach_skill': 80,
            'short_game_skill': 85,
            'putting_skill': 95
        },
        {
            'name': 'Balanced Player',
            'overall_skill': 85,
            'driving_skill': 85,
            'approach_skill': 85,
            'short_game_skill': 85,
            'putting_skill': 85
        }
    ]
    
    # Simulate scores for each player
    sim_service = SimulationService()
    
    print(f"\nSimulating 18 holes for each player on {sample_course['name']}:")
    print("-" * 80)
    
    for player in sample_players:
        total_score = 0
        scores = []
        
        # Simulate 18 holes
        for hole_num in range(1, 19):
            score = sim_service._calculate_hole_score(
                player, 
                4,  # Assume par 4 for simplicity
                1.0,  # Standard difficulty
                characteristics
            )
            scores.append(score)
            total_score += score
        
        print(f"\n{player['name']}:")
        print(f"  Skills: Driving={player['driving_skill']}, Approach={player['approach_skill']}, "
              f"Short={player['short_game_skill']}, Putting={player['putting_skill']}")
        print(f"  Total Score: {total_score} ({total_score - 72:+d} to par)")
        print(f"  Average Score: {total_score/18:.1f}")
        
        # Show how course characteristics affected this player
        if characteristics:
            print(f"  Course Impact Analysis:")
            
            # Driving impact
            if characteristics['course_length'] > 0.7:
                print(f"    - Long course favored driving distance")
            if characteristics['narrowness_factor'] > 0.7:
                print(f"    - Narrow fairways penalized driving accuracy")
            
            # Approach impact
            if characteristics['design_strategy'] > 0.7:
                print(f"    - Penal design favored approach accuracy")
            if characteristics['turf_firmness'] > 0.7:
                print(f"    - Firm turf challenged approach shots")
            
            # Putting impact
            if characteristics['green_speed'] > 0.7:
                print(f"    - Fast greens favored putting skill")
            elif characteristics['green_speed'] < 0.3:
                print(f"    - Slow greens challenged putting skill")
            
            # Mental impact
            if characteristics['prestige_level'] > 0.7:
                print(f"    - High prestige course added mental pressure")
            if characteristics['crowd_factor'] > 0.7:
                print(f"    - Large crowds added pressure")
            
            # Weather impact
            if characteristics['wind_factor'] > 0.7:
                print(f"    - High winds affected all shots")
            if characteristics['humidity_level'] > 0.7:
                print(f"    - High humidity made conditions challenging")

if __name__ == '__main__':
    test_course_characteristics() 