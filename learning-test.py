import unittest
from learning import Component

class TestComponent(unittest.TestCase):

    @unittest
    def test_compute(self):
        self.assertEqual(Component.nand2([1,0]), 1)
        self.assertEqual(Component.nor2([1,0]), 0)
        self.assertEqual(Component.xor2([1,0]), 1)
        self.assertEqual(Component.inverter([1]), 0)


if __name__ == '__main__':
    unittest.main()