"""Time-based clustering algorithm for temporal data analysis.

See docs/time-clustering-algorithm.md for detailed mathematical framework
of note existence time indexing and memory fragmentation probability calculation.
"""
from typing import List, Dict, Any, Union
from datetime import datetime
import math


def analyze_temporal_patterns(
    data_points: List[Dict[str, Any]],
    time_key: str = 'time',
    data_key: str = 'data',
    current_time: datetime = None
) -> Dict[str, Any]:
    """Comprehensive temporal analysis combining clustering and concentration metrics.

    This function provides both time clustering ranges and memory fragmentation analysis
    based on the mathematical framework of existence weights and normalized variance.

    Args:
        data_points: List of dictionaries containing time and data attributes
        time_key: Key name for the time attribute (default: 'time')
        data_key: Key name for the data attribute (default: 'data')
        current_time: Current observation time (defaults to datetime.now())

    Returns:
        Dictionary containing:
        - clusters: Time clustering ranges with metadata
        - concentration: Memory fragmentation probability (0-1)
        - metadata: Additional analysis metrics
    """
    if not data_points:
        return {
            'clusters': [],
            'concentration': 0.0,
            'metadata': {'total_points': 0}
        }

    if current_time is None:
        current_time = datetime.now()

    # Sort by time to ensure proper ordering
    sorted_points = sorted(data_points, key=lambda x: x[time_key])

    # Calculate concentration using the mathematical framework
    concentration = calculate_temporal_concentration(
        data_points, time_key, current_time
    )

    # Perform time-based clustering for temporal ranges
    clusters = _cluster_by_temporal_gaps(sorted_points, time_key, data_key)

    # Calculate additional metadata
    n = len(data_points)
    times = [point[time_key] for point in data_points]
    min_time = min(times)
    max_time = max(times)
    total_timespan = (max_time - min_time).total_seconds()

    metadata = {
        'total_points': n,
        'min_time': min_time,
        'max_time': max_time,
        'total_timespan_seconds': total_timespan,
        'current_time': current_time,
        'average_time_gap': total_timespan / (n - 1) if n > 1 else 0
    }

    return {
        'clusters': clusters,
        'concentration': concentration,
        'metadata': metadata
    }


def _cluster_by_temporal_gaps(
    sorted_points: List[Dict[str, Any]],
    time_key: str = 'time',
    data_key: str = 'data'
) -> List[Dict[str, Any]]:
    """Internal function to cluster data points based on significant time gaps."""
    n = len(sorted_points)
    if n == 1:
        return [{
            'points': sorted_points,
            'start_time': sorted_points[0][time_key],
            'end_time': sorted_points[0][time_key],
            'count': 1,
            'timespan_seconds': 0
        }]

    # Calculate time deltas between consecutive points
    deltas = []
    for i in range(n - 1):
        current_time = sorted_points[i][time_key]
        next_time = sorted_points[i + 1][time_key]
        delta = (next_time - current_time).total_seconds()
        deltas.append(delta)

    # Calculate mean and standard deviation of deltas
    mu = sum(deltas) / len(deltas)
    if len(deltas) > 1:
        sigma = math.sqrt(sum((x - mu) ** 2 for x in deltas) / (len(deltas) - 1))
    else:
        sigma = 0.0

    # Split segments where delta > mean + 1*std (significant time gap)
    segments = []
    start_idx = 0

    for i, delta in enumerate(deltas):
        if sigma > 0 and delta > mu + sigma:
            # Create segment from start_idx to i+1
            segment_points = sorted_points[start_idx:i + 1]
            segment_start = segment_points[0][time_key]
            segment_end = segment_points[-1][time_key]
            timespan = (segment_end - segment_start).total_seconds()
            segments.append({
                'points': segment_points,
                'start_time': segment_start,
                'end_time': segment_end,
                'count': len(segment_points),
                'timespan_seconds': timespan
            })
            start_idx = i + 1

    # Add the final segment
    if start_idx < n:
        final_segment_points = sorted_points[start_idx:]
        if final_segment_points:
            segment_start = final_segment_points[0][time_key]
            segment_end = final_segment_points[-1][time_key]
            timespan = (segment_end - segment_start).total_seconds()
            segments.append({
                'points': final_segment_points,
                'start_time': segment_start,
                'end_time': segment_end,
                'count': len(final_segment_points),
                'timespan_seconds': timespan
            })

    return segments


def calculate_temporal_concentration(data_points: List[Dict[str, Any]], time_key: str = 'time', current_time: datetime = None) -> float:
    """Calculate temporal concentration index using existence weights and normalized variance.

    Based on the mathematical framework:
    - Existence time: d_i(T) = T - t_i
    - Total existence time: D(T) = sum(d_i(T)) = nT - sum(t_i)
    - Existence weights: w_i(T) = d_i(T) / D(T) = (T - t_i) / (nT - sum(t_i))
    - Normalized variance: C_norm = (n / (n-1)) * sum((w_i - 1/n)^2)

    Args:
        data_points: List of dictionaries containing time attributes
        time_key: Key name for the time attribute
        current_time: Current observation time (defaults to datetime.now())

    Returns:
        Concentration index between 0.0 (uniform) and 1.0 (completely concentrated)
    """
    if not data_points or len(data_points) <= 1:
        return 0.0

    if current_time is None:
        current_time = datetime.now()

    n = len(data_points)
    times = [point[time_key] for point in data_points]

    # Convert all times to timestamps for calculation
    time_timestamps = [t.timestamp() for t in times]
    current_timestamp = current_time.timestamp()

    # Calculate existence times: d_i(T) = T - t_i
    existence_times = [current_timestamp - t_ts for t_ts in time_timestamps]

    # Ensure all existence times are non-negative
    existence_times = [max(et, 0) for et in existence_times]

    # Calculate total existence time: D(T) = sum(d_i(T)) = nT - sum(t_i)
    total_existence_time = sum(existence_times)

    # Handle edge case where all notes are from the future or same time
    if total_existence_time == 0:
        return 0.0

    # Calculate existence weights: w_i(T) = d_i(T) / D(T)
    weights = [et / total_existence_time for et in existence_times]

    # Calculate normalized variance: C_norm = (n / (n-1)) * sum((w_i - 1/n)^2)
    uniform_weight = 1.0 / n
    sum_squared_deviations = sum((w - uniform_weight) ** 2 for w in weights)
    concentration = (n / (n - 1)) * sum_squared_deviations

    # Clamp to [0, 1] range to handle floating point precision issues
    return max(0.0, min(1.0, concentration))
