"""
Kitten image fetcher
"""
import airflow, os, sys
from airflow.decorators import dag, task
from datetime import datetime, timedelta
from get_kitten_images import _get_kitten_urls
from dotenv import load_dotenv

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

VENV_PATH = os.path.join(PROJECT_DIR, ".venv", "Lib", "site-packages")

load_dotenv(os.path.join(PROJECT_DIR, ".env"))
CLIENT_ID = os.getenv("UNSPLASH_API_KEY")


default_args = {
    "owner": "jema_datateam",
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    "email_on_failure": False,
    "email_on_retry": False,
    "depends_on_past": False,
}


# Step 1 define Dag
@dag(
    dag_id="kitten_image_fetcher",
    default_args=default_args,
    description="Fetches kitten images from the Unsplash API and saves them to a specified directory.",
    start_date=datetime(2026, 9, 3),
    schedule_interval="0 0 * * *",
    catchup=False,
    tags=["kitten", "image", "fetcher"]
)

def kitten_image_fetcher_workflow():
    """
    Fetches kitten images from the Unsplash API and saves them to a specified directory.
    """
    # Runs the command to get the image URLs from the Unsplash API and saves them to a JSON file.
    @task.bash(task_id="fetch_kitten_urls")
    def fetch_kitten_urls():

       return f"mkdir -p /tmp/urls && curl -o /tmp/urls/images_urls.json -L --request GET 'https://api.unsplash.com/photos/random?query=kitten&count=2&client_id={CLIENT_ID}'"

    # Accesses the urls and downloads the images to a specified directory. 
    @task(task_id="get_kitten_urls")
    def process_and_download_images():
        os.makedirs("/tmp/images/fetched_images/", exist_ok=True)
        
        _get_kitten_urls(
            json_file="/tmp/urls/images_urls.json",
            save_path="/tmp/images/fetched_images/"
        )

    # Defines a task that prints the number of kitten images downloaded to the console.
    @task.bash(task_id="pipeline_notification")
    def pipeline_notification():
        return "echo 'There are now $(ls /tmp/images/fetched_images/ | wc -l) kitten images.'"

    fetch_kitten_urls >> process_and_download_images >> pipeline_notification

kitten_image_fetcher = kitten_image_fetcher_workflow()