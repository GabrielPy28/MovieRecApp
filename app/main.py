from app.functions import recommend_movies_by_preference
import argparse

def main():
    # Configure command line arguments
    parser = argparse.ArgumentParser(description="Movie Recommendation System")
    parser.add_argument('--genres', nargs='+', default=None,
                       help="List of preferred genres (max 5)")
    parser.add_argument('--directors', nargs='+', default=None,
                       help="List of favorite directors (max 3)")
    parser.add_argument('--num', type=int, default=10,
                       help="Number of recommendations")
    
    args = parser.parse_args()

    # If genres or directors are not provided, ask the user
    if not args.genres:
        user_genres = input("Enter your favorite genres separated by comma (max 5): ")
        args.genres = [g.strip() for g in user_genres.split(',')][:5]
    if not args.directors:
        user_directors = input("Enter your favorite directors separated by comma (max 3): ")
        args.directors = [d.strip() for d in user_directors.split(',')][:3]

    print("\n=== Movie Recommendation System ===")
    print(f"Genres: {args.genres}")
    print(f"Directors: {args.directors}")
    print(f"Number of recommendations: {args.num}\n")
    
    # Get recommendations
    recommendations = recommend_movies_by_preference(
        args.genres,
        args.directors,
        args.num
    )
    
    # Show results
    if not recommendations:
        print("No movies matching your preferences were found.")
    else:
        print("\n=== Recommended Movies ===")
        for i, movie in enumerate(recommendations, 1):
            print(f"\n{i}. {movie.get('movie_title', 'Title not available')}")
            print(f"   Director: {movie.get('directors', 'Unknown')}")
            print(f"   Genres: {movie.get('genres', 'Unknown')}")
            if 'tomatometer_rating' in movie:
                print(f"   Tomatometer: {movie['tomatometer_rating']}%")
            if 'rating_score' in movie:
                print(f"   Critic score: {round(movie['rating_score']*10,2)}/10")

if __name__ == "__main__":
    main()