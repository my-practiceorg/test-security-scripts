import requests
import csv
import argparse

def fetch_repos_and_branches(org, token, team_slug):
    url = f"https://api.github.com/orgs/{org}/teams/{team_slug}/repos"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json"
    }

    repos = []
    page = 1
    while True:
        resp = requests.get(url, headers=headers, params={"per_page": 100, "page": page})
        if resp.status_code != 200:
            raise Exception(f"Error: {resp.status_code} - {resp.text}")
        
        repo_data = resp.json()
        if not repo_data:
            break
        
        for repo in repo_data:
            repo_name = repo["name"]
            default_branch = repo["default_branch"]
            repos.append([team_slug, repo_name, default_branch])
        page += 1
    return repos

def read_team_names_from_csv(filename="get_list_teams.csv"):
    team_names = []
    with open(filename, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader)  # Skip header
        for row in reader:
            team_names.append(row[0])  # Assuming team names are in the first column
    return team_names

def save_to_csv(data, filename="team_repos.csv"):
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Team Name", "Repository", "Default Branch"])
        writer.writerows(data)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--pat', required=True, help='GitHub Personal Access Token')
    parser.add_argument('--org', required=True, help='GitHub Organization')
    args = parser.parse_args()

    # Read the team names from the input CSV
    team_names = read_team_names_from_csv("get_list_teams.csv")
    
    all_repos = []
    for team in team_names:
        try:
            # Fetch repositories for the team using the team name as slug
            team_repos = fetch_repos_and_branches(args.org, args.pat, team)
            all_repos.extend(team_repos)
        except Exception as e:
            # Error handling: Skip teams where repo fetch fails, no output to terminal
            pass

    if all_repos:
        save_to_csv(all_repos)
    else:
        # If no repositories are found, no message will be shown
        pass

if __name__ == "__main__":
    main()
