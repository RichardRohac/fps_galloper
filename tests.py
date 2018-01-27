import unittest
from GallopTracker import GallopTracker

class GallopTrackerTestCase(unittest.TestCase):
    def setUp(self):
        self.gallop_tracker = GallopTracker()

    def tearDown(self):
        self.gallop_tracker = None

    def test_not_galloping_when_empty(self):
        self.assertEqual(self.gallop_tracker.isGalloping(), False,
                         'should return false when empty')

    def test_not_galloping_when_one(self):
        self.gallop_tracker.addNoha(320, 320)
        self.assertEqual(self.gallop_tracker.isGalloping(), False,
                         'should return false when one')
    def test_galloping(self):
        self.gallop_tracker.addNoha(320, 340)
        self.gallop_tracker.addNoha(320, 300)
        self.gallop_tracker.addNoha(320, 340)
        self.gallop_tracker.addNoha(320, 300)
        self.gallop_tracker.addNoha(320, 340)
        self.assertEqual(self.gallop_tracker.isGalloping(), True,'should  Gallop')

    def test_galloping_under_thresh(self):
        self.gallop_tracker.addNoha(320, 325)
        self.gallop_tracker.addNoha(320, 315)
        self.gallop_tracker.addNoha(320, 325)
        self.gallop_tracker.addNoha(320, 315)
        self.gallop_tracker.addNoha(320, 325)
        self.assertEqual(self.gallop_tracker.isGalloping(), False, 'should  not Gallop')

    def test_ring_buffer(self):
        self.gallop_tracker.addNoha(320, 340)
        self.gallop_tracker.addNoha(320, 300)
        self.gallop_tracker.addNoha(320, 340)
        self.gallop_tracker.addNoha(320, 300)
        self.gallop_tracker.addNoha(320, 340)
        for i in range(100):
            self.gallop_tracker.addNoha(320, 340)
        self.assertEqual(self.gallop_tracker.isGalloping(), False, 'should  not Gallop')



    def test_galloping_lot_of_data(self):
        # Same
        self.gallop_tracker.addNoha(320, 340)
        self.gallop_tracker.addNoha(320, 340)
        self.gallop_tracker.addNoha(320, 340)
        self.gallop_tracker.addNoha(320, 340)
        self.gallop_tracker.addNoha(320, 340)



        #Switchy
        self.gallop_tracker.addNoha(320, 340)
        self.gallop_tracker.addNoha(320, 300)
        self.gallop_tracker.addNoha(320, 340)
        self.gallop_tracker.addNoha(320, 300)
        self.gallop_tracker.addNoha(320, 340)

        # Same
        self.gallop_tracker.addNoha(320, 340)
        self.gallop_tracker.addNoha(320, 340)
        self.gallop_tracker.addNoha(320, 340)
        self.gallop_tracker.addNoha(320, 340)
        self.gallop_tracker.addNoha(320, 340)        
        self.assertEqual(self.gallop_tracker.isGalloping(), True, 'should Gallop') 

suite = unittest.TestLoader().loadTestsFromTestCase(GallopTrackerTestCase)

unittest.TextTestRunner(verbosity=2).run(suite)