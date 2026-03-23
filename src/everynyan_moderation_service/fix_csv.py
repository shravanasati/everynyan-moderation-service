import csv
import json
import os


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


def fix_existing_csv(csv_file, backup_suffix="_backup"):
    """Fix an existing CSV file that may have malformed rows due to newlines."""
    if not os.path.exists(csv_file):
        print(f"CSV file {csv_file} does not exist.")
        return

    backup_file = csv_file.replace(".csv", f"{backup_suffix}.csv")

    # Create backup
    print(f"Creating backup: {backup_file}")
    os.rename(csv_file, backup_file)

    # Try to read the original data and reconstruct it
    print(f"Attempting to fix {backup_file}...")

    fixed_rows = []
    malformed_rows = []

    try:
        with open(backup_file, "r", encoding="utf-8") as f:
            content = f.read()

        # Try to parse line by line, handling malformed entries
        lines = content.split("\n")
        header_line = lines[0] if lines else ""

        # Expected fieldnames
        expected_fields = ["id", "type", "title", "body", "decision"]

        current_row_parts = []

        for i, line in enumerate(lines[1:], 1):  # Skip header
            if not line.strip():
                continue

            # Try to parse this line as a complete CSV row
            try:
                test_reader = csv.reader([line])
                row_data = next(test_reader)

                if len(row_data) == len(expected_fields):
                    # This looks like a complete row
                    if current_row_parts:
                        # We have accumulated parts, this means the previous was malformed
                        malformed_content = " ".join(current_row_parts)
                        malformed_rows.append(
                            f"Line {i - len(current_row_parts)} to {i - 1}: {malformed_content[:100]}..."
                        )
                        current_row_parts = []

                    # Clean the row data
                    cleaned_row = {
                        expected_fields[j]: clean_text_for_csv(
                            row_data[j], 500 if j == 3 else 200
                        )
                        for j in range(len(row_data))
                    }
                    fixed_rows.append(cleaned_row)
                else:
                    # This might be part of a malformed row
                    current_row_parts.append(line.strip())

            except csv.Error:
                # This line couldn't be parsed, probably part of a malformed row
                current_row_parts.append(line.strip())

        # Handle any remaining malformed parts
        if current_row_parts:
            malformed_content = " ".join(current_row_parts)
            malformed_rows.append(f"End of file: {malformed_content[:100]}...")

    except Exception as e:
        print(f"Error reading backup file: {e}")
        print("You may need to manually fix the CSV file.")
        return

    # Write the fixed CSV
    print(f"Writing fixed CSV to {csv_file}")
    with open(csv_file, "w", newline="", encoding="utf-8") as f:
        if fixed_rows:
            writer = csv.DictWriter(
                f, fieldnames=expected_fields, quoting=csv.QUOTE_ALL
            )
            writer.writeheader()
            writer.writerows(fixed_rows)

    print(f"\nResults:")
    print(f"✓ Fixed rows written: {len(fixed_rows)}")
    print(f"⚠ Malformed entries found: {len(malformed_rows)}")

    if malformed_rows:
        print(f"\nMalformed entries (you may need to re-moderate these):")
        for entry in malformed_rows[:5]:  # Show first 5
            print(f"  - {entry}")
        if len(malformed_rows) > 5:
            print(f"  ... and {len(malformed_rows) - 5} more")

    print(f"\nBackup saved as: {backup_file}")


def rebuild_csv_from_source(csv_file, json_file):
    """Rebuild the CSV from the original JSON source and existing decisions."""
    print(f"Rebuilding CSV from source data...")

    # Load existing decisions to preserve them
    existing_decisions = {}
    if os.path.exists(csv_file):
        backup_file = csv_file.replace(".csv", "_before_rebuild.csv")
        print(f"Backing up existing CSV to: {backup_file}")
        os.rename(csv_file, backup_file)

        # Try to extract valid decisions
        try:
            with open(backup_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if "id" in row and "decision" in row:
                        existing_decisions[row["id"]] = row["decision"]
        except:
            print("Could not read existing decisions from backup file.")

    # Load source data
    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Rebuild CSV with proper formatting
    rebuilt_rows = []

    for post_id, post_data in data.items():
        if post_id in existing_decisions:
            row = {
                "id": post_id,
                "type": "post",
                "title": clean_text_for_csv(post_data.get("title", ""), 200),
                "body": clean_text_for_csv(post_data.get("body", ""), 500),
                "decision": existing_decisions[post_id],
            }
            rebuilt_rows.append(row)

        # Handle comments
        comments = post_data.get("comments", {})
        for comment_id, comment_data in comments.items():
            if comment_id in existing_decisions:
                row = {
                    "id": comment_id,
                    "type": "comment",
                    "title": "",
                    "body": clean_text_for_csv(comment_data.get("body", ""), 500),
                    "decision": existing_decisions[comment_id],
                }
                rebuilt_rows.append(row)

    # Write rebuilt CSV
    with open(csv_file, "w", newline="", encoding="utf-8") as f:
        fieldnames = ["id", "type", "title", "body", "decision"]
        writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
        writer.writeheader()
        writer.writerows(rebuilt_rows)

    print(f"✓ Rebuilt CSV with {len(rebuilt_rows)} properly formatted rows")
    print(f"✓ Preserved {len(existing_decisions)} existing decisions")


if __name__ == "__main__":
    csv_file = "moderation_decisions.csv"
    json_file = "firestore_posts_export_no_gifs.json"

    if os.path.exists(csv_file):
        print("Found existing CSV file.")
        print("Choose an option:")
        print("1. Try to fix the existing CSV file (recommended)")
        print(
            "2. Rebuild CSV from source JSON (preserves decisions but requires source)"
        )
        print("3. Exit")

        choice = input("Enter choice (1/2/3): ").strip()

        if choice == "1":
            fix_existing_csv(csv_file)
        elif choice == "2":
            if os.path.exists(json_file):
                rebuild_csv_from_source(csv_file, json_file)
            else:
                print(f"Source JSON file {json_file} not found.")
        else:
            print("Exiting without changes.")
    else:
        print(f"No existing CSV file found at {csv_file}")
