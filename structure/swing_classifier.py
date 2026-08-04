"""Swing classifier.

Converts raw swings into market structure labels (HH, HL, LH, LL) by
comparing each swing to the previous swing of the same type.
"""

from __future__ import annotations

from dataclasses import dataclass

from structure.enums import StructureLabel, SwingType
from structure.models import StructurePoint, Swing


@dataclass(slots=True)
class SwingClassifier:
    """Classifies swings into market-structure labels."""

    def classify(self, swings: list[Swing]) -> list[StructurePoint]:
        """Classify each swing relative to the previous same-type swing.

        Args:
            swings: Detected swings, sorted by index.

        Returns:
            A list of :class:`StructurePoint` with labels. The first swing
            of each type has no prior same-type reference and is labelled
            with the neutral baseline (``HH`` for the first high, ``LL``
            for the first low).
        """
        points: list[StructurePoint] = []
        last_high: StructurePoint | None = None
        last_low: StructurePoint | None = None

        for swing in swings:
            swing_type = swing.swing_type

            if swing_type == SwingType.HIGH:
                if last_high is None:
                    label = StructureLabel.HH
                else:
                    label = (
                        StructureLabel.HH
                        if swing.price > last_high.price
                        else StructureLabel.LH
                    )
                point = StructurePoint(
                    index=swing.index,
                    timestamp=swing.timestamp,
                    price=swing.price,
                    swing_type=swing_type,
                    label=label,
                )
                last_high = point
            else:
                if last_low is None:
                    label = StructureLabel.LL
                else:
                    label = (
                        StructureLabel.LL
                        if swing.price < last_low.price
                        else StructureLabel.HL
                    )
                point = StructurePoint(
                    index=swing.index,
                    timestamp=swing.timestamp,
                    price=swing.price,
                    swing_type=swing_type,
                    label=label,
                )
                last_low = point

            points.append(point)

        return points


__all__ = ["SwingClassifier"]
