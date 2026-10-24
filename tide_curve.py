"""Visual interpolation between known tide extrema, never a new tide forecast."""
import math
from datetime import datetime, timezone

def estimated_curve(events, step_minutes=10):
    """Join alternating extrema with bounded half-cosines and zero endpoint slope.

    Adjacent days' prediction events bracket local midnight. No extrapolation,
    invented cycles, or bridging of missing events longer than 18 hours.
    """
    anchors = {}
    for event in events:
        try:
            stamp = datetime.fromisoformat(event['time'].replace('Z', '+00:00')).timestamp()
            height = float(event['height'])
            if math.isfinite(stamp) and math.isfinite(height) and event['type'] in {'H', 'L'}:
                anchors[stamp] = (height, event['type'])
        except (ValueError, KeyError, TypeError):
            continue
    if step_minutes <= 0:
        raise ValueError('Sampling step must be positive.')
    ordered = sorted(anchors.items())
    points = {}
    for (start, (low, left_type)), (end, (high, right_type)) in zip(ordered, ordered[1:]):
        duration = end - start
        if left_type == right_type or not 0 < duration <= 18*3600:
            continue
        # Refuse contradictory extrema instead of implying an extra tide cycle.
        if (left_type == 'L' and high < low) or (left_type == 'H' and high > low):
            continue
        stamp = start
        while stamp < end:
            fraction = (stamp-start)/duration
            points[stamp] = low + (high-low)*(1-math.cos(math.pi*fraction))/2
            stamp += step_minutes*60
        points[end] = high
    result = []
    previous = None
    for stamp, height in sorted(points.items()):
        if previous is not None and stamp-previous > step_minutes*60+1:
            # A null sample makes the chart break instead of drawing across a gap.
            result.append(dict(time=datetime.fromtimestamp((previous+stamp)/2, timezone.utc).isoformat(), height=None))
        result.append(dict(time=datetime.fromtimestamp(stamp, timezone.utc).isoformat(), height=height))
        previous = stamp
    return result

def with_fallback_curve(result):
    if result.get('curve'):
        result['curve_kind'] = 'provider'
    elif result.get('available', True):
        result['curve'] = estimated_curve(result.get('events', []))
        result['curve_kind'] = 'interpolated' if result['curve'] else 'none'
        result['chart_note'] = ('Estimated visual curve between provider high/low events, including adjacent-day turning points. Dashed lines are interpolation, not hourly provider predictions or observed measurements. No extrapolation.' if result['curve'] else 'Not enough consecutive high/low events to estimate a curve. Available events remain in the table.')
    else:
        result['curve_kind'] = 'none'
    result['timer_lows'] = timer_lows(result)
    return result

def timer_lows(result):
    """Prefer exact provider low events; otherwise find bracketed curve minima."""
    known = result.get('lows') or [p for p in result.get('events', []) if p.get('type') == 'L']
    if known:
        return [dict(p, timing_source='provider') for p in sorted(known,key=lambda p:p['time'])]
    points = sorted(result.get('curve', []),key=lambda p:p['time'])
    lows = []
    for before, point, after in zip(points,points[1:],points[2:]):
        heights = [p.get('height') for p in (before,point,after)]
        if any(h is None or not math.isfinite(h) for h in heights):
            continue
        stamps = [datetime.fromisoformat(p['time'].replace('Z','+00:00')).timestamp() for p in (before,point,after)]
        if not all(0 < b-a <= 3*3600 for a,b in zip(stamps,stamps[1:])):
            continue
        if heights[1] < heights[0] and heights[1] <= heights[2]:
            lows.append(dict(point,timing_source='curve estimate'))
    return lows
