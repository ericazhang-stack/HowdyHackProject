import unittest
from unittest.mock import patch
import conservation_sources as sources

class AdditionalSourcesTests(unittest.TestCase):
    def setUp(self):
        sources.CACHE.clear()

    def test_gbif_rejects_fuzzy_and_higher_taxon_matches(self):
        for match in [dict(matchType='FUZZY',rank='SPECIES'),dict(matchType='EXACT',rank='GENUS')]:
            with patch.object(sources,'request_json',return_value=match) as request:
                self.assertIsNone(sources.gbif_assessment('Test species'))
                self.assertEqual(request.call_count,1)

    def test_gbif_assessment_is_normalized_with_source(self):
        with patch.object(sources,'request_json',side_effect=[dict(matchType='EXACT',rank='SPECIES',usageKey=12),dict(category='VULNERABLE',code='VU')]):
            record=sources.gbif_assessment('Test species')
        self.assertEqual(record['code'],'VU')
        self.assertFalse(record['equivalent'])
        self.assertIn('/species/12',record['source_url'])

    def test_regional_rank_equivalents_are_not_used_as_iucn_categories(self):
        taxon=dict(conservation_status=dict(status='N2',iucn=40,authority='NatureServe',place=dict(name='Canada')))
        with patch.object(sources,'gbif_assessment',return_value=None):
            result=sources.resolve_status('Test species',taxon)
        self.assertEqual(result['code'],'UNASSESSED')
        self.assertEqual(result['assessments'],[])

    def test_no_assessment_differs_from_service_failure(self):
        with patch.object(sources,'gbif_assessment',return_value=None):
            result=sources.resolve_status('No match')
        self.assertEqual(result['code'],'UNASSESSED')
        with patch.object(sources,'gbif_assessment',side_effect=TimeoutError):
            result=sources.resolve_status('Unavailable')
        self.assertEqual(result['code'],'UNKNOWN')
        self.assertTrue(result['unavailable_sources'])

if __name__=='__main__':
    unittest.main()
