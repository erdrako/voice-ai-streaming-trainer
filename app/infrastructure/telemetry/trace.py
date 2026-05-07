from dataclasses import dataclass, field
import time


@dataclass
class Trace:
    """
    Cross-cutting telemetry object for measuring workflow latency.

    It is intentionally simple: the use case marks milestones, and the final
    metrics event exposes elapsed milliseconds. In a larger system this could be
    replaced by OpenTelemetry, Prometheus histograms, Datadog spans, or another
    tracing adapter.

    Expansion point:
    - Add a `TraceProvider` contract if tracing needs to become replaceable.
    - Keep use cases marking business milestones, not vendor-specific spans.
    """

    started_at: float = field(default_factory=time.perf_counter)
    marks: dict[str, float] = field(default_factory=dict)

    def mark(self, name: str) -> None:
        """Record milliseconds elapsed since this trace started."""

        self.marks[name] = round((time.perf_counter() - self.started_at) * 1000, 2)

    def snapshot(self) -> dict[str, float]:
        """Return a copy suitable for event payloads and persistence."""

        return dict(self.marks)
