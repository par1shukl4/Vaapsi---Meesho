from dataclasses import dataclass
from math import asin, cos, radians, sin, sqrt

from backend.models.domain import Address


@dataclass(frozen=True)
class DistanceResult:
    distance_meters: float | None
    valid: bool
    reason: str


def haversine_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius_m = 6_371_000
    d_lat = radians(lat2 - lat1)
    d_lon = radians(lon2 - lon1)
    a = (
        sin(d_lat / 2) ** 2
        + cos(radians(lat1)) * cos(radians(lat2)) * sin(d_lon / 2) ** 2
    )
    return 2 * radius_m * asin(sqrt(a))


class MapsClient:
    async def validate_attempt(
        self,
        address: Address,
        attempt_latitude: float | None,
        attempt_longitude: float | None,
        threshold_meters: int,
    ) -> DistanceResult:
        if (
            address.latitude is None
            or address.longitude is None
            or attempt_latitude is None
            or attempt_longitude is None
        ):
            return DistanceResult(None, True, "GPS validation skipped because coordinates are incomplete.")

        distance = haversine_meters(
            address.latitude,
            address.longitude,
            attempt_latitude,
            attempt_longitude,
        )
        if distance > threshold_meters:
            return DistanceResult(distance, False, "Attempt GPS is materially distant from address.")
        return DistanceResult(distance, True, "Attempt GPS is within acceptable delivery radius.")
