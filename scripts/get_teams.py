import requests
import argparse
import csv

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

def save_to_csv(teams, filename="get_list_teams.csv"):
    with open(filename, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Team Name", "Slug", "Description"])
        for team in teams:
            writer.writerow([team["name"], team["slug"], team.get("description", "N/A")])
    print(f"\n📄 Saved to {filename}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--pat', required=True, help='GitHub Personal Access Token')
    parser.add_argument('--org', required=True, help='GitHub Organization')
    args = parser.parse_args()

    print(f"🔍 Fetching teams from '{args.org}'...")
    teams = fetch_teams(args.org, args.pat)

    if teams:
        for team in teams:
            print(f"- {team['name']} (Slug: {team['slug']})")
        save_to_csv(teams)
    else:
        print("⚠️ No teams found.")

if __name__ == "__main__":
    main()
