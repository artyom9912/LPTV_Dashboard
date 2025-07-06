import os

def to_css_rgba(rgba_str):
    if rgba_str is None: return 'rgba(47, 47, 47, 1)'
    r, g, b, a = map(float, rgba_str.split(","))
    return f'rgba({int(r*255)}, {int(g*255)}, {int(b*255)}, {a})'

def get_user_picture(username):
    if os.path.isfile(f'assets/img/users/{username}.png'):
        return f'assets/img/users/{username}.png'
    else:
        return f'assets/img/users/user_nopic.png'


def rgba_string_to_hex(rgba_str):
    parts = [float(x.strip()) for x in rgba_str.split(',')]

    if len(parts) < 3:
        raise ValueError("Неправильный формат (R, G, B)")
    r, g, b = parts[:3]

    r = max(0, min(int(round(r * 255)), 255))
    g = max(0, min(int(round(g * 255)), 255))
    b = max(0, min(int(round(b * 255)), 255))

    return "#{:02x}{:02x}{:02x}".format(r, g, b)

def hex_to_rgba01(hex_color: str, alpha: float = 1.0):
    hex_color = hex_color.lstrip('#')
    if len(hex_color) != 6:
        raise ValueError("HEX color must be 6 characters long.")

    r = int(hex_color[0:2], 16) / 255.0
    g = int(hex_color[2:4], 16) / 255.0
    b = int(hex_color[4:6], 16) / 255.0

    return f'{round(r, 3)}, {round(g, 3)}, {round(b, 3)}, {round(alpha, 3)}'
