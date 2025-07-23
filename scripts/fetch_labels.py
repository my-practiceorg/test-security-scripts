import requests
import argparse
import csv
from concurrent.futures import ThreadPoolExecutor, as_completed

GITHUB_API_URL = "https://api.github.com"

def get_all_repos(org, headers):
    repos = []
    page = 1
    while True:
        url = f"{GITHUB_API_URL}/orgs/{org}/repos?per_page=100&page={page}"
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            raise Exception(f"Error fetching repos: {response.status_code} {response.text}")
        data = response.json()
        if not data:
            break
        repos.extend(data)
        page += 1
    return repos

def get_labels(repo_full_name, headers):
    labels = []
    page = 1
    while True:
        url = f"{GITHUB_API_URL}/repos/{repo_full_name}/labels?per_page=100&page={page}"
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            break
        data = response.json()
        if not data:
            break
        labels.extend([label["name"] for label in data])
        page += 1
    return labels

def fetch_labels_threadsafe(repo_full_name, headers):
    try:
        return get_labels(repo_full_name, headers)
    except Exception:
        return []

def main():
    parser = argparse.ArgumentParser(description="Get unique labels across all org repos in parallel.")
    parser.add_argument("--org", required=True, help="GitHub organization name")
    parser.add_argument("--token", required=True, help="GitHub Personal Access Token")
    args = parser.parse_args()

    headers = {
        "Authorization": f"token {args.token}",
        "Accept": "application/vnd.github+json"
    }

    print(f"Fetching all repositories from org '{args.org}'...")
    repos = get_all_repos(args.org, headers)
    print(f"Total repositories found: {len(repos)}")

    unique_labels = set()
    max_threads = 20  # adjust if needed

    print("Fetching labels in parallel...")
    with ThreadPoolExecutor(max_workers=max_threads) as executor:
        futures = {
            executor.submit(fetch_labels_threadsafe, repo["full_name"], headers): repo["full_name"]
            for repo in repos
        }

        for future in as_completed(futures):
            repo_labels = future.result()
            unique_labels.update(label.strip() for label in repo_labels)

    # Write to CSV
    with open("org_unique_labels.csv", "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Label Name"])
        for label in sorted(unique_labels):
            writer.writerow([label])

    print("\n✅ Done! Unique labels written to org_unique_labels.csv")

if __name__ == "__main__":
    main()
