import csv
import argparse
import requests

def check_branch_protection(org, repo, branch, token):
    url = f"https://api.github.com/repos/{org}/{repo}/branches/{branch}/protection"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json"
    }
    resp = requests.get(url, headers=headers)
    if resp.status_code == 200:
        return True
    elif resp.status_code == 404:
        return False
    else:
        raise Exception(f"Error checking branch protection for {repo}: {resp.status_code} - {resp.text}")

def check_rulesets(org, repo, token):
    url = f"https://api.github.com/repos/{org}/{repo}/rulesets"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json"
    }
    resp = requests.get(url, headers=headers)
    if resp.status_code == 200:
        rulesets = resp.json()
        return len(rulesets) > 0
    elif resp.status_code == 404:
        return False
    else:
        raise Exception(f"Error checking rulesets for {repo}: {resp.status_code} - {resp.text}")

def read_repos_from_csv(filename="team_repos.csv"):
    repos = []
    with open(filename, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader)  # Skip header
        for row in reader:
            team_slug, repo_name, default_branch = row
            repos.append((team_slug, repo_name, default_branch))
    return repos

def save_results_to_csv(results, filename="repo_protection_results.csv"):
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Team Slug", "Repository", "Default Branch", "Branch Protection", "Rulesets Enabled"])
        writer.writerows(results)

def main():
    parser = argparse.ArgumentParser(description="Check GitHub repo branch protection and rulesets")
    parser.add_argument('--pat', required=True, help='GitHub Personal Access Token')
    parser.add_argument('--org', required=True, help='GitHub Organization')
    parser.add_argument('--input', default="team_repos.csv", help='Input CSV with repo list')
    parser.add_argument('--output', default="repo_protection_results.csv", help='Output CSV with results')
    args = parser.parse_args()

    token = args.pat
    org = args.org
    repo_list = read_repos_from_csv(args.input)

    results = []
    for team_slug, repo, branch in repo_list:
        try:
            protection_enabled = check_branch_protection(org, repo, branch, token)
            rulesets_enabled = False
            if not protection_enabled:
                rulesets_enabled = check_rulesets(org, repo, token)
            results.append([
                team_slug,
                repo,
                branch,
                "TRUE" if protection_enabled else "FALSE",
                "TRUE" if rulesets_enabled else "FALSE"
            ])
        except Exception:
            # Silently skip if something fails
            continue

    if results:
        save_results_to_csv(results, args.output)

if __name__ == "__main__":
    main()
