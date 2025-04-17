import requests
import argparse
import csv

# ------------------- Fetch Teams -------------------
def fetch_teams(org, token):
    url = f"https://api.github.com/orgs/{org}/teams"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json"
    }

    teams = []
    page = 1
    while True:
        resp = requests.get(url, headers=headers, params={"per_page": 100, "page": page})
        if resp.status_code != 200:
            raise Exception(f"Error: {resp.status_code} - {resp.text}")

        team_data = resp.json()
        if not team_data:
            break

        teams.extend(team_data)
        page += 1
    return teams

def save_teams_to_csv(teams, filename="get_list_teams.csv"):
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Team Name", "Slug", "Description"])
        for team in teams:
            writer.writerow([team["name"], team["slug"], team.get("description", "N/A")])

# ------------------- Fetch Repos -------------------
def fetch_repos_for_team(org, token, team_slug):
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
            repos.append([team_slug, repo["name"], repo["default_branch"]])
        page += 1
    return repos

def read_team_slugs_from_csv(filename="get_list_teams.csv"):
    team_slugs = []
    with open(filename, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader)  # Skip header
        for row in reader:
            team_slugs.append(row[1])  # Slug is in second column
    return team_slugs

def save_repos_to_csv(data, filename="team_repos.csv"):
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Team Slug", "Repository", "Default Branch"])
        writer.writerows(data)

# ------------------- Main -------------------
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--pat', required=True, help='GitHub Personal Access Token')
    parser.add_argument('--org', required=True, help='GitHub Organization')
    parser.add_argument('--team_output', default="get_list_teams.csv")
    parser.add_argument('--repo_output', default="team_repos.csv")
    args = parser.parse_args()

    try:
        teams = fetch_teams(args.org, args.pat)
        if teams:
            save_teams_to_csv(teams, args.team_output)
    except:
        return  # Silently fail on team fetch error

    try:
        team_slugs = read_team_slugs_from_csv(args.team_output)
        all_repos = []
        for slug in team_slugs:
            try:
                repos = fetch_repos_for_team(args.org, args.pat, slug)
                all_repos.extend(repos)
            except:
                continue  # Silently skip this team
        if all_repos:
            save_repos_to_csv(all_repos, args.repo_output)
    except:
        return  # Silently fail on repo fetching

if __name__ == "__main__":
    main()
