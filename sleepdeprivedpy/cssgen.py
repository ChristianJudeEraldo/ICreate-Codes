def generate_css():
    css = []

    # Flexbox classes
    css.append(".flex-x {\n  display: flex;\n  flex-direction: row;\n}\n")
    css.append(".flex-y {\n  display: flex;\n  flex-direction: column;\n}\n")

    # Justify-content classes
    for pos in ["start", "center", "end", "space-between", "space-around", "space-evenly"]:
        css.append(f".jy-{pos} {{\n  justify-content: {pos};\n}}\n")

    # Align-items classes
    for pos in ["start", "center", "end"]:
        css.append(f".an-{pos} {{\n  align-items: {pos};\n}}\n")

    # Center class
    css.append(
        ".center {\n  display: flex;\n  align-items: center;\n  justify-content: center;\n  text-align: center;\n}\n"
    )

    # Push classes
    push_positions = {
        "top": "margin-bottom: auto;",
        "bottom": "margin-top: auto;",
        "left": "margin-right: auto;",
        "right": "margin-left: auto;",
        "center": "margin: auto;",
        "ne": "margin-bottom: auto; margin-left: auto;",
        "nw": "margin-bottom: auto; margin-right: auto;",
        "se": "margin-top: auto; margin-left: auto;",
        "sw": "margin-top: auto; margin-right: auto;",
    }
    for pos, rules in push_positions.items():
        css.append(f".push-{pos} {{\n  {rules}\n}}\n")

    # Margins and paddings
    spacing_values = ["0.25", "0.5", "1", "2", "4", "8", "10"]  # in rem
    for prefix in ["m", "p"]:  # Margin and padding
        for value in spacing_values:
            rem_value = value + "rem"
            prop = 'margin' if prefix == 'm' else 'padding'
            css.append(f".{prefix}-{value.replace('.', '')} {{\n  {prop}: {rem_value};\n}}\n")
            directions = {
                "t": ["top"],
                "b": ["bottom"],
                "l": ["left"],
                "r": ["right"],
                "x": ["left", "right"],
                "y": ["top", "bottom"]
            }
            for short, sides in directions.items():
                css_lines = []
                for side in sides:
                    css_lines.append(f"  {prop}-{side}: {rem_value};")
                # Only one closing brace
                css.append(f".{prefix}{short}-{value.replace('.', '')} {{\n" + "\n".join(css_lines) + "\n}\n")

    # Width and height classes
    width_values = ["1px", "1%", "5%", "10%", "25%", "50%", "75%", "100%"]
    for value in width_values:
        px_class = f".w{value.replace('%', '').replace('px', '')} {{\n  width: {value};\n}}\n"
        css.append(px_class)

    height_values = ["1px", "1%", "5%", "10%", "25%", "50%", "75%", "100%"]
    for value in height_values:
        px_class = f".h{value.replace('%', '').replace('px', '')} {{\n  height: {value};\n}}\n"
        css.append(px_class)

    return "\n".join(css)

# Write to a file
with open("framework.css", "w") as f:
    f.write(generate_css())

print("CSS framework generated successfully!")
