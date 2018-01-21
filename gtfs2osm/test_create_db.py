try:
    import unittest
    from gtfs2osm.test.libs.test_address import TestAddressResolver

except ImportError as err:
    print('Error {0} import module: {1}'.format(__name__, err))
    exit(128)


def testing_create_db():
    address_resolver = unittest.TestLoader().loadTestsFromTestCase(TestAddressResolver)
    suite = unittest.TestSuite(
        [address_resolver])
    return unittest.TextTestRunner(verbosity=2).run(suite)


if __name__ == '__main__':
    testing_create_db()
