import json
import csv
import os
from pathlib import Path


def load_existing_decisions(csv_file):
    """Load existing moderation decisions to avoid re-reviewing content."""
    decisions = {}
    if os.path.exists(csv_file):
        with open(csv_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f, quoting=csv.QUOTE_ALL)
            for row in reader:
                decisions[row["id"]] = row["decision"]
    return decisions


def save_decision(csv_file, item_data):
    """Save a moderation decision to CSV."""
    file_exists = os.path.exists(csv_file)

    with open(csv_file, "a", newline="", encoding="utf-8") as f:
        fieldnames = [
            "id",
            "type",
            "title",
            "body",
            "decision",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)

        if not file_exists:
            writer.writeheader()

        writer.writerow(item_data)


def truncate_text(text, max_length=200):
    """Truncate text for display purposes."""
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."


def clean_text_for_csv(text, max_length=500):
    """Clean text for CSV storage by handling newlines and special characters."""
    if not text:
        return ""

    # Replace newlines with spaces to prevent CSV line breaks
    cleaned = text.replace("\n", " ").replace("\r", " ")

    # Replace multiple spaces with single space
    cleaned = " ".join(cleaned.split())

    # Truncate if too long
    if len(cleaned) > max_length:
        cleaned = cleaned[:max_length] + "..."

    return cleaned


def display_content(item_type, item_id, title, body):
    """Display content for review."""
    print("\n" + "=" * 80)
    print(f"Type: {item_type.upper()}")
    print(f"ID: {item_id}")

    if title:
        print(f"Title: {title}")

    print("Body:")
    print("-" * 40)
    print(body)
    print("-" * 40)


def get_user_decision():
    """Get moderation decision from user."""
    while True:
        print("\nModeration Options:")
        print("f - Flag for removal")
        print("i - Ignore (approve)")
        print("s - Skip for now")
        print("q - Quit")

        choice = input("\nYour decision (f/i/s/q): ").lower().strip()

        if choice in ["f", "flag"]:
            return "flagged"
        elif choice in ["i", "ignore"]:
            return "approved"
        elif choice in ["s", "skip"]:
            return "skipped"
        elif choice in ["q", "quit"]:
            return "quit"
        else:
            print("Invalid choice. Please enter f, i, s, or q.")


def moderate_content():
    """Main moderation function."""
    # Load data
    print("Loading Firestore data...")
    json_file = "firestore_posts_export_no_gifs.json"
    with open(Path(__file__).parent / json_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    csv_file = "moderation_decisions.csv"
    existing_decisions = load_existing_decisions(csv_file)

    print(f"Found {len(data)} posts to review.")
    print(f"Already reviewed {len(existing_decisions)} items.")

    total_items = 0
    reviewed_items = 0

    # Count total items for progress tracking
    for post_data in data.values():
        total_items += 1  # Post
        total_items += len(post_data.get("comments", {}))  # Comments

    print(f"Total items to review: {total_items}")
    print(f"Remaining items: {total_items - len(existing_decisions)}")

    try:
        for post_id, post_data in data.items():
            # Review post
            if post_id not in existing_decisions:
                display_content(
                    item_type="post",
                    item_id=post_id,
                    title=post_data.get("title", ""),
                    body=post_data.get("body", ""),
                )

                print(
                    f"\nProgress: {reviewed_items + 1}/{total_items - len(existing_decisions)}"
                )

                decision = get_user_decision()

                if decision == "quit":
                    print("Quitting moderation session.")
                    break
                elif decision != "skipped":
                    # Save decision
                    item_data = {
                        "id": post_id,
                        "type": "post",
                        "title": clean_text_for_csv(post_data.get("title", ""), 200),
                        "body": clean_text_for_csv(post_data.get("body", ""), 500),
                        "decision": decision,
                    }
                    save_decision(csv_file, item_data)
                    print(f"✓ Post {decision}")

                reviewed_items += 1

            # Review comments
            comments = post_data.get("comments", {})
            for comment_id, comment_data in comments.items():
                if comment_id not in existing_decisions:
                    display_content(
                        item_type="comment",
                        item_id=comment_id,
                        title=None,
                        body=comment_data.get("body", ""),
                    )

                    print(f"Parent Post: {post_data.get('title', 'No title')}")
                    print(
                        f"Progress: {reviewed_items + 1}/{total_items - len(existing_decisions)}"
                    )

                    decision = get_user_decision()

                    if decision == "quit":
                        print("Quitting moderation session.")
                        return
                    elif decision != "skipped":
                        # Save decision
                        item_data = {
                            "id": comment_id,
                            "type": "comment",
                            "title": "",
                            "body": clean_text_for_csv(
                                comment_data.get("body", ""), 500
                            ),
                            "decision": decision,
                        }
                        save_decision(csv_file, item_data)
                        print(f"✓ Comment {decision}")

                    reviewed_items += 1

    except KeyboardInterrupt:
        print("\n\nModeration session interrupted by user.")

    print("\nModeration session complete!")
    print(f"Decisions saved to: {csv_file}")

    # Show summary
    final_decisions = load_existing_decisions(csv_file)
    flagged_count = sum(
        1 for decision in final_decisions.values() if decision == "flagged"
    )
    approved_count = sum(
        1 for decision in final_decisions.values() if decision == "approved"
    )

    print("\nSummary:")
    print(f"Total reviewed: {len(final_decisions)}")
    print(f"Flagged: {flagged_count}")
    print(f"Approved: {approved_count}")


if __name__ == "__main__":
    print("Content Moderation Tool")
    print("=" * 22)
    moderate_content()
