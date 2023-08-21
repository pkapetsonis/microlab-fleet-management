import shapely
import csv
from typing import List

def read_wkt_csv(path) -> List[shapely.Geometry]:
    with open(path) as f:
        reader = csv.reader(f)
        header = next(reader)
        data_col_idx = header.index('WKT')

        geometry = []
        for row in reader:
            geom = shapely.from_wkt(row[data_col_idx])
            if not geom.is_empty:
                geometry.append(geom)

        return geometry
