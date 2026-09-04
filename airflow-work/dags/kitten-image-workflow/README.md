# Kitten Image Workflow

An Apache Airflow DAG that retrieves two random kitten images from Unsplash, downloads them, and reports how many images were saved.

## Workflow

The DAG is named `kitten_image_fetcher` and runs daily at midnight:

1. `fetch_kitten_urls` calls the Unsplash API and saves its JSON response to `/tmp/urls/images_urls.json`.
2. `get_kitten_urls` reads that JSON file and downloads the images to `/tmp/images/fetched_images/`.
3. `pipeline_notification` counts the downloaded files and prints the result in the Airflow task log.

The task order is:

```text
fetch_kitten_urls -> get_kitten_urls -> pipeline_notification
```

## Requirements

- Python 3
- Apache Airflow
- `requests`
- `python-dotenv`
- An Unsplash API key

Install the Python dependencies in the environment used by Airflow. Airflow should be installed using the official constraints file for the selected Python and Airflow versions.

## Configuration

Create a `.env` file in the project directory:

```env
UNSPLASH_API_KEY=your_unsplash_api_key
```

Do not commit `.env` or expose the API key in source control. In production, use an Airflow Connection, environment variable, or secrets manager instead.

## Local Airflow Setup

From the project directory, initialize Airflow and start its services using your chosen Airflow setup. The DAG file is:

```text
kitten_image_dag.py
```

Place or link this file into Airflow's configured `dags` directory. Then verify that Airflow can discover the DAG:

```powershell
airflow dags list
```

To run the workflow manually:

```powershell
airflow dags trigger kitten_image_fetcher
```

The project also contains `get_kitten_images.py`, which holds the Python function used to download the images.

## Output Files

The current DAG uses these paths:

```text
/tmp/urls/images_urls.json
/tmp/images/fetched_images/
```

These paths are temporary and may be deleted when a worker or container is replaced. They are suitable for a simple local test only if all tasks run on the same machine and can access the same `/tmp` directory.

For production, replace them with a shared mounted volume or object storage such as Amazon S3, Azure Blob Storage, or Google Cloud Storage. This is important when Airflow uses multiple workers or Kubernetes, because different tasks may run in different containers or machines.

## Important Notes

- The Unsplash API must be reachable from the Airflow worker.
- `curl` must be installed on the worker because the first and third tasks use shell commands.
- The downloader currently saves files using Unsplash IDs without file extensions.
- The downloader should be hardened with request timeouts, HTTP status checks, and partial-download handling before production use.
- The `VENV_PATH` value in `kitten_image_dag.py` is currently defined but is not used to activate the virtual environment. Airflow must already be running with the required dependencies installed.
