import csv
import argparse
import requests

# Branch protection settings
protection_data = {
    "required_status_checks": {
        "strict": True,
        "contexts": ["scan / Gitleaks Secret Scanning"]
    },
    "enforce_admins": True,
    "required_conversation_resolution": True,
    "required_pull_request_reviews": {
        "dismiss_stale_reviews": True,
        "require_code_owner_reviews": True,
        "required_approving_review_count": 1
    },
    "restrictions": None,
    "allow_force_pushes": False
}

def read_repo_data(repos_file, protection_file):
    # Read team repo list
    repos = {}
    with open(repos_file, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            row = {k.strip(): v.strip() for k, v in row.items()}  # Normalize keys & values
            key = f"{row['Repository']}"
            repos[key] = {
                "team_slug": row["Team Slug"],
                "repo": row["Repository"],
                "branch": row["Default Branch"]
            }

    # Read protection status
    with open(protection_file, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            row = {k.strip(): v.strip() for k, v in row.items()}  # Normalize keys & values
            key = f"{row['Repository']}"
            if key in repos:
                repos[key]["branch_protection"] = row["Branch Protection"].upper() == "TRUE"
                repos[key]["rulesets"] = row["Rulesets Enabled"].upper() == "TRUE"
    return list(repos.values())

def enable_branch_protection(org, repo, branch, token):
    url = f"https://api.github.com/repos/{org}/{repo}/branches/{branch}/protection"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "Content-Type": "application/json"
    }
    response = requests.put(url, headers=headers, json=protection_data)

    # Optional: print response JSON for debugging
    try:
        print(f"{repo}/{branch} - Response: {response.status_code}")
        print(response.json())  # You can remove this after debugging
    except Exception:
        print(f"Non-JSON response for {repo}/{branch}")

    return response.status_code in [200, 201]

def process_repos(org, token, repos, output_file="final_repo_status.csv"):
    results = []

    for item in repos:
        team = item["team_slug"]
        repo = item["repo"]
        branch = item["branch"]
        branch_protection = item.get("branch_protection", False)
        rulesets = item.get("rulesets", False)

        # Determine status
        if branch_protection and not rulesets:
            status = "Branch protection already enabled"
        elif not branch_protection and rulesets:
            status = "Rulesets already enabled"
        elif branch_protection and rulesets:
            status = "Branch protection & rulesets are enabled"
        else:
            # Apply branch protection
            success = enable_branch_protection(org, repo, branch, token)
            status = "Branch protection enabled via API" if success else "Failed to enable branch protection"

        results.append([team, repo, branch, status])

    # Save to output CSV
    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Team Slug", "Repository", "Default Branch", "Status"])
        writer.writerows(results)

def main():
    parser = argparse.ArgumentParser(description="Evaluate and update repo branch protection settings")
    parser.add_argument('--pat', required=True, help='GitHub Personal Access Token')
    parser.add_argument('--org', required=True, help='GitHub Organization')
    parser.add_argument('--repos', default="team_repos.csv", help='CSV file with team repositories')
    parser.add_argument('--protection', default="repo_protection_results.csv", help='CSV with current protection status')
    parser.add_argument('--output', default="final_repo_status.csv", help='Output CSV with actions taken')
    args = parser.parse_args()

    repos = read_repo_data(args.repos, args.protection)
    process_repos(args.org, args.pat, repos, args.output)

if __name__ == "__main__":
    main()
