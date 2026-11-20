"""Authoritative vertical profile metadata for the soil experiment."""

from dataclasses import asdict, dataclass


@dataclass(frozen=True, slots=True)
class DepthInterval:
    code: str
    top_cm: int
    bottom_cm: int

    @property
    def thickness_cm(self) -> int:
        return self.bottom_cm - self.top_cm

    @property
    def midpoint_cm(self) -> float:
        return (self.top_cm + self.bottom_cm) / 2

    def to_dict(self) -> dict:
        return {**asdict(self), "thickness_cm": self.thickness_cm,
                "midpoint_cm": self.midpoint_cm}


DEPTH_PROFILE: tuple[DepthInterval, ...] = (
    DepthInterval("A", 0, 10),
    DepthInterval("B", 10, 20),
    DepthInterval("C", 20, 40),
    DepthInterval("D", 40, 60),
    DepthInterval("E", 60, 80),
    DepthInterval("F", 80, 100),
    DepthInterval("G", 100, 130),
    DepthInterval("H", 130, 160),
    DepthInterval("I", 160, 200),
)

DEPTH_BY_CODE = {item.code: item for item in DEPTH_PROFILE}


def validate_depth_profile() -> None:
    """Fail fast if intervals are not contiguous and cover 0–200 cm."""
    if not DEPTH_PROFILE or DEPTH_PROFILE[0].top_cm != 0:
        raise ValueError("Depth profile must start at 0 cm")
    for previous, current in zip(DEPTH_PROFILE, DEPTH_PROFILE[1:]):
        if previous.bottom_cm != current.top_cm:
            raise ValueError(
                f"Non-contiguous intervals: {previous.code} -> {current.code}"
            )
    if DEPTH_PROFILE[-1].bottom_cm != 200:
        raise ValueError("Depth profile must end at 200 cm")
    if any(item.thickness_cm <= 0 for item in DEPTH_PROFILE):
        raise ValueError("All depth intervals must have positive thickness")


def depth_metadata() -> list[dict]:
    validate_depth_profile()
    return [item.to_dict() for item in DEPTH_PROFILE]
