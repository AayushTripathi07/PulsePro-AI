import os
import subprocess

WORK_DIR = os.path.expanduser("~/Downloads/repo_commits_workspace_audit")
os.makedirs(WORK_DIR, exist_ok=True)

REPOS = [
    "PulsePro-AI", "Conversational-AI-Agent", "medintel-ai", "StockVision",
    "Customer-Lifetime-Value-Prediction", "marketing-analytics-ai-pipeline",
    "Trader-Sentiment-Analysis", "ResumeIQ", "Fact-Checking-Web-App",
    "stockvision-ai", "Portfolio", "Flight_Price_Prediction",
    "Marketing-Campaign-ROI-Analysis"
]

for repo in REPOS:
    repo_url = f"https://github.com/AayushTripathi07/{repo}.git"
    repo_path = os.path.join(WORK_DIR, repo)
    print(f"\n🔍 Auditing {repo}...")
    if os.path.exists(repo_path): subprocess.run(["rm", "-rf", repo_path])
    subprocess.run(["git", "clone", repo_url, repo_path], capture_output=True)
    
    # List all remote branches
    branches = subprocess.run(["git", "branch", "-r"], cwd=repo_path, capture_output=True, text=True).stdout.strip().split("\n")
    print(f"  Branches: {len(branches)}")
    for b in branches:
        if "origin/HEAD" in b or "origin/main" in b: continue
        b_name = b.strip().replace("origin/", "")
        print(f"    Deleting branch: {b_name}")
        subprocess.run(["git", "push", "origin", "--delete", b_name], cwd=repo_path)

    # List all tags
    tags = subprocess.run(["git", "tag"], cwd=repo_path, capture_output=True, text=True).stdout.strip().split("\n")
    if tags and tags[0]:
        print(f"  Tags: {len(tags)}")
        for t in tags:
            print(f"    Deleting tag: {t}")
            subprocess.run(["git", "push", "origin", ":refs/tags/" + t], cwd=repo_path)
            subprocess.run(["git", "tag", "-d", t], cwd=repo_path)
    else:
        print("  No tags found.")

print("\n✅ Audit and branch/tag cleanup complete.")
