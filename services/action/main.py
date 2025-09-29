import datetime
import json
import tempfile
from typing import Dict

import git
from jwcrypto import jwk, jws

from .models import PatchResp

# Define custom exceptions that the router can catch
class ValidationError(Exception):
    pass

class PatchError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)

def _create_jws_signature(payload: Dict, key: jwk.JWK) -> str:
    """Creates a JWS signature for the given payload."""
    payload_str = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    jwstoken = jws.JWS(payload_str.encode("utf-8"))

    # The 'alg' parameter is specified in the protected header.
    protected_header = {"alg": "EdDSA", "jwk": key.export_public(as_dict=True)}
    jwstoken.add_signature(key, alg="EdDSA", protected=json.dumps(protected_header))

    return jwstoken.serialize(compact=True)

async def apply_patch(
    planId: str,
    stepId: str,
    repo: str,
    branch: str,
    diff: str,
    commitMessage: str,
    author: Dict[str, str],
) -> PatchResp:
    """
    Applies a patch to a repository by cloning it, applying the diff,
    committing the changes, and creating a JWS signature.
    """
    # For this implementation, we assume the repo name maps to a GitHub URL.
    # In a real system, this would come from a configuration or service discovery.
    repo_url = f"https://github.com/diegocortes3211-design/{repo}.git"

    # Generate a temporary key for signing this operation.
    # In a real system, the Action Agent would have a persistent, securely stored key.
    signing_key = jwk.JWK.generate(kty="OKP", crv="Ed25519")

    with tempfile.TemporaryDirectory() as tmpdir:
        try:
            # 1. Clone the repository
            print(f"INFO: Cloning '{repo_url}' into '{tmpdir}'...")
            cloned_repo = git.Repo.clone_from(repo_url, tmpdir, branch=branch)

            # 2. Apply the patch
            patch_file = f"{tmpdir}/patch.diff"
            with open(patch_file, "w") as f:
                f.write(diff)

            print("INFO: Applying patch...")
            cloned_repo.git.apply(patch_file, "--check") # Check if patch is applicable
            cloned_repo.git.apply(patch_file)

            # 3. Commit the changes
            print("INFO: Committing changes...")

            # Construct the detailed commit message with a metadata footer
            timestamp_str = datetime.datetime.now(datetime.timezone.utc).isoformat()
            commit_footer = (
                f"\n\n"
                f"Plan: {planId}\n"
                f"Step: {stepId}\n"
                f"Author: {author['name']} <{author['email']}>\n"
                f"Timestamp: {timestamp_str}"
            )
            full_commit_message = f"{commitMessage}{commit_footer}"

            commit_author = git.Actor(author["name"], author["email"])
            commit = cloned_repo.index.commit(
                full_commit_message,
                author=commit_author,
                committer=commit_author,
            )
            commit_sha = commit.hexsha
            print(f"INFO: Committed successfully. SHA: {commit_sha}")

            # 4. Create JWS signature
            signature_payload = {
                "commitSha": commit_sha,
                "planId": planId,
                "stepId": stepId,
                "repo": repo,
                "branch": branch,
                "author": author["email"],
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            }
            signature = _create_jws_signature(signature_payload, signing_key)

            # In a real system, you would push the changes here:
            # print("INFO: Pushing changes to origin...")
            # cloned_repo.remotes.origin.push()

            return PatchResp(
                commitSha=commit_sha,
                signature=signature,
                timestamp=signature_payload["timestamp"],
            )

        except git.GitCommandError as e:
            print(f"ERROR: Git command failed: {e}")
            raise PatchError(f"Git operation failed: {e.stderr}")
        except Exception as e:
            print(f"ERROR: An unexpected error occurred: {e}")
            raise PatchError(f"An unexpected error occurred during patch application: {str(e)}")