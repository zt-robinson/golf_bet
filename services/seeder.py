import sqlite3
import random
from faker import Faker
from models.database import init_db
from datetime import datetime, timedelta

def get_db_connection():
    """Create a database connection."""
    conn = sqlite3.connect('golf_betting.db')
    conn.row_factory = sqlite3.Row
    return conn

def generate_course_name():
    """Generate a creative fictional course name based on the user's detailed spreadsheet."""
    
    adjectives = [
        "Old", "New", "Great", "High", "Royal", "Golden", "White", "Hidden", "Black", "Spotted", "St.", "Mount",
        "Astorian", "Elysian", "American", "Southern", "Northern", "Eastern", "Western"
    ]
    plants = [
        "Sycamore", "Pine", "Maple", "Spruce", "Oak", "Willow", "Aspen", "Ash", "Birch", "Cherry", "Dogwood",
        "Cottonwood", "Cedar", "Walnut", "Locust", "Larch", "Hickory", "Cypress", "Woodlands", "Ivy",
        "Amberwood", "Rose", "Apple", "Gorse", "Heather", "Larkspur", "Bramble", "Pines", "Thistle", "Elder", "Briar"
    ]
    geo = [
        "Cape", "Beach", "Ridge", "Channel", "Cliffs", "Cove", "Shoal", "Canyon", "Marsh", "Gulch", "Moors", "Hill",
        "Valley", "Meadow", "Glen", "Gap", "Stream", "River", "Creek", "Lake", "Pond", "Lagoon", "Delta", "Spring",
        "Highlands", "Dale", "Dell", "Gully", "Hills", "Hillock", "Pass", "Plains", "Summit", "Terrace", "Downs",
        "Dunes", "Hollow", "Point", "Rock", "Stone", "Grove", "Garden", "Arbor", "Heath", "Wood", "Forest", "Haven",
        "Head", "Fields", "Park", "Vale", "Fens"
    ]
    animals = [
        "Quail", "Pheasant", "Grouse", "Grebe", "Duck", "Goose", "Swan", "Teal", "Shoveler", "Wigeon", "Gadwall",
        "Pintail", "Mallard", "Scaup", "Eider", "Merganser", "Turkey", "Ptarmigan", "Rail", "Crane", "Stilt",
        "Oystercatcher", "Plover", "Sandpiper", "Turnstone", "Sanderling", "Dunlin", "Stint", "Woodcock", "Willet",
        "Jaeger", "Gull", "Tern", "Loon", "Albatross", "Petrel", "Shearwater", "Cormorant", "Heron", "Egret",
        "Bittern", "Ibis", "Spoonbill", "Osprey", "Owl", "Kingfisher", "Kestrel", "Kingbird", "Flycatcher",
        "Shrike", "Crow", "Raven", "Lark", "Kinglet", "Catbird", "Starling", "Thrush", "Finch", "Grosbeak",
        "Crossbill", "Siskin", "Longspur", "Sparrow", "Blackbird", "Grackle", "Warbler", "Cardinal", "Snapper",
        "Trout", "Steelhead", "Herring", "Bluefish", "Haddock", "Salmon", "Mackerel", "Sturgeon", "Shiner",
        "Stag", "Elk", "Deer", "Otter"
    ]
    professions = [
        "Friar", "Abbot", "Bishop", "Parson", "Foxcatcher", "Minstrel", "Maiden", "Mason", "Miller", "Deacon",
        "Butcher", "Fisherman", "Hunter", "Cooper", "Franciscan", "Jesuit", "Earl", "Duke", "Marquess", "Baron", "Baroness"
    ]
    structures = [
        "Village", "Abbey", "Rectory", "Ranch", "Farm", "Orchard", "Castle", "Manor", "Estate", "House", "Priory",
        "Court", "Hall", "Park", "Lodge", "Cottage", "Chapel", "Chateau", "Manse", "Bridge", "Cross", "Garden", "Green"
    ]
    names = [
        "Montgomery", "Cabot", "Carnegie", "Morgan", "Mellon", "Astor", "Lauder", "Hurst", "Hearst", "Pritzker",
        "Busch", "Anheuser", "Washington", "Sherman", "Baker", "Lowell", "Burgess", "Baroness", "Carter", "Nelson",
        "Lancaster", "Roosevelt", "Coolidge", "Delano", "Wilder", "Thoreau", "Harrison", "Rensselaer", "Adams",
        "Forbes", "Hardwick", "Rothschild", "Holmes", "Appleton", "Bates", "Buckingham", "Coates", "Choate",
        "Cooper", "Cushing", "Emerson", "Gardner", "Lawrence", "Peabody", "Thayer", "Warren", "Amory", "Endicott",
        "Lyman", "Oakes", "Paine", "Sedgwick", "Shattuck", "Storrow", "Winthrop", "Stoke", "Stockton", "Windsor",
        "Manse", "Hamilton", "Berkshire", "Bradley", "Stewart"
    ]
    suffixes = [
        "dore", "mere", "town", "burg", "aster", "ton", "minster", "land", "ford", "downe", "bury", "ham", "cove",
        "worth", "hurst", "lands", "wood", "shire", "dale", "hill", "bourne", "vale", "hall", "broke", "-on-Sea",
        "more", "wick", "haven", "stone", "ridge"
    ]
    organizations = [
        "Country Club", "Golf Club", "Hunt Club", "Club", "National Golf Club", "Sporting Club",
        "Links", "Golf Links", "Resort", "Golf Resort", "Golf Course", "Golf & Hunt Club", "Cricket Club", 
        "Athletic Club", "Golf & Country Club"
    ]

    # --- Naming Patterns based on User's Convention ---
    
    # Simple Patterns
    p1 = f"{random.choice(plants)} {random.choice(geo)}"                             # Walnut Lake
    p2 = f"{random.choice(plants)} {random.choice(structures)}"                      # Cottonwood House
    p3 = f"{random.choice(animals)} {random.choice(structures)}"                     # Grackle House
    p4 = f"{random.choice(names)} {random.choice(plants)}"                           # Lancaster Cottonwood
    p5 = f"{random.choice(professions)} {random.choice(structures)}"                 # Foxcatcher Chapel

    # Adjective-led Patterns
    p6 = f"{random.choice(adjectives)} {random.choice(plants)} {random.choice(geo)}" # Astorian Oak Dale
    p7 = f"{random.choice(adjectives)} {random.choice(animals)} {random.choice(geo)}" # Astorian Shiner Creek
    p8 = f"{random.choice(adjectives)} {random.choice(professions)} {random.choice(structures)}" # Golden Foxcatcher Manse
    
    # Suffix Concatenation Patterns
    name = random.choice(names)
    suffix = random.choice(suffixes)
    if suffix == "-on-Sea":
        p9 = f"{name}{suffix}" # Baker-on-Sea
    else:
        # Avoids attaching a suffix to a name that ends in the same letter
        if name.endswith(suffix[0]):
             p9 = f"{name[:-1]}{suffix}" # Peabody + burg -> Peabodyburg
        else:
             p9 = f"{name}{suffix}" # Oakes + bourne -> Oakesbourne

    p10 = f"{p9} {random.choice(structures)}" # Winthrop Rectory (structure acts as suffix here)
    
    # Select a base pattern
    patterns = [p1, p2, p3, p4, p5, p6, p7, p8, p9, p10]
    base_name = random.choice(patterns)
    
    # Always add an organization suffix
    return f"{base_name} {random.choice(organizations)}"

def seed_database():
    """Populate the database with fictional data based on the new simulation model."""
    fake = Faker()
    conn = get_db_connection()
    c = conn.cursor()

    print("Seeding database with new simulation data...")

    # --- 1. Create Players ---
    countries = ['USA', 'UK', 'Australia', 'Canada', 'Sweden', 'Spain', 'South Africa', 'Japan', 'South Korea', 'Ireland']
    players = []
    for _ in range(150):
        # Generate male names only, without professional titles
        first_name = fake.first_name_male()
        last_name = fake.last_name()
        full_name = f"{first_name} {last_name}"
        
        players.append((
            full_name,
            random.choice(countries),
            round(random.uniform(70, 95), 2),  # Overall Skill
            round(random.uniform(70, 95), 2),  # Driving Skill
            round(random.uniform(70, 95), 2),  # Approach Skill
            round(random.uniform(70, 95), 2),  # Short Game Skill
            round(random.uniform(70, 95), 2),  # Putting Skill
            0,  # Season Points
            0.0,  # Season Money
        ))
    c.executemany('INSERT INTO players (name, country, overall_skill, driving_skill, approach_skill, short_game_skill, putting_skill, season_points, season_money) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)', players)
    print(f"Seeded {len(players)} players.")

    # --- 3. Define Location and Naming Components ---
    
    # Locations (Expanded list for name generation)
    us_states = [
        "Alabama", "Alaska", "Arizona", "Arkansas", "California", "Colorado", "Connecticut", "Delaware", "Florida", 
        "Georgia", "Hawaii", "Idaho", "Illinois", "Indiana", "Iowa", "Kansas", "Kentucky", "Louisiana", "Maine", 
        "Maryland", "Massachusetts", "Michigan", "Minnesota", "Mississippi", "Missouri", "Montana", "Nebraska", 
        "Nevada", "New Hampshire", "New Jersey", "New Mexico", "New York", "North Carolina", "North Dakota", "Ohio", 
        "Oklahoma", "Oregon", "Pennsylvania", "Rhode Island", "South Carolina", "South Dakota", "Tennessee", "Texas", 
        "Utah", "Vermont", "Virginia", "Washington", "West Virginia", "Wisconsin", "Wyoming"
    ]
    
    # US Cities by State Population (Top 5 states get 5 cities, next 20 get 3, next 20 get 2, rest get 1)
    us_cities_by_state = {
        # Top 5 States by Population (5 cities each)
        "California": ["Los Angeles", "San Diego", "San Jose", "San Francisco", "Fresno"],
        "Texas": ["Houston", "San Antonio", "Dallas", "Austin", "Fort Worth"],
        "Florida": ["Jacksonville", "Miami", "Tampa", "Orlando", "St. Petersburg"],
        "New York": ["New York", "Buffalo", "Rochester", "Yonkers", "Syracuse"],
        "Pennsylvania": ["Philadelphia", "Pittsburgh", "Allentown", "Erie", "Reading"],
        
        # Next 20 States by Population (3 cities each)
        "Illinois": ["Chicago", "Aurora", "Naperville"],
        "Ohio": ["Columbus", "Cleveland", "Cincinnati"],
        "Georgia": ["Atlanta", "Augusta", "Columbus"],
        "North Carolina": ["Charlotte", "Raleigh", "Greensboro"],
        "Michigan": ["Detroit", "Grand Rapids", "Warren"],
        "New Jersey": ["Newark", "Jersey City", "Paterson"],
        "Virginia": ["Virginia Beach", "Richmond", "Norfolk"],
        "Washington": ["Seattle", "Spokane", "Tacoma"],
        "Arizona": ["Phoenix", "Tucson", "Mesa"],
        "Tennessee": ["Nashville", "Memphis", "Knoxville"],
        "Indiana": ["Indianapolis", "Fort Wayne", "Evansville"],
        "Massachusetts": ["Boston", "Worcester", "Springfield"],
        "Missouri": ["Kansas City", "St. Louis", "Springfield"],
        "Maryland": ["Baltimore", "Frederick", "Rockville"],
        "Colorado": ["Denver", "Colorado Springs", "Aurora"],
        "Wisconsin": ["Milwaukee", "Madison", "Green Bay"],
        "Minnesota": ["Minneapolis", "St. Paul", "Rochester"],
        "South Carolina": ["Columbia", "Charleston", "North Charleston"],
        "Alabama": ["Birmingham", "Montgomery", "Huntsville"],
        "Louisiana": ["New Orleans", "Baton Rouge", "Shreveport"],
        "Kentucky": ["Louisville", "Lexington", "Bowling Green"],
        "Oregon": ["Portland", "Salem", "Eugene"],
        
        # Next 20 States by Population (2 cities each)
        "Oklahoma": ["Oklahoma City", "Tulsa"],
        "Connecticut": ["Bridgeport", "New Haven"],
        "Utah": ["Salt Lake City", "West Valley City"],
        "Iowa": ["Des Moines", "Cedar Rapids"],
        "Nevada": ["Las Vegas", "Reno"],
        "Arkansas": ["Little Rock", "Fort Smith"],
        "Mississippi": ["Jackson", "Gulfport"],
        "Kansas": ["Wichita", "Overland Park"],
        "New Mexico": ["Albuquerque", "Las Cruces"],
        "Nebraska": ["Omaha", "Lincoln"],
        "West Virginia": ["Charleston", "Huntington"],
        "Idaho": ["Boise", "Meridian"],
        "Hawaii": ["Honolulu", "Hilo"],
        "New Hampshire": ["Manchester", "Nashua"],
        "Maine": ["Portland", "Lewiston"],
        "Montana": ["Billings", "Missoula"],
        "Rhode Island": ["Providence", "Warwick"],
        "Delaware": ["Wilmington", "Dover"],
        "South Dakota": ["Sioux Falls", "Rapid City"],
        "North Dakota": ["Fargo", "Bismarck"],
        "Alaska": ["Anchorage", "Fairbanks"],
        "Vermont": ["Burlington", "South Burlington"],
        "Wyoming": ["Cheyenne", "Casper"]
    }
    
    # International locations (limited pool)
    international_locations = {
        "Canada": ["Toronto", "Montreal", "Vancouver", "Calgary", "Edmonton", "Ottawa", "Winnipeg", "Quebec City"],
        "Puerto Rico": ["San Juan"],
        "Mexico": ["Mexico City"],
        "Ireland": ["Dublin"],
        "Scotland": ["Edinburgh"],
        "England": ["London"],
        # One additional location from these countries (will be randomly selected)
        "Brazil": ["São Paulo"],
        "Argentina": ["Buenos Aires"],
        "France": ["Paris"],
        "Spain": ["Madrid"],
        "Italy": ["Rome"]
    }
    
    # Famous (Fictional) Golfers
    famous_golfers = [f"{fake.first_name_male()} {fake.last_name()}" for _ in range(15)]

    # Sponsors (Real financial/corporate sector companies and non-profits)
    sponsors = [
        # Financial Services
        "J.P. Morgan", "Goldman Sachs", "Morgan Stanley", "BlackRock", "Fidelity", "State Street", "Charles Schwab",
        "Bank of America", "Citigroup", "Wells Fargo", "American Express", "Visa", "Mastercard",
        "Berkshire Hathaway", "Blackstone", "KKR", "The Carlyle Group", "Bain Capital",
        # Insurance
        "Prudential", "MetLife", "AIG", "Travelers", "Allstate", "Progressive", "Farmers", "Nationwide", "Liberty Mutual",
        # Professional Services
        "Deloitte", "PwC", "Ernst & Young", "KPMG", "Accenture", "Grant Thornton", "BKD", "Baker Tilly", "BDO", "Baker McKenzie",
        # Non-Profits
        "Red Cross", "United Way", "Salvation Army", "Make-A-Wish", "St. Jude Children's",
        "ACS", "Habitat for Humanity", "BGCA", "YMCA", "Special Olympics", "UNICEF", "Sierra Club"
    ]

    # Event Types
    general_event_types = ["Championship", "Open", "Pro-Am", "Invitational Tournament", "Invitational", "Classic"]
    location_event_types = ["Open", "Invitational", "Classic"]
    
    # Non-profit sponsors (for Pro-Am logic)
    non_profit_sponsors = [
        "Red Cross", "United Way", "Salvation Army", "Make-A-Wish", "St. Jude Children's",
        "ACS", "Habitat for Humanity", "BGCA", "YMCA", "Special Olympics", "UNICEF", "Sierra Club"
    ]

    # Location adjective mappings
    location_adjectives = {
        "Alaska": "Alaskan",
        "Canada": "Canadian", 
        "Ireland": "Irish",
        "Scotland": "Scottish",
        "England": "English",
        "France": "French",
        "Spain": "Spanish",
        "Italy": "Italian",
        "Germany": "German",
        "Mexico": "Mexican",
        "Brazil": "Brazilian",
        "Argentina": "Argentine",
        "Puerto Rico": "Puerto Rican"
    }
    
    # Locations that should use adjective form
    use_adjective_locations = {
        "Alaska", "Canada", "Ireland", "Scotland", "England", "France", 
        "Spain", "Italy", "Germany", "Mexico", "Brazil", "Argentina", "Puerto Rico"
    }
    
    # Vowel-vowel combinations to avoid (location ending in vowel + event type starting with vowel)
    vowel_vowel_avoid = {
        "Alabama": ["Open", "Invitational"],  # Alabama Open/Invitational → Alabama Classic
        "Alaska": ["Open", "Invitational"],   # Alaska Open/Invitational → Alaska Classic  
        "Arizona": ["Open", "Invitational"],
        "California": ["Open", "Invitational"],
        "Colorado": ["Open", "Invitational"],
        "Florida": ["Open", "Invitational"],
        "Georgia": ["Open", "Invitational"],
        "Hawaii": ["Open", "Invitational"],
        "Idaho": ["Open", "Invitational"],
        "Indiana": ["Open", "Invitational"],
        "Iowa": ["Open", "Invitational"],
        "Kansas": ["Open", "Invitational"],
        "Kentucky": ["Open", "Invitational"],
        "Louisiana": ["Open", "Invitational"],
        "Minnesota": ["Open", "Invitational"],
        "Mississippi": ["Open", "Invitational"],
        "Missouri": ["Open", "Invitational"],
        "Montana": ["Open", "Invitational"],
        "Nebraska": ["Open", "Invitational"],
        "Nevada": ["Open", "Invitational"],
        "New Mexico": ["Open", "Invitational"],
        "North Carolina": ["Open", "Invitational"],
        "North Dakota": ["Open", "Invitational"],
        "Ohio": ["Open", "Invitational"],
        "Oklahoma": ["Open", "Invitational"],
        "Oregon": ["Open", "Invitational"],
        "South Carolina": ["Open", "Invitational"],
        "South Dakota": ["Open", "Invitational"],
        "Tennessee": ["Open", "Invitational"],
        "Texas": ["Open", "Invitational"],
        "Utah": ["Open", "Invitational"],
        "Virginia": ["Open", "Invitational"],
        "West Virginia": ["Open", "Invitational"],
        "Wisconsin": ["Open", "Invitational"]
    }

    # --- 4. Generate and Insert Tournaments & Courses one-by-one ---
    print("Generating valid tournaments with PGA Tour-style naming conventions...")
    
    # --- Location Constraint Setup ---
    used_locations = set()
    country_counts = {}
    state_counts = {}
    used_cities = set()  # Track exact city names to prevent duplicates
    used_sponsors = set()  # Track used sponsors to prevent duplicates
    
    # Build available locations from US cities by state
    available_us_locations = []
    for state, cities in us_cities_by_state.items():
        for city in cities:
            available_us_locations.append((city, state))
    
    # Build available international locations (much more limited)
    available_international_locations = []
    
    # Canada gets 2 events max
    for city in international_locations["Canada"]:
        available_international_locations.append((city, "Canada"))
    
    # Only 2 other international locations total
    other_international = ["Ireland", "Scotland"]  # Keep it simple like real PGA Tour
    for country in other_international:
        for city in international_locations[country]:
            available_international_locations.append((city, country))
    
    random.shuffle(available_us_locations)
    random.shuffle(available_international_locations)
    
    start_date = datetime.now().replace(year=2025, month=5, day=26)
    
    NUM_TOURNAMENTS = 30
    us_tournaments = int(NUM_TOURNAMENTS * 0.93)  # 93% US tournaments (like real PGA Tour)
    international_tournaments = NUM_TOURNAMENTS - us_tournaments  # 7% international
    
    print(f"Planning {us_tournaments} US tournaments and {international_tournaments} international tournaments")
    
    # Track used international countries
    used_international_countries = set()
    pro_am_count = 0  # Track number of Pro-Ams created
    
    for i in range(NUM_TOURNAMENTS):
        
        # This loop ensures a valid tournament is created on every iteration
        while True:
            # Determine if this should be a US or international tournament
            if i < us_tournaments:
                # US tournament
                if not available_us_locations:
                    print("Error: No more available US locations. Stopping.")
                    break
                
                selected_location, state = available_us_locations.pop(0)
                
                # Check constraints
                if selected_location in used_cities:
                    continue
                
                # Check state constraints (max 3 for top 5 states, max 1 for others)
                top_5_states = ["California", "Texas", "Florida", "New York", "Pennsylvania"]
                max_per_state = 3 if state in top_5_states else 1
                if state_counts.get(state, 0) >= max_per_state:
                    continue
                
                country = "USA"
                state_counts[state] = state_counts.get(state, 0) + 1
                
            else:
                # International tournament
                if not available_international_locations:
                    print("Error: No more available international locations. Stopping.")
                    break
                
                selected_location, country = available_international_locations.pop(0)
                
                # Check constraints
                if selected_location in used_cities:
                    continue
                
                # Check international constraints
                if country != "Canada" and country in used_international_countries:
                    continue
                
                if country != "Canada":
                    used_international_countries.add(country)
                
                state = country  # For database consistency
            
            # Generate tournament name based on PGA Tour conventions
            # ~20-25% location-based, ~75-80% sponsored (like real PGA Tour)
            name_type = random.choices(['sponsor', 'location', 'golfer'], weights=[0.70, 0.25, 0.05], k=1)[0]
            
            final_tournament_name = ""
            
            if name_type == 'location':
                # Location-based events: use state name for non-top-5 states, city/state for top-5
                top_5_states = ["California", "Texas", "Florida", "New York", "Pennsylvania"]
                if state in top_5_states:
                    # Can use either city or state name
                    location_name = random.choice([selected_location, state])
                else:
                    # Use state name for smaller states
                    location_name = state
                
                # Handle location adjectives
                if location_name in use_adjective_locations:
                    location_name = location_adjectives.get(location_name, location_name)
                
                # Choose event type, avoiding vowel-vowel combinations
                if location_name in vowel_vowel_avoid:
                    # Avoid problematic combinations
                    available_types = [et for et in location_event_types if et not in vowel_vowel_avoid[location_name]]
                    if not available_types:
                        available_types = ["Classic"]  # Fallback
                    event_type = random.choice(available_types)
                else:
                    # 70-80% chance of being called an "Open"
                    if random.random() < 0.75:  # 75% probability
                        event_type = "Open"
                    else:
                        event_type = random.choice(["Invitational", "Classic"])
                
                final_tournament_name = f"{location_name} {event_type}"
            else:
                # Sponsored or golfer events
                if name_type == 'sponsor':
                    # Get available sponsors (not used yet)
                    available_sponsors = [s for s in sponsors if s not in used_sponsors]
                    if not available_sponsors:
                        # If all sponsors used, fall back to location-based
                        name_type = 'location'
                        top_5_states = ["California", "Texas", "Florida", "New York", "Pennsylvania"]
                        if state in top_5_states:
                            location_name = random.choice([selected_location, state])
                        else:
                            location_name = state
                        
                        # Handle location adjectives
                        if location_name in use_adjective_locations:
                            location_name = location_adjectives.get(location_name, location_name)
                        
                        # Choose event type, avoiding vowel-vowel combinations
                        if location_name in vowel_vowel_avoid:
                            available_types = [et for et in location_event_types if et not in vowel_vowel_avoid[location_name]]
                            if not available_types:
                                available_types = ["Classic"]
                            event_type = random.choice(available_types)
                        else:
                            if random.random() < 0.75:
                                event_type = "Open"
                            else:
                                event_type = random.choice(["Invitational", "Classic"])
                        
                        final_tournament_name = f"{location_name} {event_type}"
                    else:
                        prefix = random.choice(available_sponsors)
                        used_sponsors.add(prefix)
                        # Pro-Am only for non-profits AND if we haven't hit the limit
                        if prefix in non_profit_sponsors and pro_am_count < 2:
                            event_type = "Pro-Am"
                            pro_am_count += 1
                        else:
                            event_type = random.choice([et for et in general_event_types if et != "Pro-Am"])
                        final_tournament_name = f"{prefix} {event_type}"
                else:
                    # Golfer events (rare)
                    prefix = random.choice(famous_golfers)
                    event_type = random.choice([et for et in general_event_types if et != "Pro-Am"])
                    final_tournament_name = f"{prefix} {event_type}"

            # Create database entries
            if final_tournament_name and selected_location:
                used_locations.add(selected_location)
                used_cities.add(selected_location)
                country_counts[country] = country_counts.get(country, 0) + 1

                course_name = generate_course_name()
                course_par = random.randint(70, 72)
                
                # For location-based tournaments, use the location name as city
                # For sponsored/golfer tournaments, generate a random city from the same state/country
                if name_type == 'location':
                    city = selected_location
                    state_country = state
                else:
                    # Find a random city from the same state/country for course location
                    if country == "USA":
                        available_cities = us_cities_by_state.get(state, [selected_location])
                        city = random.choice(available_cities)
                        state_country = state
                    else:
                        # For international, use the selected location
                        city = selected_location
                        state_country = country
                
                c.execute(
                    'INSERT INTO courses (name, type, par, difficulty, city, state_country) VALUES (?, ?, ?, ?, ?, ?)',
                    (course_name, 'Fictional', course_par, round(random.uniform(0.8, 1.2), 2), city, state_country)
                )
                course_id = c.lastrowid
                
                holes, total_par = [], 0
                for hole_num in range(1, 18):
                    par = random.choice([3, 4, 5])
                    holes.append((course_id, hole_num, par, round(random.uniform(0.8, 1.2), 2)))
                    total_par += par
                last_hole_par = max(3, min(5, course_par - total_par))
                holes.append((course_id, 18, last_hole_par, round(random.uniform(0.8, 1.2), 2)))
                c.executemany('INSERT INTO holes (course_id, hole_number, par, difficulty_modifier) VALUES (?, ?, ?, ?)', holes)

                event_start_date = start_date + timedelta(days=(i * 10))
                c.execute(
                    'INSERT INTO tournaments (name, course_id, start_date, end_date, purse, status, current_round, cut_applied) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                    (final_tournament_name, course_id, event_start_date, event_start_date + timedelta(days=4), random.uniform(5.0, 15.0), 'pending', 1, 0)
                )
                
                print(f"  - Created: {final_tournament_name} at {course_name} ({city}, {state_country})")
                
                break

    # --- 5. Assign Players to all Tournaments ---
    all_player_ids = [row[0] for row in c.execute('SELECT id FROM players').fetchall()]
    all_tournament_ids = [row[0] for row in c.execute('SELECT id FROM tournaments').fetchall()]

    for tournament_id in all_tournament_ids:
        tournament_players, group_num = [], 1
        player_ids_for_grouping = all_player_ids.copy()
        random.shuffle(player_ids_for_grouping)
        
        for i in range(0, len(player_ids_for_grouping), 3):
            for player_id in player_ids_for_grouping[i:i+3]:
                tournament_players.append((tournament_id, player_id, 'active', group_num))
            group_num += 1
            
        c.executemany('INSERT INTO tournament_players (tournament_id, player_id, status, tee_group) VALUES (?, ?, ?, ?)', tournament_players)

    print(f"Assigned all {len(all_player_ids)} players to {len(all_tournament_ids)} tournaments.")

    conn.commit()
    conn.close()
    print("Database seeding complete.")

if __name__ == '__main__':
    # Initialize the database (creates tables)
    init_db()
    # Seed the database with data
    seed_database()