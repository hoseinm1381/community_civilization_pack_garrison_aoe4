"""Deterministic 0.7.0 Vietnamese architecture blockouts.

Only local design geometry is declared here. A separate Blender runner owns
collection cleanup, material creation, meshing, inspection, and export.
Coordinates are local to each asset: +Y is rear, the front entrance is -Y,
and Z=0 is grade. Each function builds one asset in its own collection.

Required helper mapping:
    box(name, loc, size, material)
    hip_roof(name, center_xy, width, depth, eave_z, rise, material, upturn=0.3)
    hall(name, xy, width, depth, plinth_z, body_h, roof_h, material)
    basin(name, xy, width, depth, z)
    post(name, loc, height, radius)
    collection(name, offset)

The runner may exec this file into a namespace containing those helpers, then
call build_garden(), etc., or pass an explicit mapping to each function.
"""

RECIPE_VERSION = "ccp-release-070-blockout/v1"


def _helpers(helpers):
    source = globals() if helpers is None else helpers
    required = ("box", "hip_roof", "hall", "basin", "post", "collection")
    missing = [name for name in required if not callable(source.get(name))]
    if missing:
        raise ValueError("Missing blockout helpers: " + ", ".join(missing))
    return [source[name] for name in required]


def build_garden(helpers=None):
    """Royal lotus court, waterside pavilion, and rear elephant service yard."""
    box, hip_roof, hall, basin, post, collection = _helpers(helpers)
    collection("CCP070_Imperial_Garden_Blockout", (0, 0, 0))

    # The pond is a real recess made by the runner. Its near edge is y=-5.8.
    basin("Garden_Lotus_Pond_Recess", (-3.0, -2.8), 10.0, 6.0, 0.0)
    box("Garden_Pond_Bridge", (-3.0, -2.275, 0.275), (1.75, 9.45, 0.55), "wood")
    box("Garden_Front_Path", (-3.0, -9.0, 0.06), (1.9, 4.0, 0.12), "stone")

    # The 7:4.2 pavilion sits at the bridge's north contact edge (y=2.7).
    hall("Garden_Waterside_Pavilion", (-3.0, 4.8), 7.0, 4.2,
         0.55, 2.65, 1.25, "plaster")
    for x in (-5.75, -3.0, -0.25):
        post("Garden_Pavilion_Front_Post_%s" % str(x).replace("-", "m").replace(".", "p"),
             (x, 2.85, 0.55), 2.65, 0.16)
    # A secondary hip above the entry makes the ceremonial roof read from afar.
    box("Garden_Pavilion_Raised_Drum", (-3.0, 4.8, 4.45),
        (3.5, 1.7, 0.45), "wood")
    hip_roof("Garden_Pavilion_Raised_Roof", (-3.0, 4.8), 4.3, 2.5,
             4.67, 0.8, "roof", upturn=0.38)
    hall("Garden_Rear_Covered_Gallery", (-3.0, 8.5), 7.0, 1.6,
         0.15, 1.9, 0.55, "wood")

    # Garden enclosure is interrupted by the south entrance and east yard exit.
    box("Garden_Wall_West", (-11.0, 0.0, 0.75), (0.5, 22.0, 1.5), "stone")
    box("Garden_Wall_North", (0.0, 11.0, 0.75), (22.0, 0.5, 1.5), "stone")
    box("Garden_Wall_South_West", (-7.0, -11.0, 0.75), (8.0, 0.5, 1.5), "stone")
    box("Garden_Wall_South_East", (5.0, -11.0, 0.75), (12.0, 0.5, 1.5), "stone")
    box("Garden_Wall_East_Lower", (11.0, -3.5, 0.75), (0.5, 15.0, 1.5), "stone")
    box("Garden_Wall_East_Upper", (11.0, 10.5, 0.75), (0.5, 1.0, 1.5), "stone")

    # Interpretive animal-service court: open and unoccupied, wide east exit.
    box("Garden_Service_Yard_South", (6.5, 2.6, 0.55), (8.5, 0.42, 1.1), "stone")
    box("Garden_Service_Yard_West", (2.5, 6.8, 0.55), (0.42, 8.4, 1.1), "stone")
    box("Garden_Service_Stable_Body", (7.6, 8.5, 1.35), (5.0, 3.0, 2.7), "wood")
    hip_roof("Garden_Service_Stable_Roof", (7.6, 8.5), 5.7, 3.7,
             2.72, 0.85, "roof", upturn=0.2)
    box("Garden_Yard_Exit_Threshold", (10.5, 7.2, 0.08),
        (1.4, 3.8, 0.16), "stone")


def build_foundry(helpers=None):
    """Asymmetric royal cannon works organized around a clear casting court."""
    box, hip_roof, hall, basin, post, collection = _helpers(helpers)
    collection("CCP070_Trung_Foundaries_Blockout", (0, 0, 0))

    box("Foundry_Work_Court", (1.7, -2.5, 0.1), (16.2, 14.2, 0.2), "stone")
    hall("Foundry_High_Forge_Hall", (-4.7, 5.1), 10.0, 5.7,
         0.35, 3.35, 1.35, "plaster")
    hall("Foundry_Low_Store_Hall", (7.1, 4.8), 5.0, 6.0,
         0.25, 2.45, 0.9, "wood")
    # Roofed weighing shed stays open toward the south court.
    for x in (-8.2, -4.9, -1.6):
        post("Foundry_Shed_Post_%s" % str(x).replace("-", "m").replace(".", "p"),
             (x, -1.0, 0.2), 2.4, 0.16)
    hip_roof("Foundry_Open_Weighing_Shed_Roof", (-4.9, -0.1),
             9.1, 3.4, 2.65, 0.7, "roof", upturn=0.18)

    # Two low masonry furnace volumes flank a free central casting lane.
    for side, x in (("West", -6.4), ("East", -0.8)):
        box("Foundry_%s_Furnace_Base" % side, (x, -5.2, 0.65),
            (3.0, 3.2, 1.3), "stone")
        box("Foundry_%s_Furnace_Hearth" % side, (x, -5.2, 1.5),
            (2.2, 2.35, 0.45), "clay")
        box("Foundry_%s_Low_Chimney" % side, (x - 0.8, -4.35, 2.4),
            (0.9, 0.9, 3.5), "stone")
    box("Foundry_Casting_Bed", (4.6, -5.2, 0.32),
        (5.6, 2.7, 0.44), "clay")
    box("Foundry_Mould_Store", (8.25, -4.7, 0.68),
        (2.3, 3.3, 1.35), "wood")
    box("Foundry_Back_Store_Court", (7.0, 9.1, 0.08),
        (5.5, 2.3, 0.16), "stone")
    # Only short boundary lengths: the work court remains visually open.
    box("Foundry_West_Screen", (-10.0, 5.8, 0.7),
        (0.35, 10.0, 1.4), "stone")
    box("Foundry_North_Screen", (-5.0, 10.6, 0.7),
        (10.4, 0.35, 1.4), "stone")


def build_wonder(helpers=None):
    """Kinh Thien-inspired axial palace, with three ten-step stair aisles."""
    box, hip_roof, hall, basin, post, collection = _helpers(helpers)
    collection("CCP070_Kinh_Thien_Wonder_Blockout", (0, 0, 0))

    # Podium plan ratio 21:15.3 ~= documented 57:41.5. Its top is z=1.2.
    box("Wonder_Kinh_Thien_Podium", (0.0, 0.0, 0.6),
        (21.0, 15.3, 1.2), "stone")
    # Ten level surfaces in each aisle. The northmost step touches the podium.
    for aisle, x in (("West", -5.4), ("Center", 0.0), ("East", 5.4)):
        for index in range(10):
            level = 0.12 * (index + 1)
            box("Wonder_%s_Stair_%02d" % (aisle, index + 1),
                (x, -10.5 + 0.3 * index, level / 2),
                (3.0, 0.3, level), "stone")
    box("Wonder_Front_Gate_Path", (0.0, -7.25, 1.28),
        (5.0, 0.8, 0.16), "stone")
    hall("Wonder_Main_Audience_Hall", (0.0, 2.2), 12.5, 6.8,
         1.2, 3.7, 1.45, "wood")
    # Raised second roof over a narrower upper chamber: two roof tiers,
    # each with four curved slopes supplied by the runner's hip_roof helper.
    box("Wonder_Upper_Chamber", (0.0, 2.2, 6.15),
        (9.3, 4.4, 1.45), "plaster")
    hip_roof("Wonder_Upper_Four_Hip_Roof", (0.0, 2.2), 10.6, 5.6,
             6.87, 1.32, "roof", upturn=0.42)
    for side, x in (("West", -8.2), ("East", 8.2)):
        hall("Wonder_%s_Flanking_Gallery" % side, (x, 2.0),
             3.1, 7.0, 1.2, 2.6, 0.9, "plaster")
    hall("Wonder_South_Ceremonial_Gate", (0.0, -5.55),
         5.0, 1.6, 1.2, 2.5, 0.75, "wood")


def build_university_additions(helpers=None):
    """Conservative forecourt added around the separately imported exact stock mesh.

    The runner must place stock chi_university_control_age04 at local origin first.
    Its decoded body extent is about 14.09 x 12.41 x 8.38, centered here for
    planning only; verify actual Blender origin and bounds before joining.
    """
    box, hip_roof, hall, basin, post, collection = _helpers(helpers)
    collection("CCP070_University_Additions_Blockout", (0, 0, 0))
    # Fit additions inside the actual L-shaped stock building's empty quadrant.
    # No extension of its measured XY envelope is needed for this proposal.
    # Verified by downward BVH rays: clear stock quadrant is X>0, Y<0.
    box("University_Forecourt", (3.0, -3.6, 0.08),
        (5.5, 4.4, 0.16), "stone")
    for side, x in (("West", 0.8), ("East", 5.2)):
        post("University_%s_Gate_Post" % side, (x, -5.3, 0.16), 2.55, 0.2)
    box("University_Gate_Lintel", (3.0, -5.3, 2.62),
        (5.1, 0.45, 0.32), "wood")
    hip_roof("University_Entrance_Gate_Roof", (3.0, -5.3),
             5.7, 1.8, 2.8, 0.7, "roof", upturn=0.25)
    # Four stele-scale masses are placeholders for later reviewed detail.
    for side, x in (("West", 1.1), ("East", 4.9)):
        for row, y in (("Front", -3.1), ("Rear", -1.85)):
            box("University_%s_%s_Stele_Base" % (side, row),
                (x, y, 0.27), (0.95, 0.68, 0.38), "stone")
            box("University_%s_%s_Stele_Mass" % (side, row),
                (x, y, 1.12), (0.46, 0.25, 1.38), "stone")


def build(helpers=None):
    """Build all four for inspection; prefer one build_* function at a time."""
    build_garden(helpers)
    build_foundry(helpers)
    build_wonder(helpers)
    build_university_additions(helpers)
