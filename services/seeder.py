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
        "Country Club", "Golf Club", "Hunt Club", "Club", "National Golf Club", "Athletic Club", "Cricket Club",
        "Links", "Golf Links", "Resort", "Golf Resort", "Golf Course", "Golf & Hunt Club", "Golf & Tennis Club"
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
    
    # Optionally add an organization
    if random.random() < 0.6: # 60% chance to add an organization
        # Some patterns are complex and already include an organization in the example
        if base_name in [p6, p7, p8]:
             if random.random() < 0.3: # Lower chance for already complex names
                return f"{base_name} {random.choice(organizations)}"
        else:
            return f"{base_name} {random.choice(organizations)}"

    return base_name

def seed_database():
    """Populate the database with fictional data based on the new simulation model."""
    fake = Faker()
    conn = get_db_connection()
    c = conn.cursor()

    print("Seeding database with new simulation data...")

    # --- 1. Create Players ---
    countries = ['USA', 'England', 'Australia', 'Canada', 'Sweden', 'Spain', 'South Africa', 'Japan', 'South Korea', 'Ireland']
    players = []
    for _ in range(150):
        # Generate male names only, without professional titles
        first_name = fake.first_name_male()
        last_name = fake.last_name()
        full_name = f"{first_name} {last_name}"
        
        players.append((
            full_name,
            random.choice(countries),
            round(random.uniform(70, 98), 2),  # overall_skill
            round(random.uniform(70, 98), 2)   # consistency
        ))
    c.executemany('''
        INSERT INTO players (name, country, overall_skill, consistency)
        VALUES (?, ?, ?, ?)
    ''', players)
    print(f"✅ Created {len(players)} players.")

    # --- 2. Create Courses and Holes based on User-defined Guardrails ---
    # Generate unique course names
    course_names = []
    for _ in range(10):
        name = generate_course_name()
        while name in course_names:  # Ensure uniqueness
            name = generate_course_name()
        course_names.append(name)
    
    for course_name in course_names:
        # Define course personality
        architecture = random.choice(['Penal', 'Strategic'])
        green_speed = round(random.uniform(0.9, 1.1), 2)
        rough_height = round(random.uniform(0.9, 1.1), 2)
        
        c.execute('''
            INSERT INTO courses (name, architecture_style, green_speed, rough_height)
            VALUES (?, ?, ?, ?)
        ''', (course_name, architecture, green_speed, rough_height))
        
        course_id = c.lastrowid
        
        # --- Generate Course Layout using Guardrails ---
        target_par = random.randint(70, 72)
        num_par_4s = random.randint(12, 14)
        
        # Ensure at least one par 3 and one par 5
        hole_pars = [4] * num_par_4s
        hole_pars.append(3)
        hole_pars.append(5)
        
        # Fill remaining holes to meet target par
        remaining_holes = 18 - len(hole_pars)
        current_par_sum = sum(hole_pars)
        
        for _ in range(remaining_holes):
            par_needed = target_par - current_par_sum
            # Decide whether to add a 3, 4, or 5 to get closer to the target
            if par_needed >= 5 and len(hole_pars) < 18:
                hole_pars.append(5)
            elif par_needed >= 4 and len(hole_pars) < 18:
                hole_pars.append(4)
            else:
                hole_pars.append(3)
            current_par_sum = sum(hole_pars)

        # If par is still off, adjust last few holes (a simple method to get closer)
        while sum(hole_pars) != target_par and len(hole_pars) == 18:
            diff = sum(hole_pars) - target_par
            # find a hole to safely increment or decrement
            idx_to_change = random.randint(0, 17)
            if diff > 0 and hole_pars[idx_to_change] > 3:
                hole_pars[idx_to_change] -= 1
            elif diff < 0 and hole_pars[idx_to_change] < 5:
                hole_pars[idx_to_change] += 1
            else:
                # Break if we're stuck in a loop
                break

        random.shuffle(hole_pars)
        
        # Insert the 18 holes
        for i, par in enumerate(hole_pars, 1):
            difficulty = round(random.uniform(0.8, 1.2), 2)
            c.execute('INSERT INTO holes (course_id, hole_number, par, difficulty_modifier) VALUES (?, ?, ?, ?)',
                      (course_id, i, par, difficulty))

    print(f"✅ Created {len(course_names)} courses, each with 18 holes.")

    # --- 3. Create a Season of Tournaments ---
    tournament_adjectives = ["Open", "Classic", "Invitational", "Championship", "Masters", "Cup"]
    all_course_ids = [row['id'] for row in c.execute('SELECT id FROM courses').fetchall()]
    tournaments = []
    for i in range(20):
        course_id = random.choice(all_course_ids)
        tournament_name = f"{fake.city()} {random.choice(tournament_adjectives)}"
        # Stagger start dates
        start_date = datetime.now() + timedelta(days=i*10)
        end_date = start_date + timedelta(days=4)
        tournaments.append((tournament_name, course_id, start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")))

    c.executemany('INSERT INTO tournaments (name, course_id, start_date, end_date) VALUES (?, ?, ?, ?)', tournaments)
    print(f"✅ Created {len(tournaments)} tournaments.")

    conn.commit()
    conn.close()
    print("\nDatabase seeding complete!")

if __name__ == '__main__':
    init_db()
    seed_database() 