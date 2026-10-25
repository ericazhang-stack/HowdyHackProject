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

    def test_natureserve_preserves_its_own_ranking_system(self):
        with patch.object(sources,'request_json',return_value=dict(results=[dict(scientificName='Test species',roundedGRank='G2',uniqueId='ELEMENT_GLOBAL.2.1')])):
            record=sources.natureserve_assessment('Test species')
        self.assertEqual(record['code'],'NS_G2')
        self.assertEqual(record['label'],'Imperiled · G2')
        self.assertFalse(record['equivalent'])

    def test_ranked_natureserve_preferred_over_gbif_not_evaluated(self):
        gbif=dict(code='NE',label='Not evaluated',source='IUCN category via GBIF',scope='Global assessment')
        nature=dict(code='NS_G4',label='Apparently secure',source='NatureServe Explorer',scope='Global NatureServe rank')
        with patch.object(sources,'gbif_assessment',return_value=gbif),patch.object(sources,'natureserve_assessment',return_value=nature):
            result=sources.resolve_status('Test species')
        self.assertEqual(result['code'],'NS_G4')
        self.assertEqual(len(result['assessments']),2)

    def test_no_assessment_differs_from_service_failure(self):
        with patch.object(sources,'gbif_assessment',return_value=None),patch.object(sources,'natureserve_assessment',return_value=None):
            result=sources.resolve_status('No match')
        self.assertEqual(result['code'],'UNASSESSED')
        with patch.object(sources,'gbif_assessment',side_effect=TimeoutError),patch.object(sources,'natureserve_assessment',return_value=None):
            result=sources.resolve_status('Unavailable')
        self.assertEqual(result['code'],'UNKNOWN')
        self.assertTrue(result['unavailable_sources'])

if __name__=='__main__':
    unittest.main()
