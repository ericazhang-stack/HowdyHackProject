import unittest
from conservation import status_for

class ConservationTests(unittest.TestCase):
    def test_missing_assessment_does_not_mean_least_concern_or_not_evaluated(self):
        self.assertEqual(status_for({})['code'],'UNKNOWN')

    def test_global_iucn_assessment_preferred_over_regional_rank(self):
        taxon=dict(id=1,conservation_statuses=[dict(status='N2',iucn=40,authority='NatureServe',place=dict(name='Canada')),dict(status='LC',authority='IUCN Red List',place_id=None)])
        result=status_for(taxon)
        self.assertEqual(result['code'],'LC')
        self.assertEqual(result['scope'],'Global assessment')
        self.assertFalse(result['equivalent'])

    def test_regional_equivalent_keeps_scope_and_original_rank(self):
        result=status_for(dict(id=2,conservation_status=dict(status='N2',iucn=40,authority='NatureServe',place=dict(name='Canada'))))
        self.assertEqual(result['code'],'EN')
        self.assertTrue(result['equivalent'])
        self.assertEqual(result['reported_status'],'N2')
        self.assertEqual(result['scope'],'Canada')

    def test_data_deficient_remains_distinct_from_missing(self):
        result=status_for(dict(conservation_status=dict(status='DD',authority='IUCN')))
        self.assertEqual(result['code'],'DD')

    def test_unsafe_source_urls_are_not_exposed(self):
        result=status_for(dict(id=123,conservation_status=dict(status='EN',url='javascript:alert(1)')))
        self.assertEqual(result['source_url'],'https://www.inaturalist.org/taxa/123')

if __name__=='__main__':
    unittest.main()
