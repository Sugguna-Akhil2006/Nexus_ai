"""Rating service capturing user feedback and updating package ratings."""

import threading
from backend.marketplace.models import Rating, MarketplacePackage
from backend.marketplace.package_registry import PackageRegistry


class RatingService:
    """Manages scoring, downloads tracking, and reviews for marketplace packages."""

    def __init__(self, registry: PackageRegistry) -> None:
        self.registry = registry
        self._lock = threading.RLock()

    def submit_rating(self, package_id: str, version: str, user_id: str, score: int, comment: str = "") -> None:
        """Adds or updates a user rating for a package version, updating statistics."""
        with self._lock:
            pkg = self.registry.get_package_metadata(package_id, version)
            if not pkg:
                raise ValueError(f"Package '{package_id}' version '{version}' not found.")

            # Create or update rating
            new_rating = Rating(user_id=user_id, score=score, comment=comment)
            existing_idx = -1
            for i, r in enumerate(pkg.ratings):
                if r.user_id == user_id:
                    existing_idx = i
                    break

            if existing_idx >= 0:
                pkg.ratings[existing_idx] = new_rating
            else:
                pkg.ratings.append(new_rating)

            # Recalculate average rating
            total_score = sum(r.score for r in pkg.ratings)
            pkg.ratings_count = len(pkg.ratings)
            pkg.average_rating = total_score / pkg.ratings_count

            # Sync update to all versions for user simplicity if necessary
            for other_ver in self.registry.get_package_versions(package_id):
                other_ver.ratings_count = pkg.ratings_count
                other_ver.average_rating = pkg.average_rating

    def increment_downloads(self, package_id: str) -> None:
        """Increments download counters across all versions of a package."""
        with self._lock:
            for p in self.registry.get_package_versions(package_id):
                p.downloads += 1
