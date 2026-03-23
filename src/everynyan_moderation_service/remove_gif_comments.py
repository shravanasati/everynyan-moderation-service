import json
import re


def is_gif_only_comment(body):
    """
    Check if a comment body contains only GIF links/embeds and no meaningful text.

    Args:
        body (str): The comment body text

    Returns:
        bool: True if the comment is GIF-only, False otherwise
    """
    if not body or not body.strip():
        return True  # Empty comments are considered GIF-only

    # Common GIF patterns
    gif_patterns = [
        r"https?://.*\.gif\b",  # Direct GIF URLs
        r"https?://giphy\.com/\S+",  # Giphy links
        r"https?://tenor\.com/\S+",  # Tenor links
        r"https?://media\.giphy\.com/\S+",  # Giphy media links
        r"https?://c\.tenor\.com/\S+",  # Tenor CDN links
        r"\[gif\].*?\[/gif\]",  # GIF BBCode tags
        r"!\[.*?\]\(.*?\.gif.*?\)",  # Markdown image with GIF
        r"<img.*?\.gif.*?>",  # HTML img tags with GIF
        r"https?://imgur\.com/\S+\.gif",  # Imgur GIF links
    ]

    # Remove all GIF-related content
    cleaned_body = body
    for pattern in gif_patterns:
        cleaned_body = re.sub(pattern, "", cleaned_body, flags=re.IGNORECASE)

    # Remove common whitespace, punctuation, and filler words
    cleaned_body = re.sub(r"[^\w\s]", "", cleaned_body)  # Remove punctuation
    cleaned_body = re.sub(r"\s+", " ", cleaned_body)  # Normalize whitespace
    cleaned_body = cleaned_body.strip().lower()

    # List of filler words/phrases that don't constitute meaningful content
    filler_words = {
        "",
        "gif",
        "lol",
        "lmao",
        "haha",
        "hehe",
        "lmfao",
        "rofl",
        "this",
        "that",
        "yes",
        "no",
        "true",
        "same",
        "mood",
        "me",
        "nice",
        "cool",
        "wow",
        "omg",
        "tbh",
        "ngl",
        "fr",
        "imo",
        "yep",
        "nope",
        "yeah",
        "yup",
        "ok",
        "okay",
        "good",
        "bad",
        "exactly",
        "agree",
        "disagree",
        "facts",
        "cap",
        "nocap",
    }

    # Split into words and check if only filler words remain
    words = cleaned_body.split()
    meaningful_words = [
        word for word in words if word not in filler_words and len(word) > 2
    ]

    # If no meaningful words remain after cleaning, it's likely a GIF-only comment
    return len(meaningful_words) == 0


def remove_gif_comments(input_file, output_file):
    """
    Remove GIF-only comments from the Firestore export and save to a new file.

    Args:
        input_file (str): Path to the input JSON file
        output_file (str): Path to the output JSON file
    """
    print(f"Loading data from {input_file}...")

    with open(input_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    total_posts = len(data)
    total_comments_before = 0
    total_comments_after = 0
    gif_comments_removed = 0
    posts_processed = 0

    # Count total comments before processing
    for post_data in data.values():
        total_comments_before += len(post_data.get("comments", {}))

    print(f"Found {total_posts} posts with {total_comments_before} total comments")
    print("Processing comments...")

    # Process each post
    for post_id, post_data in data.items():
        comments = post_data.get("comments", {})
        comments_to_keep = {}

        for comment_id, comment_data in comments.items():
            comment_body = comment_data.get("body", "")

            if not is_gif_only_comment(comment_body):
                comments_to_keep[comment_id] = comment_data
            else:
                gif_comments_removed += 1
                print(
                    f"Removing GIF-only comment: {comment_id[:8]}... - '{comment_body[:50]}{'...' if len(comment_body) > 50 else ''}'"
                )

        # Update the post with filtered comments
        post_data["comments"] = comments_to_keep
        total_comments_after += len(comments_to_keep)

        posts_processed += 1
        if posts_processed % 10 == 0:
            print(f"Processed {posts_processed}/{total_posts} posts...")

    print(f"\nSaving cleaned data to {output_file}...")

    # Save the cleaned data
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    # Print summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Posts processed: {total_posts}")
    print(f"Comments before: {total_comments_before}")
    print(f"Comments after: {total_comments_after}")
    print(f"GIF-only comments removed: {gif_comments_removed}")
    print(f"Reduction: {gif_comments_removed / total_comments_before * 100:.1f}%")
    print(f"Output saved to: {output_file}")

    return {
        "posts_processed": total_posts,
        "comments_before": total_comments_before,
        "comments_after": total_comments_after,
        "comments_removed": gif_comments_removed,
        "reduction_percentage": gif_comments_removed / total_comments_before * 100,
    }


def main():
    """Main function to run the GIF comment removal process."""
    input_file = "firestore_posts_export.json"
    output_file = "firestore_posts_export_no_gifs.json"

    try:
        stats = remove_gif_comments(input_file, output_file)

        # Verify the output
        print("\nVerifying output file...")
        with open(output_file, "r", encoding="utf-8") as f:
            cleaned_data = json.load(f)

        verification_comment_count = sum(
            len(post.get("comments", {})) for post in cleaned_data.values()
        )

        if verification_comment_count == stats["comments_after"]:
            print("✓ Output file verification successful!")
        else:
            print(
                f"⚠ Warning: Expected {stats['comments_after']} comments, but found {verification_comment_count}"
            )

    except FileNotFoundError:
        print(f"Error: Input file '{input_file}' not found.")
        print("Make sure you have run the download script first to generate the data.")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
