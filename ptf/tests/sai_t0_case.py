from t0_base_test import SaiT0HelperBase

class InitBasicData(SaiT0HelperBase):
    """
    This is a test class use to trigger some basic verification when set up the basic t0 data configuration.
    """
    #Todo remove this class when T0 data is ready, this class should not be checked into repo
    def setUp(self):
        """
        Test the basic setup proecss
        """
        #this process contains the switch_init process
        SaiT0HelperBase.setUp(self)

    def runTest(self):
        """
        Test the basic runTest proecss
        """
        pass

    def tearDown(self):
        """
        Test the basic tearDown proecss
        """
        pass
