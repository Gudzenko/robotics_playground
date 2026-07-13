def _c(color):
    r, g, b = color
    return f'{r} {g} {b} 1'


def solid_link(name, pose, size, color):
    cx, cy, cz = pose
    sx, sy, sz = size
    c = _c(color)
    return (
        f'    <link name="{name}">\n'
        f'      <pose>{cx} {cy} {cz} 0 0 0</pose>\n'
        f'      <collision name="col"><geometry><box>'
        f'<size>{sx} {sy} {sz}</size></box></geometry></collision>\n'
        f'      <visual name="vis">\n'
        f'        <geometry><box><size>{sx} {sy} {sz}</size></box></geometry>\n'
        f'        <material><ambient>{c}</ambient><diffuse>{c}</diffuse></material>\n'
        f'      </visual>\n'
        f'    </link>'
    )


def visual_link(name, pose, size, color):
    cx, cy, cz = pose
    sx, sy, sz = size
    c = _c(color)
    return (
        f'    <link name="{name}">\n'
        f'      <pose>{cx} {cy} {cz} 0 0 0</pose>\n'
        f'      <visual name="vis">\n'
        f'        <geometry><box><size>{sx} {sy} {sz}</size></box></geometry>\n'
        f'        <material><ambient>{c}</ambient><diffuse>{c}</diffuse></material>\n'
        f'      </visual>\n'
        f'    </link>'
    )


def model_file(model_name, links):
    body = '\n'.join(links)
    return (
        '<?xml version="1.0"?>\n'
        '<sdf version="1.8">\n'
        f'  <model name="{model_name}">\n'
        '    <static>true</static>\n'
        '    <pose>0 0 0 0 0 0</pose>\n'
        f'{body}\n'
        '  </model>\n'
        '</sdf>\n'
    )
