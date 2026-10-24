import unittest
from datetime import datetime
from tide_curve import estimated_curve, with_fallback_curve, timer_lows

def event(hour, height, kind):
    return dict(time=f'2026-10-24T{hour:02}:00:00+00:00',height=height,type=kind)

class CurveTests(unittest.TestCase):
    def test_interpolated_curve_keeps_exact_provider_countdown_time(self):
        result=with_fallback_curve(dict(curve=[],events=[event(0,4,'H'),event(6,0,'L'),event(12,4,'H')]))
        self.assertEqual(result['timer_lows'][0]['time'],event(6,0,'L')['time'])
        self.assertEqual(result['timer_lows'][0]['timing_source'],'provider')

    def test_curve_only_data_has_an_estimated_timer(self):
        points=[dict(time=event(h,0,'L')['time'],height=value) for h,value in [(0,3),(1,1),(2,2)]]
        lows=timer_lows(dict(curve=points))
        self.assertEqual(len(lows),1)
        self.assertEqual(lows[0]['time'],event(1,0,'L')['time'])
        self.assertEqual(lows[0]['timing_source'],'curve estimate')

    def test_countdown_does_not_invent_minima_at_endpoints_or_gaps(self):
        for points in [
            [dict(time=event(0,0,'L')['time'],height=0),dict(time=event(1,0,'L')['time'],height=1)],
            [dict(time=event(h,0,'L')['time'],height=v) for h,v in [(0,2),(6,0),(12,2)]],
            [dict(time=event(h,0,'L')['time'],height=v) for h,v in [(0,None),(1,0),(2,2)]]
        ]:
            self.assertEqual(timer_lows(dict(curve=points)),[])

    def test_exact_extrema_bounded_monotonic_shape(self):
        points=estimated_curve([event(0,-1,'L'),event(6,5,'H'),event(12,0,'L')])
        by_time={p['time']:p['height'] for p in points}
        self.assertEqual(by_time[event(0,-1,'L')['time']],-1)
        self.assertEqual(by_time[event(6,5,'H')['time']],5)
        self.assertEqual(by_time[event(12,0,'L')['time']],0)
        self.assertAlmostEqual(by_time[event(3,0,'L')['time']],2)
        self.assertTrue(all(-1<=p['height']<=5 for p in points))
        heights=[p['height'] for p in points[:37]]
        self.assertEqual(heights,sorted(heights))

    def test_adjacent_day_events_cover_midnight_without_extrapolation(self):
        previous=dict(time='2026-10-23T22:00:00+00:00',height=4,type='H')
        points=estimated_curve([previous,event(4,-1,'L')])
        self.assertTrue(any(p['time']==event(0,0,'L')['time'] for p in points))
        self.assertEqual(points[0]['time'],previous['time'])
        self.assertEqual(points[-1]['time'],event(4,-1,'L')['time'])

    def test_insufficient_and_contradictory_events(self):
        for events in [[],[event(0,0,'L')],[event(0,0,'L'),event(6,2,'L')],[event(0,5,'L'),event(6,1,'H')],[event(0,0,'L'),event(23,5,'H')]]:
            self.assertEqual(estimated_curve(events),[])

    def test_missing_cycle_creates_a_chart_break(self):
        points=estimated_curve([event(0,0,'L'),event(6,4,'H'),event(12,5,'H'),event(18,0,'L')])
        self.assertTrue(any(p['height'] is None for p in points))

    def test_provider_curve_is_preserved(self):
        curve=[dict(time=event(0,0,'L')['time'],height=1.234)]
        result=with_fallback_curve(dict(curve=curve,events=[event(0,0,'L'),event(6,4,'H')]))
        self.assertIs(result['curve'],curve)
        self.assertEqual(result['curve_kind'],'provider')

    def test_estimation_label_and_missing_provider(self):
        result=with_fallback_curve(dict(curve=[],events=[event(0,0,'L'),event(6,4,'H')]))
        self.assertEqual(result['curve_kind'],'interpolated')
        self.assertIn('not hourly provider predictions',result['chart_note'])
        unavailable=with_fallback_curve(dict(available=False,curve=[],events=[]))
        self.assertEqual(unavailable['curve_kind'],'none')

if __name__=='__main__':
    unittest.main()
