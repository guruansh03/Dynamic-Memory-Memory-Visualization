import unittest
from memory import MemoryManagementSimulator

class TestMemoryManagement(unittest.TestCase):
    def setUp(self):
        self.simulator = MemoryManagementSimulator(total_memory=4, page_size=1)

    def test_allocate_paging(self):
        self.simulator.allocate_paging("P1", 2)
        self.assertEqual(len(self.simulator.page_table["P1"]), 2)

    def test_page_fault(self):
        self.simulator.allocate_paging("P1", 4)
        self.simulator.handle_page_fault("P2")
        self.assertEqual(self.simulator.page_faults, 1)

if __name__ == "__main__":
    unittest.main()
