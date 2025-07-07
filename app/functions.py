from pyspark.sql import SparkSession
from pyspark.sql.functions import regexp_extract, when, col, avg, lit, row_number, rand, count, log10
from pyspark.sql.functions import udf
from pyspark.sql.types import BooleanType, FloatType
from pyspark.sql.window import Window
import re
from typing import List, Dict, Optional
from pyspark.sql.types import FloatType
import hashlib

# Singleton for SparkSession
def get_spark_session() -> SparkSession:
    """Gets or creates a SparkSession."""
    return SparkSession.builder \
        .appName("MovieRecommendationEngine") \
        .config("spark.executor.memory", "2g") \
        .config("spark.driver.memory", "1g") \
        .getOrCreate()

def normalize_text(text: str) -> str:
    """Normalizes text for comparison."""
    return re.sub(r'[^a-zA-Z]', '', text).lower() if text else ""


def recommend_movies_by_preference(
    genres: List[str],
    directors: List[str],
    num_recommendations: int = 10,
    user_id: Optional[str] = None,
    diversity_factor: float = 0.3
) -> List[Dict]:
    """
    Recommends movies based on favorite genres and directors with enhanced diversity.
    
    Args:
        genres: List of preferred genres (max. 5)
        directors: List of favorite directors (max. 3)
        num_recommendations: Maximum number of recommendations
        user_id: Optional user ID for personalization
        diversity_factor: Diversity factor (0-1) to mix recommendations
        
    Returns:
        List of dictionaries with information about recommended movies
    """
    try:
        # Input validation and normalization
        if not genres and not directors:
            raise ValueError("You must provide at least one genre or director")
            
        genres = [g.strip() for g in genres][:5] if genres else []
        directors = [d.strip() for d in directors][:3] if directors else []
        
        spark = get_spark_session()
        
        # Read movies dataset
        try:
            movies_df = spark.read.csv(
                './app/dataset/movies.csv',
                header=True,
                inferSchema=True,
                escape='"'
            ).dropDuplicates(['movie_title'])  # Remove duplicates by title
        except Exception as e:
            print(f"Error reading movies.csv file: {str(e)}")
            return []
        
        # Check required columns
        required_columns = {'movie_title', 'genres', 'directors'}
        if not required_columns.issubset(movies_df.columns):
            missing = required_columns - set(movies_df.columns)
            print(f"Error: Missing required columns: {missing}")
            return []
        
        # Normalize genres for comparison
        user_genres = [normalize_text(g) for g in genres]
        
        # UDF to filter by genres
        def contains_gender(movie_genres: str) -> bool:
            if not movie_genres:
                return False
            genres_mov = [normalize_text(g) for g in movie_genres.split(',')]
            return any(g in genres_mov for g in user_genres)
        
        contains_gender_udf = udf(contains_gender, BooleanType())
        
        # Apply initial filters
        filtered_df = movies_df
        
        if user_genres:
            filtered_df = filtered_df.filter(contains_gender_udf(col("genres")))
        
        if directors:
            filtered_df = filtered_df.filter(col("directors").isin(directors))
        
        # Process critic reviews if available
        try:
            reviews_df = spark.read.csv(
                './app/dataset/critic_reviews.csv', 
                header=True, 
                inferSchema=True, 
                escape='"'
            ).dropDuplicates()
        except Exception as e:
            print(f"Error reading critic_reviews.csv: {str(e)}")
            reviews_df = None

        # Improved scoring system
        if reviews_df and 'rotten_tomatoes_link' in reviews_df.columns and 'review_score' in reviews_df.columns:
            def parse_review_score(score):
                if not score or not isinstance(score, str):
                    return None
                score = score.strip()
                if "/" in score:
                    try:
                        num, denom = score.split("/")
                        return float(num) / float(denom) * 10
                    except:
                        return None
                letter_map = {"A": 9.5, "A-": 9.0, "B+": 8.5, "B": 8.0, 
                             "B-": 7.5, "C+": 7.0, "C": 6.5, "C-": 6.0, 
                             "D+": 5.5, "D": 5.0, "D-": 4.5, "F": 3.0}
                if score in letter_map:
                    return letter_map[score]
                try:
                    return float(score)
                except:
                    return None
            
            parse_review_score_udf = udf(parse_review_score, FloatType())
            reviews_df = reviews_df.withColumn('review_score_num', parse_review_score_udf(col('review_score')))
            
            avg_reviews = reviews_df.groupBy('rotten_tomatoes_link').agg(
                avg('review_score_num').alias('avg_review_score'),
                count('review_score_num').alias('review_count')
            )
            
            if 'rotten_tomatoes_link' in movies_df.columns:
                filtered_df = filtered_df.join(avg_reviews, on='rotten_tomatoes_link', how='left')
                filtered_df = filtered_df.withColumn(
                    'rating_score',
                    when(
                        col('avg_review_score').isNotNull(), 
                        (col('avg_review_score')/10) * (1 + log10(col('review_count') + 1))
                    ).otherwise(lit(0.5))
                )
            else:
                filtered_df = filtered_df.withColumn('rating_score', lit(0.5))
        else:
            filtered_df = filtered_df.withColumn('rating_score', lit(0.5))
        
        # Add diversity to recommendations
        window_spec = Window.orderBy(col("rating_score").desc())
        
        # Mix controlled randomness based on user_id for consistency
        if user_id:
            seed = int(hashlib.md5(user_id.encode()).hexdigest(), 16) % (2**32)
            filtered_df = filtered_df.withColumn("random_factor", rand(seed))
        else:
            filtered_df = filtered_df.withColumn("random_factor", rand())
        
        # Combine score with diversity factor
        filtered_df = filtered_df.withColumn(
            "combined_score",
            (1 - diversity_factor) * col("rating_score") + diversity_factor * col("random_factor")
        )
        
        # Select movies avoiding duplicates and with diversity
        recommended_movies = filtered_df.orderBy(col("combined_score").desc()) \
                                      .limit(num_recommendations * 3)  # Take more for final selection
                                      
        # Group by director and genre for diversity
        window_director = Window.partitionBy("directors").orderBy(col("combined_score").desc())
        window_genre = Window.partitionBy("genres").orderBy(col("combined_score").desc())
        
        recommended_movies = recommended_movies \
            .withColumn("rank_director", row_number().over(window_director)) \
            .withColumn("rank_genre", row_number().over(window_genre)) \
            .orderBy(col("rank_director"), col("rank_genre")) \
            .limit(num_recommendations)
        
        # Convert to output format
        result = recommended_movies.toPandas().to_dict(orient='records')
        
        return result
        
    except Exception as e:
        print(f"Error generating recommendations: {str(e)}")
        return []

# Example usage:
# recommendations = recomendar_peliculas_por_preferencia([
#     'Action', 'Comedy'
# ], [
#     'Christopher Nolan'
# ], num_recommendations=10)
# print(recommendations)
