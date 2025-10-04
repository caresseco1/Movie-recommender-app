import pandas as pd
import numpy as np
import os
import requests
import time
from ast import literal_eval
import warnings
from config import TMDB_API_KEY, TMDB_BASE_URL, TMDB_IMAGE_BASE_URL, DATA_RAW_PATH, DATA_PROCESSED_PATH

warnings.filterwarnings('ignore')

class TMDBAPI:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = TMDB_BASE_URL
        
    def get_trending_movies(self, time_window='week'):
        """Get currently trending movies from TMDB"""
        url = f"{self.base_url}/trending/movie/{time_window}"
        params = {'api_key': self.api_key}
        
        try:
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                return response.json()['results']
            else:
                print(f"TMDB API Error: {response.status_code}")
                return []
        except Exception as e:
            print(f"TMDB API call failed: {e}")
            return []
    
    def get_movie_details(self, movie_id):
        """Get detailed information for a specific movie"""
        url = f"{self.base_url}/movie/{movie_id}"
        params = {
            'api_key': self.api_key,
            'append_to_response': 'credits,keywords'
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                return None
        except:
            return None
    
    def search_movies(self, query, year=None):
        """Search for movies by title"""
        url = f"{self.base_url}/search/movie"
        params = {
            'api_key': self.api_key,
            'query': query,
            'page': 1
        }
        if year:
            params['year'] = year
            
        try:
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                return response.json()['results']
            else:
                return []
        except:
            return []

class MovieDataPreprocessor:
    def __init__(self):
        self.data_path = DATA_RAW_PATH
        self.output_path = DATA_PROCESSED_PATH
        self.tmdb = TMDBAPI(TMDB_API_KEY)
        
    def enhance_with_tmdb_trending(self, existing_movie_ids, max_trending=50):
        """Add currently trending movies from TMDB that aren't in our dataset"""
        print("🎬 Fetching trending movies from TMDB...")
        
        trending_movies = self.tmdb.get_trending_movies()
        new_movies = []
        
        for movie in trending_movies[:max_trending]:
            tmdb_id = movie['id']
            
            # Skip if already in our dataset
            if tmdb_id in existing_movie_ids:
                continue
                
            # Get full movie details
            movie_details = self.tmdb.get_movie_details(tmdb_id)
            if movie_details:
                processed_movie = self.process_tmdb_movie(movie_details)
                if processed_movie:
                    new_movies.append(processed_movie)
            
            # Rate limiting
            time.sleep(0.1)
        
        print(f"   Added {len(new_movies)} new trending movies")
        return new_movies
    
    def process_tmdb_movie(self, movie_data):
        """Process TMDB movie data to match our schema"""
        try:
            # Extract basic info
            movie = {
                'id': movie_data['id'],
                'title': movie_data.get('title', ''),
                'overview': movie_data.get('overview', ''),
                'poster_path': movie_data.get('poster_path', ''),
                'release_date': movie_data.get('release_date', ''),
                'runtime': movie_data.get('runtime', 0),
                'vote_average': movie_data.get('vote_average', 0),
                'vote_count': movie_data.get('vote_count', 0),
                'popularity': movie_data.get('popularity', 0),
                'genres': [genre['name'] for genre in movie_data.get('genres', [])],
                'production_companies': [company['name'] for company in movie_data.get('production_companies', [])]
            }
            
            # Extract release year
            if movie['release_date']:
                movie['release_year'] = pd.to_datetime(movie['release_date']).year
            else:
                movie['release_year'] = None
            
            # Extract cast and director from credits
            if 'credits' in movie_data:
                credits = movie_data['credits']
                # Top 5 cast members
                movie['cast'] = [actor['name'] for actor in credits.get('cast', [])[:5]]
                # Director
                directors = [crew['name'] for crew in credits.get('crew', []) if crew.get('job') == 'Director']
                movie['director'] = directors[0] if directors else None
            else:
                movie['cast'] = []
                movie['director'] = None
            
            # Extract keywords
            if 'keywords' in movie_data:
                movie['keywords'] = [kw['name'] for kw in movie_data['keywords'].get('keywords', [])]
            else:
                movie['keywords'] = []
            
            return movie
            
        except Exception as e:
            print(f"Error processing TMDB movie {movie_data.get('id')}: {e}")
            return None
    
    def fill_missing_posters(self, movies_df):
        """Fill missing poster paths using TMDB"""
        print("🖼️ Filling missing posters from TMDB...")
        
        missing_posters = movies_df[movies_df['poster_path'].isna() | (movies_df['poster_path'] == '')]
        print(f"   Found {len(missing_posters)} movies with missing posters")
        
        updated_count = 0
        for idx, movie in missing_posters.iterrows():
            if pd.notna(movie['id']):
                movie_details = self.tmdb.get_movie_details(int(movie['id']))
                if movie_details and movie_details.get('poster_path'):
                    movies_df.at[idx, 'poster_path'] = movie_details['poster_path']
                    updated_count += 1
                
                # Rate limiting
                time.sleep(0.1)
        
        print(f"   Updated {updated_count} missing posters")
        return movies_df
    
    def get_current_trending_ids(self):
        """Get IDs of currently trending movies for recommendations"""
        print("🔥 Getting current trending movie IDs...")
        
        trending_movies = self.tmdb.get_trending_movies()
        trending_ids = [movie['id'] for movie in trending_movies]
        
        print(f"   Found {len(trending_ids)} trending movies")
        return trending_ids
    
    def create_master_dataset(self):
        """Create the final merged dataset with TMDB enhancement"""
        print("🔄 Creating master dataset with TMDB integration...")
        
        # Load all local data
        ratings, movielens_movies, links, tags = self.load_movielens_data()
        movies_meta, credits, keywords = self.load_movies_metadata()
        
        # Clean and process local data
        movies_meta_clean = self.clean_movies_metadata(movies_meta)
        credits_clean = self.process_credits(credits)
        keywords_clean = self.process_keywords(keywords)
        
        # Merge local datasets
        print("🔗 Merging local datasets...")
        movies_merged = movies_meta_clean.merge(credits_clean, on='id', how='left')
        movies_merged = movies_merged.merge(keywords_clean, on='id', how='left')
        
        # Merge with MovieLens links
        links['tmdbId'] = pd.to_numeric(links['tmdbId'], errors='coerce')
        links_clean = links.dropna(subset=['tmdbId'])
        links_clean['tmdbId'] = links_clean['tmdbId'].astype(int)
        
        movies_final = movies_merged.merge(
            links_clean[['movieId', 'tmdbId']], 
            left_on='id', 
            right_on='tmdbId', 
            how='inner'
        )
        
        # ENHANCE WITH TMDB DATA
        print("🎬 Enhancing with TMDB data...")
        
        # 1. Add trending movies not in dataset
        existing_ids = set(movies_final['id'].tolist())
        new_trending_movies = self.enhance_with_tmdb_trending(existing_ids)
        
        if new_trending_movies:
            trending_df = pd.DataFrame(new_trending_movies)
            # Create synthetic movieId for new movies (negative IDs to avoid conflicts)
            trending_df['movieId'] = [-i for i in range(1, len(trending_df) + 1)]
            trending_df['tmdbId'] = trending_df['id']
            
            # Combine with existing movies
            movies_final = pd.concat([movies_final, trending_df], ignore_index=True)
        
        # 2. Fill missing posters
        movies_final = self.fill_missing_posters(movies_final)
        
        # 3. Get current trending IDs for recommendation context
        trending_ids = self.get_current_trending_ids()
        
        # Prepare ratings data
        print("📈 Preparing ratings data...")
        ratings_clean = ratings[ratings['movieId'].isin(movies_final['movieId'])]
        
        # Save processed data
        print("💾 Saving processed data...")
        os.makedirs(self.output_path, exist_ok=True)
        
        movies_final.to_csv(f"{self.output_path}movies_final.csv", index=False)
        ratings_clean.to_csv(f"{self.output_path}ratings_clean.csv", index=False)
        
        # Save trending IDs for context-aware recommendations
        pd.DataFrame({'trending_ids': trending_ids}).to_csv(
            f"{self.output_path}trending_ids.csv", index=False
        )
        
        print(f"✅ Enhanced dataset created: {len(movies_final):,} movies")
        print(f"✅ Clean ratings: {len(ratings_clean):,} ratings")
        print(f"✅ Trending movies tracked: {len(trending_ids)}")
        
        return movies_final, ratings_clean, trending_ids

    # [Include all the previous methods from the earlier script here]
    # load_movielens_data(), load_movies_metadata(), clean_movies_metadata(), 
    # process_credits(), process_keywords(), etc.

    def load_movielens_data(self):
        """Load and preprocess MovieLens 25M data"""
        print("📊 Loading MovieLens 25M data...")
        
        ratings = pd.read_csv(f"{self.data_path}movielens-25m/ratings.csv")
        movies = pd.read_csv(f"{self.data_path}movielens-25m/movies.csv")
        links = pd.read_csv(f"{self.data_path}movielens-25m/links.csv")
        tags = pd.read_csv(f"{self.data_path}movielens-25m/tags.csv")
        
        print(f"   Ratings: {len(ratings):,} records")
        print(f"   Movies: {len(movies):,} records")
        print(f"   Links: {len(links):,} records")
        print(f"   Tags: {len(tags):,} records")
        
        return ratings, movies, links, tags
    
    def load_movies_metadata(self):
        """Load and preprocess The Movies Dataset"""
        print("📊 Loading Movies Metadata...")
        
        movies_meta = pd.read_csv(f"{self.data_path}movies-dataset/movies_metadata.csv", low_memory=False)
        credits = pd.read_csv(f"{self.data_path}movies-dataset/credits.csv")
        keywords = pd.read_csv(f"{self.data_path}movies-dataset/keywords.csv")
        
        print(f"   Movies Metadata: {len(movies_meta):,} records")
        print(f"   Credits: {len(credits):,} records")
        print(f"   Keywords: {len(keywords):,} records")
        
        return movies_meta, credits, keywords
    
    def load_imdb_reviews(self):
        """Load IMDb reviews for sentiment analysis"""
        print("📊 Loading IMDb Reviews...")
        reviews = pd.read_csv(f"{self.data_path}imdb-reviews/IMDB Dataset.csv")
        print(f"   IMDb Reviews: {len(reviews):,} records")
        return reviews
    
    def load_posters_data(self):
        """Load movie posters data"""
        print("📊 Loading Posters Data...")
        posters = pd.read_csv(f"{self.data_path}posters/MovieGenre.csv", encoding='latin-1')
        print(f"   Posters: {len(posters):,} records")
        return posters
    
    def clean_movies_metadata(self, movies_meta):
        """Clean and prepare movies metadata"""
        print("🧹 Cleaning movies metadata...")
        
        # Basic cleaning
        movies_meta = movies_meta.dropna(subset=['title', 'release_date'])
        movies_meta = movies_meta[movies_meta['adult'] == 'False']
        
        # Convert ID to integer
        movies_meta['id'] = pd.to_numeric(movies_meta['id'], errors='coerce')
        movies_meta = movies_meta.dropna(subset=['id'])
        movies_meta['id'] = movies_meta['id'].astype(int)
        
        # Parse JSON columns
        def safe_parse_json(x):
            if pd.isna(x):
                return []
            try:
                if isinstance(x, str):
                    return [item['name'] for item in literal_eval(x)]
                return []
            except:
                return []
        
        movies_meta['genres'] = movies_meta['genres'].apply(safe_parse_json)
        movies_meta['production_companies'] = movies_meta['production_companies'].apply(safe_parse_json)
        
        # Convert numeric columns
        movies_meta['vote_average'] = pd.to_numeric(movies_meta['vote_average'], errors='coerce')
        movies_meta['vote_count'] = pd.to_numeric(movies_meta['vote_count'], errors='coerce')
        movies_meta['popularity'] = pd.to_numeric(movies_meta['popularity'], errors='coerce')
        
        # Extract year from release date
        movies_meta['release_year'] = pd.to_datetime(movies_meta['release_date'], errors='coerce').dt.year
        
        # Select relevant columns
        movies_meta = movies_meta[[
            'id', 'title', 'genres', 'overview', 'poster_path', 
            'release_date', 'release_year', 'runtime', 'vote_average', 
            'vote_count', 'popularity', 'production_companies'
        ]]
        
        print(f"   Cleaned metadata: {len(movies_meta):,} records")
        return movies_meta
    
    def process_credits(self, credits):
        """Process credits data to extract cast and directors"""
        print("🎬 Processing credits data...")
        
        credits['id'] = pd.to_numeric(credits['id'], errors='coerce')
        credits = credits.dropna(subset=['id'])
        credits['id'] = credits['id'].astype(int)
        
        def extract_cast(cast_str):
            if pd.isna(cast_str):
                return []
            try:
                cast_list = literal_eval(cast_str)
                return [actor['name'] for actor in cast_list[:5]]  # Top 5 actors
            except:
                return []
        
        def extract_director(crew_str):
            if pd.isna(crew_str):
                return None
            try:
                crew_list = literal_eval(crew_str)
                directors = [member['name'] for member in crew_list if member['job'] == 'Director']
                return directors[0] if directors else None
            except:
                return None
        
        credits['cast'] = credits['cast'].apply(extract_cast)
        credits['director'] = credits['crew'].apply(extract_director)
        
        credits_clean = credits[['id', 'cast', 'director']]
        print(f"   Processed credits: {len(credits_clean):,} records")
        return credits_clean
    
    def process_keywords(self, keywords):
        """Process keywords data"""
        print("🔑 Processing keywords...")
        
        keywords['id'] = pd.to_numeric(keywords['id'], errors='coerce')
        keywords = keywords.dropna(subset=['id'])
        keywords['id'] = keywords['id'].astype(int)
        
        def extract_keywords(keywords_str):
            if pd.isna(keywords_str):
                return []
            try:
                keywords_list = literal_eval(keywords_str)
                return [kw['name'] for kw in keywords_list]
            except:
                return []
        
        keywords['keywords'] = keywords['keywords'].apply(extract_keywords)
        keywords_clean = keywords[['id', 'keywords']]
        
        print(f"   Processed keywords: {len(keywords_clean):,} records")
        return keywords_clean

def main():
    preprocessor = MovieDataPreprocessor()
    movies_final, ratings_clean, trending_ids = preprocessor.create_master_dataset()
    
    print("\n🎉 ENHANCED DATA PREPROCESSING COMPLETED!")
    print(f"📁 Output saved to: {preprocessor.output_path}")
    print(f"🎬 Final movies: {len(movies_final):,} (with TMDB trending)")
    print(f"⭐ Final ratings: {len(ratings_clean):,}")
    print(f"🔥 Current trending: {len(trending_ids)} movies")

if __name__ == "__main__":
    main()
