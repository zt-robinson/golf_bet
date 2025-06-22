# Course Characteristics System

## Overview

The golf simulator now includes a comprehensive course characteristics system that makes each course unique and affects player performance in realistic ways. Each course has 15 different characteristics that interact with player skills to create more dynamic and strategic gameplay.

## Course Characteristics

### Weather Conditions (0.0 = mild, 1.0 = extreme)

1. **Average Temperature** (50-95°F, normalized to 0-1)
   - Extreme temperatures (hot or cold) affect player stamina and performance
   - Influenced by geographic location

2. **Humidity Level** (0.0 = dry, 1.0 = very humid)
   - High humidity makes conditions more challenging
   - Influenced by coastal vs. desert locations

3. **Wind Factor** (0.0 = calm, 1.0 = very windy)
   - Wind affects all shots and makes course more difficult
   - Influenced by location (e.g., Chicago, Dallas) and course type (links courses)

4. **Rain Probability** (0.0 = no rain, 1.0 = heavy rain)
   - Rain makes course conditions more challenging
   - Influenced by geographic location (e.g., Seattle, Portland)

### Course Design and Strategy

5. **Design Strategy** (0.0 = strategic/forgiving, 1.0 = penal/demanding)
   - Penal courses favor accuracy over distance
   - Strategic courses are more forgiving and reward smart play
   - Influenced by course name and type

6. **Course Length** (0.0 = short, 1.0 = very long)
   - Longer courses favor players with strong driving distance
   - Influenced by course type (championship vs. executive courses)

7. **Narrowness Factor** (0.0 = wide fairways, 1.0 = very narrow)
   - Narrow courses favor accuracy over distance
   - Influenced by design strategy

8. **Hazard Density** (0.0 = few hazards, 1.0 = many hazards)
   - More hazards make the course more challenging
   - Influenced by design strategy and course type

### Course Conditions

9. **Green Speed** (0.0 = slow, 1.0 = very fast)
   - Fast greens favor putting skill
   - Slow greens challenge putting skill
   - Influenced by prestige and maintenance level

10. **Turf Firmness** (0.0 = soft, 1.0 = very firm)
    - Firm turf affects approach shots and ball roll
    - Influenced by climate and maintenance

11. **Rough Length** (0.0 = short rough, 1.0 = very long rough)
    - Longer rough affects all shots and makes recovery more difficult
    - Influenced by course type and maintenance

### Mental Factors

12. **Prestige Level** (0.0 = local course, 1.0 = major championship venue)
    - Higher prestige adds mental pressure
    - Influenced by course name and type

13. **Course Age** (0.0 = new course, 1.0 = historic course)
    - Historic courses can be intimidating
    - Influenced by course name and type

14. **Crowd Factor** (0.0 = small crowds, 1.0 = major tournament crowds)
    - Larger crowds add pressure and affect performance
    - Influenced by prestige level

### Physical Factors

15. **Elevation Factor** (0.0 = sea level, 1.0 = high altitude)
    - High elevation affects distance and stamina
    - Influenced by geographic location

16. **Terrain Difficulty** (0.0 = flat, 1.0 = very hilly)
    - Hilly courses are more physically demanding
    - Influenced by location and course type

## How Characteristics Affect Player Performance

### Skill Interactions

- **Driving Skill**: Affected by course length, narrowness, wind, and elevation
- **Approach Skill**: Affected by design strategy, turf firmness, and hazard density
- **Short Game Skill**: Affected by rough length, design strategy, and hazard density
- **Putting Skill**: Affected by green speed and mental factors
- **Overall Skill**: Base performance affected by all factors

### Weather Effects

- **Temperature**: Extreme temperatures reduce performance
- **Humidity**: High humidity makes conditions more challenging
- **Wind**: Wind affects all shots and increases difficulty
- **Rain**: Rain makes course conditions more difficult

### Design Effects

- **Penal Courses**: Favor accuracy over distance, penalize mistakes heavily
- **Strategic Courses**: More forgiving, reward smart play
- **Long Courses**: Favor driving distance
- **Narrow Courses**: Favor driving accuracy

### Mental Effects

- **Prestige**: Higher prestige courses add pressure
- **Crowds**: Larger crowds increase pressure
- **History**: Historic courses can be intimidating

### Physical Effects

- **Elevation**: High elevation affects distance and stamina
- **Terrain**: Hilly courses are more physically demanding

## Implementation

### Database Schema

Course characteristics are stored in a new `course_characteristics` table with a foreign key relationship to the `courses` table.

### Generation

Characteristics are automatically generated when courses are created, based on:
- Course name and type
- Geographic location (city, state/country)
- Realistic golf course patterns

### Simulation Integration

The simulation service now incorporates course characteristics when calculating player scores, making each tournament unique and challenging in different ways.

## Testing

Run the test script to see how course characteristics affect different player types:

```bash
python test_course_characteristics.py
```

This will show:
- Sample course characteristics
- How different player skill profiles perform on the same course
- Analysis of which course factors most affected each player

## Future Enhancements

Potential improvements to the system:
- Dynamic weather changes during tournaments
- Course condition changes between rounds
- Player-specific course preferences
- Historical performance data on specific course types
- Course-specific strategies and shot selection 