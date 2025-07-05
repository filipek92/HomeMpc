from flask import Blueprint, request, redirect, url_for
import json
from options import VARIABLES_SPEC

SETTINGS_FILE = "mpc_settings.json"
settings_bp = Blueprint("settings_bp", __name__)

def load_settings():
    try:
        with open(SETTINGS_FILE, "r") as f:
            settings = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, ValueError):
        settings = {}
    # Doplnění defaultních hodnot podle VARIABLES_SPEC["options"]
    spec = VARIABLES_SPEC["options"]
    for key, meta in spec.items():
        if key not in settings:
            if "default" in meta:
                settings[key] = meta["default"]
            elif meta["type"] == "bool":
                settings[key] = False
            elif meta["type"] == "float":
                settings[key] = 0.0
    return settings

def save_settings(settings):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=2)

@settings_bp.route("/settings", methods=["GET", "POST"])
def settings():
    current = load_settings()
    spec = VARIABLES_SPEC["options"]
    if request.method == "POST":
        for key in spec:
            if spec[key]["type"] == "bool":
                current[key] = key in request.form
            elif spec[key]["type"] == "float":
                val = request.form.get(key)
                if val:
                    current[key] = float(val)
        save_settings(current)
        return redirect('./')
    # Vykreslení formuláře s jednotkami a rozsahem
    form_html = """
    <h1>Nastavení MPC</h1>
    <form method='post' style='max-width:400px;padding:1em;background:#f9f9f9;border-radius:8px;'>
    <table style='width:100%;border-collapse:collapse;'>
    <tr><th style='text-align:left'>Parametr</th><th>Hodnota</th><th>Jednotka</th><th>Rozsah</th></tr>
    """
    for key, meta in spec.items():
        val = current.get(key, meta.get("default", ""))
        unit = meta.get("unit", "")
        rng = meta.get("range", None)
        if meta["type"] == "bool":
            checked = "checked" if val else ""
            form_html += f"<tr><td>{key}</td><td><input type='checkbox' name='{key}' {checked}></td><td>{unit}</td><td></td></tr>"
        else:
            minval = f"min='{rng[0]}'" if rng and rng[0] is not None else ""
            maxval = f"max='{rng[1]}'" if rng and rng[1] is not None else ""
            step = "step='any'"
            form_html += f"<tr><td>{key}</td><td><input type='number' name='{key}' value='{val}' {minval} {maxval} {step}></td><td>{unit}</td><td>{rng if rng else ''}</td></tr>"
    form_html += """
    </table>
    <button type='submit' style='margin-top:1em'>Uložit</button>
    </form>
    <a href='./'>Zpět</a>
    """
    return form_html
