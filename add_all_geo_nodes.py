import bpy
import ast
import inspect
from bl_ui import node_add_menu_geometry, node_add_menu

with open(inspect.getsourcefile(node_add_menu), "r", encoding="utf-8") as f:
    source = f.read()

tree = ast.parse(source)
add_functions = {node.name for node in tree.body if isinstance(node, ast.FunctionDef) and "add" in node.name}

with open(inspect.getsourcefile(node_add_menu_geometry), "r", encoding="utf-8") as f:
    source = f.read()

all_bpy_types = set(dir(bpy.types))
tree = ast.parse(source)
categories = {}
bl_classes = {node for node in tree.body if isinstance(node, ast.ClassDef)}

for bl_class in bl_classes:
    category = None
    for stmt in bl_class.body:
        if category is not None:
            break
        if isinstance(stmt, ast.Assign):
            for target in stmt.targets:
                if isinstance(target, ast.Name) and target.id == "bl_label":
                    try:
                        category = f"{ast.literal_eval(stmt.value).upper()} - {bl_class.name.lower()}"
                        categories[category] = set()
                        break
                    except:
                        continue
    if not category:
        continue
    for stmt in bl_class.body:
        if isinstance(stmt, ast.FunctionDef) and stmt.name == "draw":
            for sub in ast.walk(stmt):
                if isinstance(sub, ast.Call):
                    for arg in sub.args:
                        try:
                            node_id = ast.literal_eval(arg)
                            if node_id in all_bpy_types:
                                categories[category].add(node_id)
                        except:
                            pass

tree = None
for area in bpy.context.screen.areas:
    if area.type == 'NODE_EDITOR':
        for space in area.spaces:
            if space.type == 'NODE_EDITOR' and hasattr(space, 'node_tree'):
                if space.node_tree:
                    tree = space.node_tree
                    break

cat_nodes = {}
if tree and categories:
    tree.nodes.clear()
    for category, identifiers in categories.items():
        nodes = []
        for identifier in identifiers:
            try:
                node = tree.nodes.new(identifier)
                if node:
                    node.location.x = 1000
                    node.location.y = 1000
                    nodes.append(node)
            except:
                continue
        if nodes:
            cat_nodes[category] = nodes

frame_nodes = []
if cat_nodes:
    for category, nodes in cat_nodes.items():
        frame = tree.nodes.new("NodeFrame")
        frame.label = category
        frame.shrink = False
        frame.width = 1000
        frame.height = 1000
        for node in nodes:
            node.parent = frame
        frame.shrink = True
        frame_nodes.append((frame, nodes))

y = 0
for frame, nodes in frame_nodes:
    frame.location.x = 0
    frame.location.y = y
    y -= frame.dimensions.y + 40
    x = frame.location.x - (frame.dimensions.x / 2)
    for node in nodes:
        node.location.x = x
        x += node.dimensions.x + 20
