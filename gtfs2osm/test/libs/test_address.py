try:
    import unittest
    from gtfs2osm.libs.address import extract_street_housenumber_better
except ImportError as err:
    print('Error {0} import module: {1}'.format(__name__, err))
    exit(128)


class TestAddressResolver(unittest.TestCase):
    def setUp(self):
        self.adresses = [
            {'original': 'Gránátos u. 11.', 'street': 'Gránátos utca', 'housenumber': '11', 'conscriptionnumber': None},
            {'original': 'BERCSÉNYI U.1 2934/5 HRSZ', 'street': 'Bercsényi utca', 'housenumber': '1',
             'conscriptionnumber': '2934/5'},
            {'original': 'Szérűskert utca 018910/23. hrsz. (Köles utca 1.)', 'street': 'Szérűskert utca',
             'housenumber': None,
             'conscriptionnumber': '018910/23'}]
        self.full_addresses = [
            {'original': '9737 Bük, Petőfi utca 63. Fszt. 1.', 'street': 'Petőfi utca', 'housenumber': '63',
             'conscriptionnumber': None}]


        def test_extract_street_housenumber_better(self):
            for i in self.adresses:
                original, street, housenumber, conscriptionnumber = i['original'], i['street'], i['housenumber'], i[
                    'conscriptionnumber']
                a, b, c = extract_street_housenumber_better(original)
                with self.subTest():
                    self.assertEqual(street, a)
                with self.subTest():
                    self.assertEqual(housenumber, b)
                with self.subTest():
                    self.assertEqual(conscriptionnumber, c)
