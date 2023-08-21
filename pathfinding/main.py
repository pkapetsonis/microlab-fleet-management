import matplotlib.pyplot as plt
import shapely.plotting as spt
from shapely import Point, Polygon, STRtree, LineString
from dataclasses import dataclass
from typing import Optional

from read_wkt_csv import read_wkt_csv


start = Point(0, -100)
target = Point(0, 200)

MAP_FILE = 'map.csv'

BUFF_DISTANCE = 10
POINTGEN_DISTANCE = 12 # load object file


def load_geometry(filepath):
    objects = read_wkt_csv(filepath)
    colide_objects = [o.buffer(BUFF_DISTANCE, join_style=2) for o in objects]
    point_objects  = [o.buffer(POINTGEN_DISTANCE, join_style=2) for o in objects]
    tree = STRtree(colide_objects)

    return objects, colide_objects, point_objects, tree


objects, colide_objects, point_objects, tree = load_geometry(MAP_FILE)

@dataclass
class AStarPoint:
    real_point: Point
    g_score: float
    f_score: float
    parent: Optional[Point]


def pathfind(start, target, tree, point_objects, plot=False):
    POINT_DATA = {}
    open_set = {start}
    heur = lambda p: target.distance(p)

    current = start
    POINT_DATA[start] = AStarPoint(start, heur(start), 0, None)

    while open_set:
        # SEM.acquire()
        current = min(open_set, key=lambda n: POINT_DATA[n].f_score)
        current_real = POINT_DATA[current].real_point
        direct_line = LineString((current_real, target))

        if plot:
            spt.plot_points(current_real, color='yellow')

        intersect_geoms = tree.query(direct_line, predicate='intersects')
        pointgen_geoms = tree.query(direct_line)

        # path found
        if len(intersect_geoms) == 0:
            # recreate path
            path = []
            while current is not None:
                pd = POINT_DATA[current]
                path.append(pd.real_point)
                current = pd.parent

            path.reverse()
            path.append(target)

            return LineString(path)

        open_set.remove(current)
        # generate neighbour points
        # for geom_idx in intersect_geoms:
        for geom_idx in pointgen_geoms:
            geom: Polygon = tree.geometries[geom_idx]
            buffed_geom  = point_objects[geom_idx]
            # get the intersection line with geometry
            # itsct = direct_line.intersection(geom)
            # print(geom)

            for point in buffed_geom.exterior.coords:
                # compute the new point based on the direction of intersection
                pp = Point(point)
                new_point = pp
                # print(new_point)
                """
                sline = shapely.shortest_line(itsct, pp)
                vec = np.array(sline.coords[1]) - np.array(sline.coords[0])
                vec_norm = vec / np.linalg.norm(vec)
                new_point = Point(np.array(point) + offset*vec_norm)
                """

                # check if point is reachable
                point_line = LineString((current_real, new_point))
                if len(tree.query(point_line, predicate='intersects')) > 0:
                    # reject point
                    # spt.plot_points(new_point, color='red')
                    continue

                # spt.plot_points(new_point, color='green')

                t_score = POINT_DATA[current].g_score + current.distance(new_point)
                if pp not in POINT_DATA:
                    POINT_DATA[pp] = AStarPoint(new_point, t_score, t_score + heur(new_point), current)
                    open_set.add(pp)
                elif t_score < POINT_DATA[pp].g_score:
                    POINT_DATA[pp].real_point = new_point
                    POINT_DATA[pp].g_score = t_score
                    POINT_DATA[pp].f_score = t_score + heur(new_point)
                    POINT_DATA[pp].parent = current
                    open_set.add(pp)

    # if not path found, return False
    return None


def run():
    path = pathfind(start, target, tree, point_objects, plot=True)
    if path:
        spt.plot_line(path, color='black')
        plt.gcf().canvas.draw()

def render_field():
    plt.cla()
    # for o in buffed_objects:
    #     spt.plot_polygon(o, color='grey')

    for o in objects:
        spt.plot_polygon(o)

    spt.plot_points(start, color='green')
    spt.plot_points(target, color='pink')
    plt.gcf().canvas.draw()

def key_handler(event):
    global start, target, objects, tree, point_objects, colide_objects

    if event.key == 'b':
        start = Point(event.xdata, event.ydata)
    elif event.key == 't':
        target = Point(event.xdata, event.ydata)
    elif event.key == 'r':
        objects, colide_objects, point_objects, tree = load_geometry(MAP_FILE)

    render_field()
    run()



def headless_run():
    objects, colide_objects, point_objects, tree = load_geometry(MAP_FILE)
    path = pathfind(start, target, tree, point_objects)
    print(path)


cid = plt.gcf().canvas.mpl_connect('key_press_event', key_handler)
plt.xlim(-400, 400)
plt.ylim(-400, 400)

render_field()


plt.show()

