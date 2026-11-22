import os
import requests

from datetime import datetime, timezone
from dotenv import load_dotenv

from file_handler import ExportFileHandler
from helper import get_language_type


load_dotenv()


class GitLabCommentExporter:

    def __init__(self):
        self.base_url = os.getenv("GITLAB_URL", "").rstrip("/")
        self.token = os.getenv("GITLAB_TOKEN")
        self.project_id = os.getenv("GITLAB_PROJECT_ID")
        self.allowed_users = {u.strip() for u in os.getenv("GITLAB_ALLOWED_USERS", "").split(",") if u.strip()}

        if not all([self.base_url, self.token, self.project_id]):
            raise ValueError("Missing GitLab configuration in .env")

        self.session = requests.Session()
        self.session.headers.update({"PRIVATE-TOKEN": self.token})

        self.api_url = f"{self.base_url}/api/v4/projects/{self.project_id}"
        self.max_per_page = 100

        self.file_handler = ExportFileHandler()
        self.history = self.file_handler.load_history()

    def get_response(self, url, params=None):
        """GET request with auth. Raises on non-2xx."""
        response = self.session.get(url, params=params, timeout=30)
        response.raise_for_status()
        return response

    def _iter_mr_pages(self, per_page: int | None):
        """Yield (page_number, mrs) one API page at a time until exhausted or per_page reached."""
        url = f"{self.api_url}/merge_requests"
        base_params = {
            "state": "merged",
            "order_by": "merged_at",
            "sort": "desc",
        }
        page = 1
        remaining = per_page  # None = no limit

        while True:
            chunk = min(remaining, self.max_per_page) if remaining is not None else self.max_per_page
            response = self.get_response(url, {**base_params, "per_page": chunk, "page": page})
            mrs = response.json()

            if not mrs:
                break

            print(f"Page {page}: {len(mrs)} records")
            yield page, mrs

            if remaining is not None:
                remaining -= len(mrs)
                if remaining <= 0:
                    break

            next_page = response.headers.get("X-Next-Page")
            if not next_page:
                break
            page = int(next_page)

    def get_mr_comments(self, mr_iid):
        """Return raw discussions list for one MR."""
        return self.get_response(
            f"{self.api_url}/merge_requests/{mr_iid}/discussions"
        ).json()

    def normalize_comment(self, note):
        """Extract {username, body, language_type} from a raw GitLab note dict."""
        author = note.get("author") or {}
        return {
            "username": author.get("username"),
            "body": note.get("body"),
            "language_type": get_language_type(
                note.get("position", {}).get("new_path")
            ),
        }

    def _process_page(self, mrs_raw: list, tracked_mr_iids: set) -> tuple[list, int]:
        """Filter MRs, fetch and normalize comments. Returns (exported_mrs, total_comments)."""
        merge_requests = [
            mr for mr in mrs_raw
            if mr.get("iid") not in tracked_mr_iids and bool(mr.get("merged_at"))
        ]

        exported_mrs = []
        total_comments = 0

        for index, mr in enumerate(merge_requests, start=1):
            mr_iid = mr["iid"]
            print(f"[{index}/{len(merge_requests)}] Processing MR !{mr_iid}: {mr['title']}")

            discussions = self.get_mr_comments(mr_iid)

            all_notes = [
                note
                for discussion in discussions
                for note in discussion.get("notes", [])
            ]
            filtered_notes = [
                note for note in all_notes
                if not note.get("system", True)
                and note.get("author", {}).get("username") in self.allowed_users
            ]

            filtered_comments = [self.normalize_comment(note) for note in filtered_notes]

            if not filtered_comments:
                continue

            exported_mrs.append({
                "iid": mr_iid,
                "title": mr.get("title"),
                "source_branch": mr.get("source_branch"),
                "target_branch": mr.get("target_branch"),
                "web_url": mr.get("web_url"),
                "merged_at": mr.get("merged_at"),
                "comments": filtered_comments,
            })
            total_comments += len(filtered_comments)

        return exported_mrs, total_comments

    def export_single(self, mr_iid: int):
        """Fetch all comments for one MR (no user filter) and export."""
        print(f"\nFetching comments for MR !{mr_iid}...")
        discussions = self.get_mr_comments(mr_iid)

        all_notes = [
            note
            for discussion in discussions
            for note in discussion.get("notes", [])
            if not note.get("system", True)
        ]
        comments = [self.normalize_comment(note) for note in all_notes]

        if not comments:
            print("\nNo comments found.")
            return

        output = {
            "metadata": {
                "gitlab_url": self.base_url,
                "project_id": self.project_id,
                "total_comments": len(comments),
                "exported_at": datetime.now(timezone.utc).isoformat(),
            },
            "merge_requests": [{"iid": mr_iid, "comments": comments}],
        }

        output_file = self.file_handler.save_export(
            output, "", "", filename=f"pr_comments_{mr_iid}"
        )
        print("\nExport completed!")
        print(f"  {output_file}")

    def export_multiple(self, per_page: int | None = None):
        """Fetch MRs page by page, write one export file per page when multi-page, one file otherwise."""
        print("\nRetrieving merge requests...")

        tracked_mr_iids = set(self.history.get("tracked_mr_iids", []))
        is_multi_file = per_page is None or per_page > self.max_per_page

        all_exported_mrs = []
        output_files = []

        for page_num, mrs_raw in self._iter_mr_pages(per_page):
            exported_mrs, total_comments = self._process_page(mrs_raw, tracked_mr_iids)

            if total_comments == 0:
                continue

            # Date range from MRs that have comments
            mrs_with_dates = [mr for mr in exported_mrs if mr.get("merged_at")]
            if not mrs_with_dates:
                continue

            latest_date = mrs_with_dates[0]["merged_at"][:10].replace("-", "")
            oldest_date = mrs_with_dates[-1]["merged_at"][:10].replace("-", "")

            output = {
                "metadata": {
                    "gitlab_url": self.base_url,
                    "project_id": self.project_id,
                    "start_date": oldest_date,
                    "end_date": latest_date,
                    "total_comments": total_comments,
                    "exported_at": datetime.now(timezone.utc).isoformat(),
                },
                "merge_requests": exported_mrs,
            }

            page_arg = page_num if is_multi_file else None
            output_file = self.file_handler.save_export(output, oldest_date, latest_date, page_arg)
            output_files.append(output_file)
            all_exported_mrs.extend(exported_mrs)

        if all_exported_mrs:
            self.file_handler.save_history(all_exported_mrs)
            print("\nExport completed!")
            print(f"Merge requests: {len(all_exported_mrs)}")
            print(f"Files written: {len(output_files)}")
            for f in output_files:
                print(f"  {f}")
        else:
            print("\nNo comments found.")


def main():
    print("=" * 50)
    print("GitLab Code Review Comment Exporter")
    print("=" * 50)

    exporter = GitLabCommentExporter()

    mode = input("\nFetch (1) single MR or (2) multiple MRs? [1/2]: ").strip()

    if mode == "1":
        raw_id = input("Enter MR IID: ").strip()
        exporter.export_single(int(raw_id))
    else:
        latest_at = exporter.history.get("latest_tracked_at")
        prompt = f"\nLatest MR amount to fetch (leave empty for all, last tracked: {latest_at}): "
        raw = input(prompt).strip()
        per_page = int(raw) if raw else None
        exporter.export_multiple(per_page=per_page)


if __name__ == "__main__":
    main()
