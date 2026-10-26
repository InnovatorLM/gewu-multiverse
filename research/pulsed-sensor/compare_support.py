"""Compare actual mixed recipes with repository-declared synthetic support."""
from decimal import Decimal
import json
from pathlib import Path


def compare(recipes, lower=Decimal('0.00001'), upper=Decimal('0.1')):
    return [{'mixture':mix,'concentration_M':[str(c) for c in values],
             'outside_repository_declared_synthetic_range':[ion for ion,c in zip(('NO3','Cl','HPO4'),values) if not lower<=c<=upper]}
            for mix,*values in recipes]


if __name__=='__main__':
    root=Path(__file__).resolve().parents[2]
    audit=json.loads((root/'docs/science-universe/proposals/pulsed-sensor-protocol-audit.json').read_text(),parse_float=Decimal)
    print(json.dumps(compare(audit['concentration_combinations']),indent=2))
