"""
OpenTelemetry tracing and span utilities.
"""

from collections.abc import Generator
from contextlib import contextmanager
from typing import Any

from opentelemetry import trace

tracer = trace.get_tracer("narrative-continuity-copilot", "0.1.0")


@contextmanager
def trace_span(
    span_name: str, attributes: dict[str, Any] | None = None
) -> Generator[trace.Span, None, None]:
    """
    Context manager for creating OpenTelemetry spans with safe metadata attributes.
    Raw manuscript content is never stored in attributes.
    """
    with tracer.start_as_current_span(span_name) as span:
        if attributes:
            for k, v in attributes.items():
                # Disallow raw text payload attributes
                if "text" in k.lower() or "content" in k.lower() or "quote" in k.lower():
                    continue
                if isinstance(v, (str, int, float, bool)):
                    span.set_attribute(k, v)
        yield span
