import requests
import datetime
import csv
import argparse

# Function to get repositories created in the last 30 days
def get_repos_created_last_30_days(github_token, org_name):
    github_api_url = f"https://api.github.com/orgs/{org_name}/repos"
    headers = {
        "Authorization": f"Bearer {github_token}",
        "Accept": "application/vnd.github+json"
    }

    today = datetime.date.today()
    thirty_days_ago = today - datetime.timedelta(days=30)

    params = {
        'per_page': 100,
    }

    repo_list = []
    page = 1
    while True:
        params['page'] = page
        response = requests.get(github_api_url, headers=headers, params=params)

        if response.status_code != 200:
            print(f"Failed to fetch repos: {response.status_code} - {response.text}")
            break

        repos = response.json()
        if not repos:
            break

        for repo in repos:
            created_at = datetime.datetime.strptime(repo['created_at'], "%Y-%m-%dT%H:%M:%SZ").date()
            if thirty_days_ago <= created_at <= today:
                creator = get_repo_creator(repo['full_name'], headers)
                last_updated_by = get_last_updated_by(repo['full_name'], headers)
                has_pre_commit_config = check_pre_commit_config(repo['full_name'], headers)
                has_gitleaks_workflow = check_gitleaks_workflow(repo['full_name'], headers)
                custom_properties = get_repo_custom_properties(repo['full_name'], headers)
                branch_protection_enabled = check_branch_protection(repo['full_name'], repo['default_branch'], headers)
                rulesets_enabled = check_rulesets(org_name, repo['name'], headers)

                repo_list.append({
                    'name': repo['name'],
                    'created_at': repo['created_at'],
                    'creator': creator,
                    'last_updated_by': last_updated_by,
                    'has_pre_commit_config': has_pre_commit_config,
                    'has_gitleaks_workflow': has_gitleaks_workflow,
                    'repo_type': custom_properties,
                    'branch_protection_enabled': branch_protection_enabled,
                    'rulesets_enabled': rulesets_enabled
                })

        page += 1

    return repo_list

def get_repo_creator(repo_full_name, headers):
    events_url = f"https://api.github.com/repos/{repo_full_name}/events"
    response = requests.get(events_url, headers=headers)
    if response.status_code != 200:
        print(f"Failed to fetch events for {repo_full_name}: {response.status_code} - {response.text}")
        return "Unknown"
    events = response.json()
    for event in events:
        if event['type'] == 'CreateEvent':
            return event['actor']['login']
    return "Unknown"

def get_last_updated_by(repo_full_name, headers):
    commits_url = f"https://api.github.com/repos/{repo_full_name}/commits?per_page=1"
    response = requests.get(commits_url, headers=headers)
    if response.status_code != 200:
        print(f"Failed to fetch commits for {repo_full_name}: {response.status_code} - {response.text}")
        return "Unknown"
    commits = response.json()
    if commits:
        return commits[0]['commit']['author']['name']
    return "Unknown"

def check_pre_commit_config(repo_full_name, headers):
    contents_url = f"https://api.github.com/repos/{repo_full_name}/contents/.pre-commit-config.yaml"
    response = requests.get(contents_url, headers=headers)
    return response.status_code == 200

def check_gitleaks_workflow(repo_full_name, headers):
    workflow_url = f"https://api.github.com/repos/{repo_full_name}/contents/.github/workflows/gitleaks_secret_scan.yml"
    response = requests.get(workflow_url, headers=headers)
    return response.status_code == 200

def get_repo_custom_properties(repo_full_name, headers):
    custom_properties_url = f"https://api.github.com/repos/{repo_full_name}/properties/values"
    response = requests.get(custom_properties_url, headers=headers)
    if response.status_code == 200:
        custom_properties = response.json()
        for prop in custom_properties:
            if prop['property_name'] == 'Repo_Type':
                return prop['value']
        return 'Repo_Type not found'
    else:
        print(f"Failed to fetch custom properties for {repo_full_name}: {response.status_code} - {response.text}")
        return "Unknown"

def check_branch_protection(repo_full_name, default_branch, headers):
    protection_url = f"https://api.github.com/repos/{repo_full_name}/branches/{default_branch}/protection"
    response = requests.get(protection_url, headers=headers)
    if response.status_code == 200:
        return True
    elif response.status_code == 404:
        return False
    else:
        print(f"Failed to check branch protection for {repo_full_name}: {response.status_code} - {response.text}")
        return "Unknown"

def check_rulesets(org_name, repo_name, headers):
    url = f"https://api.github.com/repos/{org_name}/{repo_name}/rulesets"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        rulesets = response.json()
        return len(rulesets) > 0
    elif response.status_code == 404:
        return False
    else:
        print(f"Error checking rulesets for {repo_name}: {response.status_code} - {response.text}")
        return "Unknown"

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Fetch GitHub org repos created in the last 30 days with metadata.')
    parser.add_argument('-pat', '--github_token', type=str, required=True, help='GitHub Personal Access Token')
    parser.add_argument('-org', '--org_name', type=str, required=True, help='GitHub Organization Name')
    args = parser.parse_args()

    repos_last_30_days = get_repos_created_last_30_days(args.github_token, args.org_name)

    if repos_last_30_days:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"repos_last_30_days_{timestamp}.csv"
        with open(filename, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow([
                'Repo Name',
                'Created At',
                'Created By',
                'Last Updated By',
                'Has .pre-commit-config.yaml',
                'Has gitleaks_secret_scan.yml',
                'Repo_Type',
                'Branch Protection Enabled',
                'Rulesets Enabled'
            ])
            for repo in repos_last_30_days:
                writer.writerow([
                    repo['name'],
                    repo['created_at'],
                    repo['creator'],
                    repo['last_updated_by'],
                    repo['has_pre_commit_config'],
                    repo['has_gitleaks_workflow'],
                    repo['repo_type'],
                    repo['branch_protection_enabled'],
                    repo['rulesets_enabled']
                ])
        print(f"Results saved to '{filename}'")
    else:
        print(f"No repositories created in the last 30 days for organization '{args.org_name}'.")
