# Socratic PR script
import os
import re
import subprocess
import sys
import json
import urllib.request

def get_pr_diff():
    """
    Gets the pull request diff using git, fetching the base branch first.
    Relies on GITHUB_BASE_REF and GITHUB_HEAD_REF environment variables.
    """
    base_ref = os.environ.get("GITHUB_BASE_REF")
    head_ref = os.environ.get("GITHUB_HEAD_REF")

    if not base_ref or not head_ref:
        print("ERROR: GITHUB_BASE_REF and GITHUB_HEAD_REF must be set.", file=sys.stderr)
        return None

    try:
        print(f"Fetching base branch: {base_ref}")
        subprocess.run(["git", "fetch", "origin", base_ref, "--depth=1"], check=True, capture_output=True, text=True)

        print(f"Getting diff between origin/{base_ref} and {head_ref}")
        result = subprocess.run(
            ["git", "diff", f"origin/{base_ref}...{head_ref}"],
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"ERROR: git diff failed.\nSTDOUT:\n{e.stdout}\nSTDERR:\n{e.stderr}", file=sys.stderr)
        return None

def get_pr_details():
    """Gets PR number and body from the GitHub event payload."""
    event_path = os.environ.get("GITHUB_EVENT_PATH")
    if not event_path or not os.path.exists(event_path):
        print("ERROR: GITHUB_EVENT_PATH not found.", file=sys.stderr)
        return None, None

    with open(event_path, 'r', encoding='utf-8') as f:
        event_data = json.load(f)

    pr_details = event_data.get("pull_request")
    if not pr_details:
        print("ERROR: No pull_request details in event payload.", file=sys.stderr)
        return None, None

    return pr_details.get("number"), pr_details.get("body", "")

def post_github_comment(repo, pr_number, token, comment_body):
    """Posts a comment to the GitHub PR. In dry-run mode, prints to stdout."""
    if os.environ.get("SOCRATIC_DRY_RUN"):
        print("\n--- SOCRATIC COMMENT (DRY RUN) ---")
        print(comment_body)
        print("---------------------------------\n")
        return

    url = f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
        "Content-Type": "application/json"
    }
    data = json.dumps({"body": comment_body}).encode("utf-8")

    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req) as response:
            if response.status in [200, 201]:
                print(f"Successfully posted comment to PR #{pr_number}.")
            else:
                print(f"ERROR: Failed to post comment. Status: {response.status}, Body: {response.read().decode()}", file=sys.stderr)
    except urllib.error.URLError as e:
        print(f"ERROR: Failed to post comment. {e.reason}", file=sys.stderr)

def slop_score(md: str):
    """
    Prefer project SlopScorer; gracefully fall back to a lightweight heuristic.
    Returns a dict with keys: score, emojis, emdash, endash
    """
    if md is None:
        md = ""
    try:
        from services.scorecard.slop_scorer import SlopScorer  # type: ignore
        res = SlopScorer().score(md)
        return {
            "score": float(res.get("score", 0.0)),
            "emojis": int(res.get("emojis", 0)),
            "emdash": int(res.get("emdash", 0)),
            "endash": int(res.get("endash", 0)),
        }
    except ImportError:
        emojis = len(re.findall(r"[\U0001F300-\U0001FAFF]", md))
        emdash = md.count("—")
        endash = md.count("–")
        score = min(1.0, 0.02 * emojis + 0.01 * emdash + 0.01 * endash)
        return {"score": score, "emojis": emojis, "emdash": emdash, "endash": endash}

def _test_run():
    """Simulates a PR environment for local testing."""
    print("--- Running Socratic Script in Test Mode ---")

    # Create a fake event payload
    fake_event = {
        "pull_request": {
            "number": 123,
            "body": "This is a test PR body. It has some emojis 😊 and an em-dash — just for fun."
        }
    }
    event_file = "github_event.json"
    with open(event_file, 'w', encoding='utf-8') as f:
        json.dump(fake_event, f)

    # Set mock environment variables
    os.environ["GITHUB_EVENT_PATH"] = event_file
    os.environ["GITHUB_REPOSITORY"] = "test/repo"
    os.environ["GITHUB_TOKEN"] = "fake_token"
    os.environ["SOCRATIC_DRY_RUN"] = "1"

    # Mock the git diff call
    os.environ["GITHUB_BASE_REF"] = "main"
    os.environ["GITHUB_HEAD_REF"] = "feature"

    main()

    # Clean up
    os.remove(event_file)
    print("--- Test Mode Finished ---")

def main():
    print("Running Socratic PR script...")
    repo = os.environ.get("GITHUB_REPOSITORY")
    token = os.environ.get("GITHUB_TOKEN")
    pr_number, pr_body = get_pr_details()

    if not all([repo, token, pr_number is not None]):
        print("ERROR: Missing GITHUB_REPOSITORY, GITHUB_TOKEN, or PR details.", file=sys.stderr)
        sys.exit(1)

    score_details = slop_score(pr_body)
    comment = (
        f"### Socratic Analysis\n\n"
        f"**Slop Score**: {score_details['score']:.2f}\n"
        f"- Emojis: {score_details['emojis']}\n"
        f"- Em-dashes: {score_details['emdash']}\n"
        f"- En-dashes: {score_details['endash']}\n\n"
        f"*This is an automated analysis based on the PR description.*"
    )
    post_github_comment(repo, pr_number, token, comment)

    # Diff logic is not part of the comment yet, so we can skip it in the main flow for now
    # diff = get_pr_diff()
    # if diff:
    #     print("\n--- PR Diff ---")
    #     print(diff)
    #     print("--- End PR Diff ---\n")
    # else:
    #     print("Could not retrieve PR diff.")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        _test_run()
    else:
        main()