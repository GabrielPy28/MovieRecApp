# Movie Recommendation System

This is a command-line Movie Recommendation System built with Python. It suggests movies based on your preferred genres and favorite directors, using a dataset of movies and critic reviews.

## Important Note
Before running the code, please download the necessary dataset files from Kaggle:

- **Critic Reviews**: [critic_reviews.csv](https://www.kaggle.com/datasets/stefanoleone992/rotten-tomatoes-movies-and-critic-reviews-dataset?select=rotten_tomatoes_critic_reviews.csv)
- **Movies**: [movies.csv](https://www.kaggle.com/datasets/stefanoleone992/rotten-tomatoes-movies-and-critic-reviews-dataset?select=rotten_tomatoes_movies.csv)

Make sure to rename the files to `critic_reviews.csv` and `movies.csv` respectively, and place them in the `app/dataset/` folder.

## Features
- Get movie recommendations based on up to 5 genres and 3 directors.
- Specify the number of recommendations you want.
- Uses critic reviews and movie metadata for better suggestions.

## Requirements
- Python 3.7+
- See `requirements.txt` for required Python packages.

## Datasets
- `app/dataset/movies.csv`: Movie metadata (title, genres, directors, etc.)
- `app/dataset/critic_reviews.csv`: Critic reviews and ratings

## Usage
You can run the application from the command line:

```bash
python -m app.main --genres Action Comedy --directors "Steven Spielberg" --num 5
```

- `--genres`: List of your favorite genres (max 5)
- `--directors`: List of your favorite directors (max 3)
- `--num`: Number of movie recommendations to display (default: 10)

If you do not provide genres or directors as arguments, the program will prompt you to enter them interactively.

## Example
```
$ python -m app.main --genres Drama Thriller --directors "Christopher Nolan" --num 3

=== Movie Recommendation System ===
Genres: ['Drama', 'Thriller']
Directors: ['Christopher Nolan']
Number of recommendations: 3

=== Recommended Movies ===
1. Inception
   Director: Christopher Nolan
   Genres: Action, Thriller, Sci-Fi
   Tomatometer: 87%
   Critic score: 9.1/10
...
```

## Docker
A `Dockerfile` is provided for containerized deployment. Build and run with:

```bash
docker build -t movierec .
docker run --rm -it movierec
```

> [!TIP]
> You can also use the pre-built image of my project published on [Docker Hub](https://hub.docker.com/r/gabrielpy77/movie-rec-app):
```
docker pull gabrielpy77/movie-rec-app:latest
```

## License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more details.
