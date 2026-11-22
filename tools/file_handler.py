import json

from pathlib import Path

class ExportFileHandler:

    def __init__(self, output_dir: str = "output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

    def save_export(
        self,
        output: dict,
        oldest_date: str,
        latest_date: str,
        page: int | None = None,
        filename: str | None = None,
    ) -> Path:
        """Write export JSON. Adds _p{page} suffix when page is given. filename overrides default stem."""
        if filename:
            resolved = f"{filename}.json"
        else:
            suffix = f"_p{page}" if page is not None else ""
            resolved = f"pr_comments_{oldest_date}_{latest_date}{suffix}.json"
        output_file = self.output_dir / resolved
        with output_file.open("w", encoding="utf-8") as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        return output_file

    def save_history(self, exported_mrs: list) -> None:
        """Merge new MR IIDs into output/history.json to skip them on future runs."""
        history_file = self.output_dir / "history.json"
        latest_merged_at = max(
            (mr["merged_at"] for mr in exported_mrs if mr.get("merged_at")),
            default=None,
        )
        existing = self.load_history()
        existing_iids = set(existing.get("tracked_mr_iids", []))
        existing_tracked_at = existing.get("latest_tracked_at", None)
        latest_tracked_at = max(
            filter(None, [existing_tracked_at, latest_merged_at]),
            default=None,
        )
        new_iids = {mr["iid"] for mr in exported_mrs}
        history = {
            "latest_tracked_at": latest_tracked_at,
            "tracked_mr_iids": sorted(existing_iids | new_iids),
        }
        with history_file.open("w", encoding="utf-8") as f:
            json.dump(history, f, indent=2, ensure_ascii=False)

    def load_history(self) -> dict:
        """Read output/history.json. Returns empty-state dict if file absent."""
        history_file = self.output_dir / "history.json"
        if history_file.exists():
            with history_file.open("r", encoding="utf-8") as f:
                return json.load(f)
        return {"latest_tracked_at": None, "tracked_mr_iids": []}
