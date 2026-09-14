# SPDX-License-Identifier: MIT
"""Native filled-island extension; zone outlines never substitute for copper.

Promoted from the preserved routing recovery. The primitive graph remains the
shared pad/track/via checker; each actual filled island has its own identity.
"""
from check_printed_bell_power_rework import (
    CopperGraph as PrimitiveGraph, bbox, boxes_touch, native_polygon, rectangle,
)


def require(value, message):
    if not value:
        raise ValueError(message)


def filled_islands(pcb, zone, layer):
    filled = zone.GetFilledPolysList(layer)
    require(filled is not None and not filled.IsEmpty(),
            "Zone has no actual filled polygons on " + pcb.LayerName(layer))
    polygons = filled.CloneDropTriangulation()
    for index in range(polygons.OutlineCount()):
        island = polygons.UnitSet(index)
        require(island.OutlineCount() == 1 and island.Area() > 0,
                "Invalid native filled island")
        yield index, island


class IslandItem:
    """Expose exactly one filled island, including holes, to the shared checker."""

    def __init__(self, zone, layer, index, polygon):
        self.zone, self.layer, self.index, self.polygon = zone, layer, index, polygon
        self.zone_uuid = zone.m_Uuid.AsString()

    def GetNetname(self):
        return self.zone.GetNetname()

    def IsOnLayer(self, layer):
        return layer == self.layer

    def GetEffectiveShape(self, layer):
        require(layer == self.layer, "Island queried on a different copper layer")
        return self.polygon

    def TransformShapeToPolygon(self, output, layer, clearance, error, error_location):
        require(layer == self.layer and clearance == 0,
                "Island adapter supports only exact filled copper on its own layer")
        output.Append(self.polygon)


class CopperGraph(PrimitiveGraph):
    def __init__(self, pcb, path):
        super().__init__(pcb, path)
        self.zone_islands = []
        zone_keys = []
        seen = set(self.items)
        for zone in self.board.Zones():
            zone_uuid = zone.m_Uuid.AsString()
            require(zone_uuid and zone_uuid not in seen, "Duplicate native zone identity")
            seen.add(zone_uuid)
            if zone.GetIsRuleArea():
                continue
            require(zone.GetNetname(), "Unassigned copper zone is unsupported")
            layers = list(zone.GetLayerSet().Seq())
            require(layers and all(layer in (pcb.F_Cu, pcb.B_Cu) for layer in layers),
                    "Unsupported filled-zone layer set")
            for layer in layers:
                for index, polygon in filled_islands(pcb, zone, layer):
                    uid = f"{zone_uuid}:{self.layer_name(layer)}:island:{index}"
                    require(uid not in self.items, "Duplicate synthetic filled-island identity")
                    item = IslandItem(zone, layer, index, polygon)
                    key = (uid, layer)
                    self.items[uid] = item
                    self.vertices[key] = {
                        "item": item, "shape": polygon, "bbox": bbox(polygon),
                        "net": zone.GetNetname(),
                    }
                    self.by_uuid[uid].append(key)
                    self.adj[key]
                    zone_keys.append(key)
                    self.zone_islands.append({
                        "uuid": uid, "zone_uuid": zone_uuid, "layer": self.layer_name(layer),
                        "island_index": index, "explicit_native_holes": polygon.HoleCount(0),
                        "boundary_representation": "Exact native filled boundary; linked-hole cuts are not normalized or counted as explicit holes",
                        "filled_area_mm2": polygon.Area() / pcb.FromMM(1) ** 2,
                    })
        done = set()
        for a in zone_keys:
            aa = self.vertices[a]
            for b, bb in self.vertices.items():
                if a == b or a[1] != b[1] or b in done:
                    continue
                if not boxes_touch(aa["bbox"], bb["bbox"]):
                    continue
                if not aa["shape"].Collide(bb["shape"], 0):
                    continue
                if aa["net"] != bb["net"]:
                    self.shorts.append({
                        "a_uuid": a[0], "b_uuid": b[0], "layer": self.layer_name(a[1]),
                        "nets": [aa["net"], bb["net"]],
                    })
                else:
                    self.join(a, b)
            done.add(a)
        self.components = {}
        for node in self.vertices:
            if node not in self.components:
                reached = self.reachable([node])
                identity = min(reached)
                self.components.update({key: identity for key in reached})

    def path(self, a, b, layer=None):
        result = super().path(a, b, layer)
        for step in result:
            item = self.items[step["uuid"]]
            if isinstance(item, IslandItem):
                step.update(zone_uuid=item.zone_uuid, filled_island_index=item.index)
        return result


def self_test(pcb):
    """Existing synthetic island/hole/short checks, with no candidate writes."""
    donut = rectangle(pcb, [0, 0, 10, 10])
    hole = rectangle(pcb, [3, 3, 7, 7])
    donut.BooleanSubtract(hole)
    other = rectangle(pcb, [20, 0, 25, 5])
    donut.Append(other)
    donut.Fracture()

    class TestZone:
        def GetFilledPolysList(self, layer):
            return donut

    islands = list(filled_islands(pcb, TestZone(), pcb.F_Cu))
    require(len(islands) == 2, "Disjoint filled polygons collapsed into one island")
    annulus = next(poly for _, poly in islands if bbox(poly)[0] == 0)
    separate = next(poly for _, poly in islands if bbox(poly)[0] == pcb.FromMM(20))
    in_hole = rectangle(pcb, [4, 4, 6, 6])
    in_copper = rectangle(pcb, [1, 1, 2, 2])
    require(not annulus.Collide(in_hole, 0), "Polygon collision incorrectly fills a hole")
    require(annulus.Collide(in_copper, 0), "Filled copper containment contact omitted")
    require(not annulus.Collide(separate, 0), "Disjoint same-zone islands falsely touch")
    overlap = annulus.CloneDropTriangulation()
    overlap.BooleanIntersection(in_hole)
    require(overlap.IsEmpty(), "Terminal-cut intersection incorrectly fills a hole")
    zone = TestZone()
    zone.GetNetname = lambda: "GND"
    zone.m_Uuid = type("TestUuid", (), {"AsString": lambda self: "test-zone"})()
    adapter = IslandItem(zone, pcb.F_Cu, 0, annulus)
    poly = native_polygon(pcb, adapter, pcb.F_Cu)
    require(not poly.Collide(in_hole, 0) and poly.Collide(in_copper, 0),
            "Legacy native_polygon adapter lost the filled-island hole")

    class EmptyZone:
        def GetFilledPolysList(self, layer):
            return pcb.SHAPE_POLY_SET()

    try:
        list(filled_islands(pcb, EmptyZone(), pcb.F_Cu))
    except ValueError:
        pass
    else:
        raise ValueError("Unfilled zone accepted as connected copper")
    board = pcb.BOARD()
    net = pcb.NETINFO_ITEM(board, "GND")
    board.Add(net)
    zone = pcb.ZONE(board)
    zone.SetLayer(pcb.F_Cu)
    zone.SetNetCode(net.GetNetCode())
    zone.SetFilledPolysList(pcb.F_Cu, donut)
    zone.SetIsFilled(True)
    board.Add(zone)
    layers = pcb.LSET()
    layers.AddLayer(pcb.F_Cu)

    def pad_at(ref, x, y, pad_net):
        fp = pcb.FOOTPRINT(board)
        fp.SetReference(ref)
        board.Add(fp)
        pad = pcb.PAD(fp)
        pad.SetNumber("1")
        pad.SetAttribute(pcb.PAD_ATTRIB_SMD)
        pad.SetShape(pcb.PAD_SHAPE_RECT)
        pad.SetSize(pcb.VECTOR2I(pcb.FromMM(.5), pcb.FromMM(.5)))
        pad.SetPosition(pcb.VECTOR2I(pcb.FromMM(x), pcb.FromMM(y)))
        pad.SetLayerSet(layers)
        pad.SetNetCode(pad_net.GetNetCode())
        fp.Add(pad)

    for ref, x, y in (("A", 1, 1), ("B", 21, 1), ("H", 5, 5), ("C", 2, 1)):
        pad_at(ref, x, y, net)

    class MemoryApi:
        def __getattr__(self, name):
            return getattr(pcb, name)

        def LoadBoard(self, path):
            return board

    graph = CopperGraph(MemoryApi(), "<synthetic-memory-board>")
    a, b, h, c = [graph.pad_uuid(ref, "1") for ref in ("A", "B", "H", "C")]
    require(len(graph.zone_islands) == 2 and len(graph.nets()[0]["islands"]) == 3
            and not graph.connected(a, b) and not graph.connected(a, h) and graph.connected(a, c),
            "Native graph falsely joined disjoint islands/holes or missed actual zone contacts")
    require(any(step.get("zone_uuid") for step in graph.path(a, c)),
            "Graph path hides the native zone-island witness")
    foreign = pcb.NETINFO_ITEM(board, "/CELL_NEG")
    board.Add(foreign)
    pad_at("FOREIGN", 2, 2, foreign)
    short_graph = CopperGraph(MemoryApi(), "<synthetic-memory-board>")
    require(any("/CELL_NEG" in record["nets"] and "island:" in record["a_uuid"]
                for record in short_graph.shorts), "Zone-to-foreign-net short was omitted")
    return {"disjoint_islands": 2, "preserved_holes": 1, "unfilled_zone_rejected": True,
            "actual_graph_pad_islands": 3, "zone_path_witness_checked": True,
            "CELL_NEG_zone_short_detected": True, "candidate_loaded_or_written": False}
