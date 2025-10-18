import argparse
import concurrent.futures
import csv
import logging
import os
import signal
import sys
import threading
from datetime import datetime
from pathlib import Path
from urllib.parse import urlencode

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

# at_end_of_archive = "false"

articles_saved = 0


def sigint_handler(signal_num, frame):
    # Handle when Ctrl+C is pressed
    print(" Ctrl+C pressed. Gracefully exiting program")
    sys.exit(0)


def get_archive_start_date():
    # Get year and date of the Newsmax archive to start downloading
    parser = argparse.ArgumentParser(
        prog="dl_newsmax_articles",
        description='Downloads all news articles from Newsmax\'s "Newfront" section',
        usage="%(prog)s [year] (YYYY) [month] (M or MM)",
    )
    parser.add_argument("year", type=int, help="YYYY year of archive")
    parser.add_argument("month", type=int, help="MM month of archive")
    args = parser.parse_args()

    archive_year = args.year
    archive_month = args.month

    return archive_year, archive_month


def create_archive_year_month_queue(archive_year, archive_month):
    year_month_queue = []

    # Create 2D list that has a starting year/month on the based
    # archive_year/ archive_month that was input
    months = list(range(archive_month, 13))
    for month in months:
        year_month_queue.append((archive_year, month))

    # Then append the additional years/months to the list. The
    # program will exit if "www.newsmax.com/404/" received in the
    # HTTP response so the "end_year"/month may not be reached
    today_date = datetime.today()
    end_year = int(today_date.strftime("%Y"))

    years = range(archive_year + 1, end_year + 1)
    months = list(range(1, 13))
    for year in years:
        for month in months:
            year_month_queue.append((year, month))

    logging.debug("-- Year/Month Queue: ")
    logging.debug(f"{year_month_queue}")

    return year_month_queue


def save_to_storage(
    filename,
    news_article_title,
    news_article_url,
    news_article_month,
    news_article_day,
    news_article_year,
    news_article_datetime,
    news_article_string,
):
    global articles_saved
    csv_writer_lock = threading.Lock()
    data_file = Path(filename)

    # sleep(5)

    if data_file.exists():
        with open(filename, "a+") as file:
            with csv_writer_lock:
                writer = csv.writer(file)
                writer.writerow(
                    [
                        news_article_title,
                        news_article_url,
                        news_article_month,
                        news_article_day,
                        news_article_year,
                        news_article_datetime,
                        news_article_string,
                    ]
                )
            articles_saved += 1
            print(f"Articles saved: {articles_saved}", end="\r")
    else:
        # Column headers
        headers = "news_article_url,news_article_month,news_article_day,news_article_year,news_article_datetime,news_article_contents"

        with open(filename, "a+") as file:
            with csv_writer_lock:
                writer = csv.writer(file)
                file.write(headers + "\n")
                writer.writerow(
                    [
                        news_article_title,
                        news_article_url,
                        news_article_month,
                        news_article_day,
                        news_article_year,
                        news_article_datetime,
                        news_article_string,
                    ]
                )
            articles_saved += 1
            print(f"Articles saved: {articles_saved}", end="\r")


def get_scrapeops_url(url):
    scrapeops_proxy_url = "https://proxy.scrapeops.io/v1/"
    scrapeops_api_key = os.getenv("SCRAPEOPS_API_KEY")

    payload = {
        "api_key": scrapeops_api_key,
        "url": url,
    }

    return scrapeops_proxy_url, payload


def scrape_article_data(year_month_queue_sublist):
    archive_year = year_month_queue_sublist[0]
    archive_month = year_month_queue_sublist[1]
    logging.debug(
        f"-- Current Archive Year/Month Working On: {archive_year},{archive_month}"
    )

    session = requests.Session()

    news_archive_url = (
        "https://www.newsmax.com/archives/newsfront/16/"
        + str(archive_year)
        + "/"
        + str(archive_month)
    )

    scrapeops_proxy_url, payload = get_scrapeops_url(news_archive_url)

    """
    EXTRACT: Get URLs of news articles
    """
    retries = Retry(total=5, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
    session.mount("https://", HTTPAdapter(max_retries=retries))

    try:
        response = session.get(scrapeops_proxy_url, params=urlencode(payload))
        response.raise_for_status()
    except requests.exceptions.HTTPError as error:
        print(f"HTTP Error: {error}")
    except requests.exceptions.ConnectionError as error:
        print(f"Connection Failed: {error}")
    except requests.exceptions.Timeout as error:
        print(f"Timeout Occurred: {error}")
    except requests.exceptions.RequestException as error:
        if "www.newsmax.com/404/" in response.text:
            print("\nReached the end of the archive; no more articles to download.")
            sys.exit(0)
        elif response.status_code == 401:
            print("HTTP 401. All ScrapeOps credits used.")
            sys.exit(0)
        print(f"An Error Occurred: {error}")

    news_bsoup = BeautifulSoup(response.text, "html.parser")
    news_articles = news_bsoup.find("ul", class_="archiveRepeaterUL")
    news_article_titles_and_urls = news_articles.find_all("h5", class_="archiveH5")
    logging.debug("-- News Article Titles And URLs:")
    logging.debug(f"{news_article_titles_and_urls}")
    logging.debug(
        f"-- Number Of Article Titles: {str(len(news_article_titles_and_urls))}"
    )
    """
    EXTRACT & TRANSFORM

    Loop through article URLs and titles, extracting the month, day and year each article
    was created, its title, the URL to the article's contents and its contents

    Transform fields so that they have the proper types for Clickhouse
    """
    for item in news_article_titles_and_urls:
        # Parse "<span class="copy">" to get article's published date
        news_article_date = item.find("span", class_="copy").get_text(strip=True)
        # Split article's published date into separate strings to store as columns
        # in the .CSV
        datetime_object = datetime.strptime(news_article_date, "%b %d, %Y")
        news_article_month = datetime_object.strftime("%B")
        news_article_day = datetime_object.day
        news_article_year = datetime_object.year
        # Get article's title
        news_article_title = item.find("a", class_="").get_text()
        news_article_url = item.find("a", href=True)
        news_article_url = "https://www.newsmax.com" + news_article_url["href"]

        # Access URL for article's content
        scrapeops_proxy_url, payload = get_scrapeops_url(news_article_url)

        logging.debug(f"-- News Article URL: {news_article_url}")
        try:
            response = session.get(scrapeops_proxy_url, params=urlencode(payload))
            response.raise_for_status()
        except requests.exceptions.HTTPError as error:
            print(f"HTTP Error: {error}")
        except requests.exceptions.ConnectionError as error:
            print(f"Connection Failed: {error}")
        except requests.exceptions.Timeout as error:
            print(f"Timeout Occurred: {error}")
        except requests.exceptions.RequestException as error:
            if "www.newsmax.com/404/" in response.text:
                print("\nReached the end of the archive; no more articles to download.")
                sys.exit(0)
            elif response.status_code == 401:
                print("HTTP 401. All ScrapeOps credits used.")
                sys.exit(0)
            print(f"An Error Occurred: {error}")

        # Strip all <p> tags from article's contents
        news_bsoup = BeautifulSoup(response.text, "html.parser")
        news_article_datetime = news_bsoup.find(
            "meta", property="article:published_time"
        )
        news_article_section = news_bsoup.find("div", id="mainArticleDiv")
        news_article_content = news_article_section.find_all("p")

        news_article_string = ""
        for p in news_article_content:
            news_article_string = news_article_string + str(p.get_text(strip=True))

        """
        LOAD: Save article data to .CSV file
        """
        save_to_storage(
            "newsmax_articles.csv",
            news_article_title,
            news_article_url,
            news_article_month,
            str(news_article_day),
            str(news_article_year),
            news_article_datetime["content"],
            news_article_string,
        )


def scraper_threads(year_month_queue):
    # Launch 5 threads as that is the max of the current ScrapeOps
    # subscription
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = {
            executor.submit(
                scrape_article_data, year_month_queue_sublist
            ): year_month_queue_sublist
            for year_month_queue_sublist in year_month_queue
        }


def main():
    """
    Main function
    """
    # Uncomment for debugging purposes
    # logging.basicConfig(level=logging.DEBUG)

    # If env variable for ScrapeOps proxy is set then proceed.
    env_var_value = os.getenv("SCRAPEOPS_API_KEY")
    if env_var_value is not None:
        # Set up signal handler for Ctrl+C
        signal.signal(signal.SIGINT, sigint_handler)

        archive_year, archive_month = get_archive_start_date()
        year_month_queue = create_archive_year_month_queue(archive_year, archive_month)
        scraper_threads(year_month_queue)
    else:
        print(
            "SCRAPEOPS_API_KEY environment variable for ScrapeOps proxy is not set. Exiting."
        )


if __name__ == "__main__":
    main()
