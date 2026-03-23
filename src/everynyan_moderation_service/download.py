import firebase_admin
from firebase_admin import credentials, firestore
import json
from concurrent.futures import ThreadPoolExecutor
import time
from datetime import datetime

# Try to import DatetimeWithNanoseconds from different possible locations
try:
    from google.cloud.firestore_v1.base_document import DatetimeWithNanoseconds
except ImportError:
    try:
        from google.cloud.firestore import DatetimeWithNanoseconds
    except ImportError:
        # Fallback for older versions
        try:
            from google.api_core.datetime_helpers import DatetimeWithNanoseconds
        except ImportError:
            # If all imports fail, we'll handle this in the encoder
            DatetimeWithNanoseconds = None


# Custom JSON encoder to handle Firestore DatetimeWithNanoseconds
class FirestoreJSONEncoder(json.JSONEncoder):
    def default(self, o):
        # Handle DatetimeWithNanoseconds if it's available
        if DatetimeWithNanoseconds is not None and isinstance(
            o, DatetimeWithNanoseconds
        ):
            # Convert to ISO format string
            return o.isoformat()
        elif isinstance(o, datetime):
            # Handle regular datetime objects too
            return o.isoformat()
        # Also handle any object with an isoformat method (duck typing)
        elif hasattr(o, "isoformat") and callable(getattr(o, "isoformat")):
            return o.isoformat()
        return super().default(o)


# Initialize Firebase Admin SDK
# Make sure you have your service account JSON key downloaded
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)

db = firestore.client()


def fetch_subcollection(doc_ref, subcollection_name):
    """Fetch all documents from a subcollection of a document."""
    sub_docs = doc_ref.collection(subcollection_name).stream()
    return {doc.id: doc.to_dict() for doc in sub_docs}


def fetch_single_post_with_comments(post):
    """Fetch a single post with its comments."""
    post_data = post.to_dict()
    post_data["id"] = post.id

    # Fetch comments subcollection
    comments = fetch_subcollection(post.reference, "comments")
    post_data["comments"] = comments

    return post.id, post_data


def fetch_posts_with_comments():
    """Fetch all posts with comments using concurrent processing."""
    posts_ref = db.collection("posts")
    all_posts_docs = list(posts_ref.stream())

    print(f"Found {len(all_posts_docs)} posts to process...")

    posts = {}

    # Use ThreadPoolExecutor for concurrent processing
    # Adjust max_workers based on your Firebase quota and performance needs
    max_workers = min(10, len(all_posts_docs))

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all post processing tasks
        future_to_post = {
            executor.submit(fetch_single_post_with_comments, post): post
            for post in all_posts_docs
        }

        # Collect results as they complete
        completed = 0
        for future in future_to_post:
            try:
                post_id, post_data = future.result()
                posts[post_id] = post_data
                completed += 1
                print(f"Processed post {completed}/{len(all_posts_docs)}: {post_id}")
            except Exception as exc:
                post = future_to_post[future]
                print(f"Post {post.id} generated an exception: {exc}")
                completed += 1

    return posts


if __name__ == "__main__":
    print("Starting concurrent Firestore data export...")
    start_time = time.time()

    all_posts = fetch_posts_with_comments()

    # Save to JSON file
    with open("firestore_posts_export.json", "w", encoding="utf-8") as f:
        json.dump(all_posts, f, indent=2, ensure_ascii=False, cls=FirestoreJSONEncoder)

    end_time = time.time()
    duration = end_time - start_time

    print("Export complete! Data saved to firestore_posts_export.json")
    print(f"Processing time: {duration:.2f} seconds")
    print(f"Total posts exported: {len(all_posts)}")
