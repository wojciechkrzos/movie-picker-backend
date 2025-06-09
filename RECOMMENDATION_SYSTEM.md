# Movie Recommendation System Documentation

## Overview

The Movie Picker backend now includes a sophisticated recommendation system that provides personalized movie suggestions based on:

1. **User's Streaming Services** - Only shows movies available on services the user subscribes to
2. **Quiz Answers** - Maps user preferences from quiz responses to movie categories
3. **Watch History** - Excludes already watched films and learns from user ratings
4. **User Review Patterns** - Recommends similar content to highly-rated films

## Key Features

### ✅ Smart Filtering
- **Streaming Service Integration**: Only recommends films available on user's streaming platforms
- **Watched Film Exclusion**: Never shows films the user has already seen
- **Preference Learning**: Analyzes user's high ratings (4+ stars) to understand preferences

### ✅ Quiz-Based Recommendations
The system maps quiz answers to movie categories:

#### Mood-Based Mapping:
- **"Energetic"** → Action, Adventure, Thriller
- **"Bored"** → Comedy, Action, Adventure  
- **"Chill"** → Romance, Drama, Documentary
- **"Jittery"** → Horror, Thriller, Mystery

#### Preference-Based Mapping:
- **"Action-packed"** → Action, Adventure, Thriller
- **"Emotional"** → Drama, Romance
- **"Mind-bending"** → Science Fiction, Thriller, Mystery
- **"Light-hearted"** → Comedy, Animation, Romance

#### Context-Based Mapping:
- **"Alone for focus"** → Drama, Documentary, Thriller
- **"With friends for fun"** → Comedy, Action, Horror
- **"Date night romance"** → Romance, Comedy
- **"Family time"** → Animation, Adventure, Comedy

#### Visual/Creative Preferences:
- **"Amazing visuals"** → Science Fiction, Fantasy, Action, Animation
- **"Great storyline"** → Drama, Mystery, Thriller
- **"Favorite actors"** → Enhanced actor-based scoring
- **"Director's reputation"** → Enhanced director-based scoring

### ✅ Advanced Scoring Algorithm

The recommendation engine calculates scores based on:

1. **Category Matching** (10x weight): Quiz preferences mapped to film categories
2. **Review History** (15x weight): Categories from user's highly-rated films
3. **Actor Preferences** (20x weight): Actors from user's favorite films
4. **Director Preferences** (25x weight): Directors from user's favorite films
5. **Time Period Preferences**: Based on quiz answers about preferred movie eras
6. **Randomization**: Ensures variety in recommendations
7. **Recency Boost**: Slight preference for newer content

### ✅ Enhanced Quiz Questions

The system now includes 6 comprehensive questions:

1. **"What's your mood today?"**
   - Energetic, Bored, Chill, Jittery

2. **"What type of movie do you prefer?"**
   - Action-packed, Emotional, Mind-bending, Light-hearted

3. **"What's your favorite time period for movies?"**
   - Classic (before 1980), Retro (1980-2000), Modern (2000-2015), Recent (2015+)

4. **"How do you prefer to watch movies?"**
   - Alone for focus, With friends for fun, Date night romance, Family time

5. **"What movie length do you prefer?"**
   - Short and sweet (under 90 min), Standard length (90-120 min), Epic length (over 2 hours), No preference

6. **"What draws you to a movie most?"**
   - Amazing visuals, Great storyline, Favorite actors, Director's reputation

## API Endpoints

### GET `/api/v1/movie/recommendations/`
**Authentication Required**: Yes

**Response Example**:
```json
{
    "message": "Recommendations based on your 2 streaming services and preferences",
    "streaming_services": ["Netflix", "Hulu"],
    "recommendations": [
        {
            "id": 1,
            "title": "Movie Title",
            "release_date": "2023-01-01",
            "language": "en",
            "poster_url": "https://image.tmdb.org/...",
            "tmdb_id": 12345
        }
        // ... up to 20 recommendations
    ]
}
```

**Error Cases**:
- No streaming services selected: Returns empty recommendations with message
- No quiz answers: Still works but with basic recommendations
- No available films: Returns empty list

## Testing

The system includes comprehensive tests via `test_recommendations.py`:

```bash
cd movie_picker
python test_recommendations.py
```

**Test Coverage**:
- ✅ User creation and data setup
- ✅ Streaming service association
- ✅ Quiz answer creation
- ✅ Watched film exclusion
- ✅ Recommendation scoring
- ✅ User statistics calculation

## Database Seeding

### Add Quiz Questions:
```bash
python manage.py db_seed --questions
```

### Add Movies and Streaming Providers:
```bash
python manage.py db_seed --popular --pages 5 --providers
```

## Architecture

### Models Used:
- **User** (authentication): User profiles and preferences
- **Film** (movie): Movie data with relationships
- **StreamingService** (movie): Available streaming platforms  
- **WatchedFilm** (movie): User's viewing history with ratings
- **Category** (movie): Movie genres/categories
- **Answer** (authentication): User's quiz responses
- **Question** (authentication): Quiz questions

### Key Relationships:
- User ↔ StreamingService (many-to-many)
- User ↔ WatchedFilm ↔ Film (user's viewing history)
- User ↔ Answer ↔ Question (quiz responses)
- Film ↔ Category (movie genres)
- Film ↔ StreamingService (availability)

## Performance Considerations

- **Efficient Queries**: Uses `select_related()` and `prefetch_related()` to minimize database hits
- **Smart Caching**: Quiz answers are fetched once per recommendation request
- **Optimized Scoring**: Recommendation algorithm runs in-memory after initial query
- **Limited Results**: Returns maximum 20 recommendations to ensure fast response times

## Future Enhancements

1. **Machine Learning Integration**: Could implement collaborative filtering
2. **Real-time Preferences**: Update recommendations based on viewing behavior
3. **Social Features**: Recommendations based on friends' preferences
4. **Advanced Filters**: Genre mixing, release year preferences, runtime filters
5. **Seasonal Recommendations**: Holiday-themed or seasonal content suggestions
6. **Diversity Scoring**: Ensure recommendations span different genres and eras

## Usage Example

1. User completes onboarding quiz
2. User selects streaming services
3. User watches and rates some films
4. System generates personalized recommendations
5. Recommendations improve over time as user provides more ratings

The system is designed to work immediately after setup and continuously improve as users interact with the platform.
