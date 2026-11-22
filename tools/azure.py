import os
import base64
import requests

from datetime import datetime, timezone
from dotenv import load_dotenv

from file_handler import ExportFileHandler
from helper import get_language_type, strip_ref


load_dotenv()


class AzureDevOpsCommentExporter:

    def __init__(self):
        self.base_url = os.getenv("AZURE_URL", "").rstrip("/")
        self.org = os.getenv("AZURE_ORG", "").strip()
        self.project = os.getenv("AZURE_PROJECT", "").strip()
        self.repo_id = os.getenv("AZURE_REPO_ID", "").strip()
        self.token = os.getenv("AZURE_TOKEN")
        self.allowed_users = {u.strip() for u in os.getenv("AZURE_ALLOWED_USERS", "").split(",") if u.strip()}

        if not all([self.org, self.project, self.repo_id, self.token, self.allowed_users]):
            raise ValueError("Missing Azure DevOps configuration in .env")

        # PAT auth: Basic base64(":" + token)
        encoded = base64.b64encode(f":{self.token}".encode()).decode()
        self.session = requests.Session()
        self.session.headers.update({"Authorization": f"Basic {encoded}"})

        self.api_url = (
            f"{self.base_url}/{self.org}/{self.project}"
            f"/_apis/git/repositories/{self.repo_id}"
        )
        self.api_version = "7.1"
        self.max_per_page = 100

        self.file_handler = ExportFileHandler()
        self.history = self.file_handler.load_history()

    def get_response(self, url, params=None):
        """GET request with auth. Raises on non-2xx."""
        response = self.session.get(url, params=params, timeout=30)
        response.raise_for_status()
        return response

    def _iter_pr_pages(self, per_page: int | None):
        """Yield (page_number, prs) one API page at a time until exhausted or per_page reached."""
        url = f"{self.api_url}/pullrequests"
        base_params = {
            "searchCriteria.status": "completed",
            "api-version": self.api_version,
        }
        skip = 0
        page = 1
        remaining = per_page

        while True:
            chunk = min(remaining, self.max_per_page) if remaining is not None else self.max_per_page
            response = self.get_response(url, {**base_params, "$top": chunk, "$skip": skip})
            prs = response.json().get("value", [])

            if not prs:
                break

            print(f"Page {page}: {len(prs)} records")
            yield page, prs

            if remaining is not None:
                remaining -= len(prs)
                if remaining <= 0:
                    break

            if len(prs) < chunk:
                break

            skip += len(prs)
            page += 1

    def get_pr_threads(self, pr_id):
        """Return raw threads list for one PR."""
        return self.get_response(
            f"{self.api_url}/pullRequests/{pr_id}/threads",
            {"api-version": self.api_version},
        ).json().get("value", [])

    def normalize_comment(self, comment, file_path: str | None):
        """Extract {username, body, language_type} from a raw Azure comment dict."""
        author = comment.get("author") or {}
        return {
            "username": author.get("uniqueName"),
            "body": comment.get("content"),
            "language_type": get_language_type(file_path),
        }

    def _process_page(self, prs_raw: list, tracked_pr_ids: set) -> tuple[list, int]:
        """Filter PRs, fetch and normalize comments. Returns (exported_prs, total_comments)."""
        prs = [
            pr for pr in prs_raw
            if pr.get("pullRequestId") not in tracked_pr_ids and bool(pr.get("closedDate"))
        ]

        exported_prs = []
        total_comments = 0

        for index, pr in enumerate(prs, start=1):
            pr_id = pr["pullRequestId"]
            print(f"[{index}/{len(prs)}] Processing PR #{pr_id}: {pr['title']}")

            threads = self.get_pr_threads(pr_id)

            filtered_comments = []
            for thread in threads:
                file_path = (thread.get("threadContext") or {}).get("filePath")
                for comment in thread.get("comments", []):
                    if (
                        comment.get("commentType") == "text"
                        and not comment.get("isDeleted", False)
                        and comment.get("author", {}).get("uniqueName") in self.allowed_users
                    ):
                        filtered_comments.append(self.normalize_comment(comment, file_path))

            if not filtered_comments:
                continue

            repo_name = pr.get("repository", {}).get("name", self.repo_id)
            web_url = (
                f"{self.base_url}/{self.org}/{self.project}"
                f"/_git/{repo_name}/pullrequest/{pr_id}"
            )

            exported_prs.append({
                "iid": pr_id,
                "title": pr.get("title"),
                "source_branch": strip_ref(pr.get("sourceRefName"), "refs/heads/"),
                "target_branch": strip_ref(pr.get("targetRefName"), "refs/heads/"),
                "web_url": web_url,
                "merged_at": pr.get("closedDate"),
                "comments": filtered_comments,
            })
            total_comments += len(filtered_comments)

        return exported_prs, total_comments

    def export_single(self, pr_id: int):
        """Fetch all comments for one PR (no user filter) and export."""
        print(f"\nFetching comments for PR #{pr_id}...")
        threads = self.get_pr_threads(pr_id)

        all_comments = []
        for thread in threads:
            file_path = (thread.get("threadContext") or {}).get("filePath")
            for comment in thread.get("comments", []):
                if comment.get("commentType") == "text" and not comment.get("isDeleted", False):
                    all_comments.append(self.normalize_comment(comment, file_path))

        if not all_comments:
            print("\nNo comments found.")
            return

        output = {
            "metadata": {
                "azure_org": self.org,
                "azure_project": self.project,
                "repo_id": self.repo_id,
                "total_comments": len(all_comments),
                "exported_at": datetime.now(timezone.utc).isoformat(),
            },
            "merge_requests": [{"iid": pr_id, "comments": all_comments}],
        }

        output_file = self.file_handler.save_export(
            output, "", "", filename=f"pr_comments_{pr_id}"
        )
        print("\nExport completed!")
        print(f"  {output_file}")

    def export_multiple(self, per_page: int | None = None):
        """Fetch PRs page by page, write one export file per page when multi-page, one file otherwise."""
        print("\nRetrieving pull requests...")

        tracked_pr_ids = set(self.history.get("tracked_mr_iids", []))
        is_multi_file = per_page is None or per_page > self.max_per_page

        all_exported_prs = []
        output_files = []

        for page_num, prs_raw in self._iter_pr_pages(per_page):
            exported_prs, total_comments = self._process_page(prs_raw, tracked_pr_ids)

            if total_comments == 0:
                continue

            prs_with_dates = [pr for pr in exported_prs if pr.get("merged_at")]
            if not prs_with_dates:
                continue

            latest_date = prs_with_dates[0]["merged_at"][:10].replace("-", "")
            oldest_date = prs_with_dates[-1]["merged_at"][:10].replace("-", "")

            output = {
                "metadata": {
                    "azure_org": self.org,
                    "azure_project": self.project,
                    "repo_id": self.repo_id,
                    "start_date": oldest_date,
                    "end_date": latest_date,
                    "total_comments": total_comments,
                    "exported_at": datetime.now(timezone.utc).isoformat(),
                },
                "merge_requests": exported_prs,
            }

            page_arg = page_num if is_multi_file else None
            output_file = self.file_handler.save_export(output, oldest_date, latest_date, page_arg)
            output_files.append(output_file)
            all_exported_prs.extend(exported_prs)

        if all_exported_prs:
            self.file_handler.save_history(all_exported_prs)
            print("\nExport completed!")
            print(f"Pull requests: {len(all_exported_prs)}")
            print(f"Files written: {len(output_files)}")
            for f in output_files:
                print(f"  {f}")
        else:
            print("\nNo comments found.")


def main():
    print("=" * 50)
    print("Azure DevOps Code Review Comment Exporter")
    print("=" * 50)

    exporter = AzureDevOpsCommentExporter()

    mode = input("\nFetch (1) single PR or (2) multiple PRs? [1/2]: ").strip()

    if mode == "1":
        raw_id = input("Enter PR ID: ").strip()
        exporter.export_single(int(raw_id))
    else:
        latest_at = exporter.history.get("latest_tracked_at")
        prompt = f"\nLatest PR amount to fetch (leave empty for all, last tracked: {latest_at}): "
        raw = input(prompt).strip()
        per_page = int(raw) if raw else None
        exporter.export_multiple(per_page=per_page)


if __name__ == "__main__":
    main()
