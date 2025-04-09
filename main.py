from youtube_contact_scraper import YouTubeScraper

api_keys = ["AIzaSyA4__CEwYmsgaFqjmQ0epUntSUgWtNUffM"]
db_params = {
    "host": "localhost",
    "database": "youtube_dat",
    "user": "postgres",
    "password": "penis"
}

scraper = YouTubeScraper(api_keys, db_params)
scraper.run(duration_hours=4, min_subs=1000000)