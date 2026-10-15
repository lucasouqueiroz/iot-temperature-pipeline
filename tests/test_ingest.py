import sys
import unittest
from pathlib import Path
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from ingest import normalize_columns

class TransformTests(unittest.TestCase):
    def sample(self):
        return pd.DataFrame({'id': ['r1'], 'room_id/id': ['Room Admin'], 'noted_date': ['08-12-2018 09:30'], 'temp': [29], 'out/in': ['In']})

    def test_normalization(self):
        result = normalize_columns(self.sample())
        self.assertEqual(result.iloc[0]['device_id'], 'Room Admin / In')
        self.assertEqual(result.iloc[0]['reading_at'], pd.Timestamp('2018-12-08 09:30'))

    def test_exact_duplicates(self):
        self.assertEqual(len(normalize_columns(pd.concat([self.sample()] * 2))), 1)

    def test_conflicting_id(self):
        other = self.sample()
        other['temp'] = 30
        with self.assertRaises(ValueError):
            normalize_columns(pd.concat([self.sample(), other]))

    def test_invalid_direction(self):
        frame = self.sample()
        frame['out/in'] = 'unknown'
        with self.assertRaises(ValueError):
            normalize_columns(frame)

    def test_missing_column(self):
        with self.assertRaises(ValueError):
            normalize_columns(self.sample().drop(columns='temp'))

if __name__ == '__main__':
    unittest.main()
