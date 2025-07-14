from flask import Blueprint, request, redirect, url_for
import json
from options import VARIABLES_SPEC
import os.path
from powerplan_environment import SETTINGS_FILE

settings_bp = Blueprint("settings_bp", __name__)

def load_settings():
    try:
        print(f"Loading settings from {SETTINGS_FILE}")
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
    # Uloží pouze hodnoty, které se liší od defaultu
    from options import VARIABLES_SPEC
    spec = VARIABLES_SPEC["options"]
    to_save = {}
    for key, meta in spec.items():
        val = settings.get(key, None)
        default = meta.get("default", False if meta["type"] == "bool" else 0.0 if meta["type"] == "float" else None)
        if val != default:
            to_save[key] = val
    with open(SETTINGS_FILE, "w") as f:
        print(f"Saving settings to {SETTINGS_FILE}")
        json.dump(to_save, f, indent=2)

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
        
        # Automaticky spustit novou optimalizaci po uložení nastavení
        try:
            from powerplan_server import compute_and_cache
            compute_and_cache()
        except Exception as e:
            print(f"Chyba při automatickém přepočtu optimalizace: {e}")
        
        return redirect('./')
    # Vykreslení moderního formuláře
    form_html = """
    <!DOCTYPE html>
    <html lang="cs">
    <head>
        <title>HomeOptim - Nastavení MPC</title>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
        <style>
            :root {
                --primary-color: #3B82F6;
                --secondary-color: #8B5CF6;
                --success-color: #10B981;
                --warning-color: #F59E0B;
                --danger-color: #EF4444;
                --dark-color: #1F2937;
                --light-color: #F8FAFC;
                --bg-primary: #F9FAFB;
                --bg-secondary: #FFFFFF;
                --border-color: #E5E7EB;
                --text-primary: #111827;
                --text-secondary: #6B7280;
                --text-muted: #9CA3AF;
                --shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
                --shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);
                --shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1);
                --shadow-xl: 0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1);
                --border-radius-sm: 0.375rem;
                --border-radius-md: 0.5rem;
                --border-radius-lg: 0.75rem;
                --border-radius-xl: 1rem;
                --transition-fast: 0.15s ease-in-out;
                --transition-normal: 0.2s ease-in-out;
                --transition-slow: 0.3s ease-in-out;
            }

            * { box-sizing: border-box; }

            body {
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                margin: 0;
                padding: 0;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: var(--text-primary);
                line-height: 1.6;
                min-height: 100vh;
            }

            .container {
                max-width: 1000px;
                margin: 0 auto;
                padding: 2rem 1rem;
            }

            .header {
                background: rgba(255, 255, 255, 0.98);
                backdrop-filter: blur(20px);
                border-radius: var(--border-radius-xl);
                padding: 1.5rem 2rem;
                margin-bottom: 2rem;
                box-shadow: var(--shadow-xl);
                border: 1px solid rgba(255, 255, 255, 0.2);
                display: flex;
                justify-content: space-between;
                align-items: center;
                flex-wrap: wrap;
                gap: 1rem;
                position: relative;
                overflow: hidden;
            }

            .header::before {
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                height: 4px;
                background: linear-gradient(90deg, var(--primary-color), var(--secondary-color), var(--success-color));
            }

            .header h1 {
                margin: 0;
                font-size: 2rem;
                font-weight: 700;
                color: var(--dark-color);
                display: flex;
                align-items: center;
                gap: 0.75rem;
            }

            .header h1 i {
                color: var(--primary-color);
            }

            .back-link {
                background: var(--text-secondary);
                color: white;
                text-decoration: none;
                padding: 0.5rem 1rem;
                border-radius: var(--border-radius-md);
                font-size: 0.875rem;
                font-weight: 500;
                transition: all 0.2s;
                display: flex;
                align-items: center;
                gap: 0.5rem;
            }

            .back-link:hover {
                background: var(--dark-color);
                transform: translateY(-1px);
            }

            .form-container {
                background: rgba(255, 255, 255, 0.98);
                backdrop-filter: blur(20px);
                border-radius: var(--border-radius-xl);
                padding: 2rem;
                box-shadow: var(--shadow-lg);
                border: 1px solid rgba(255, 255, 255, 0.2);
            }

            .settings-table {
                width: 100%;
                border-collapse: collapse;
                margin-top: 1rem;
            }

            .settings-table th {
                background: var(--light-color);
                color: var(--text-primary);
                font-weight: 600;
                padding: 1rem 0.75rem;
                text-align: left;
                border-bottom: 2px solid var(--border-color);
                font-size: 0.875rem;
            }

            .settings-table td {
                padding: 1rem 0.75rem;
                border-bottom: 1px solid var(--border-color);
                font-size: 0.875rem;
            }

            .settings-table tr:hover {
                background: rgba(59, 130, 246, 0.05);
            }

            .settings-table tr.modified {
                background: rgba(251, 191, 36, 0.1);
                border-left: 4px solid var(--warning-color);
            }

            .form-input {
                width: 100%;
                padding: 0.5rem 0.75rem;
                border: 1px solid var(--border-color);
                border-radius: var(--border-radius-sm);
                font-size: 0.875rem;
                background: white;
                transition: all 0.2s;
            }

            .form-input:focus {
                outline: none;
                border-color: var(--primary-color);
                box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
            }

            .form-checkbox {
                width: 1.25rem;
                height: 1.25rem;
                accent-color: var(--primary-color);
                cursor: pointer;
            }

            .btn-save {
                background: var(--success-color);
                color: white;
                border: none;
                padding: 0.75rem 2rem;
                border-radius: var(--border-radius-md);
                font-size: 1rem;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.2s;
                display: flex;
                align-items: center;
                gap: 0.5rem;
                margin-top: 2rem;
            }

            .btn-save:hover {
                background: #059669;
                transform: translateY(-1px);
                box-shadow: var(--shadow-md);
            }

            .parameter-name {
                font-weight: 600;
                color: var(--text-primary);
            }

            .default-value {
                color: var(--text-secondary);
                font-size: 0.8rem;
            }

            .unit {
                color: var(--text-secondary);
                font-weight: 500;
            }

            .range {
                color: var(--text-secondary);
                font-size: 0.8rem;
                font-family: 'Monaco', 'Consolas', monospace;
            }

            @media (max-width: 768px) {
                .container {
                    padding: 1rem 0.5rem;
                }

                .header {
                    flex-direction: column;
                    text-align: center;
                    padding: 1rem;
                }

                .header h1 {
                    font-size: 1.5rem;
                }

                .form-container {
                    padding: 1rem;
                }

                .settings-table {
                    font-size: 0.8rem;
                }

                .settings-table th,
                .settings-table td {
                    padding: 0.5rem 0.25rem;
                }

                /* Stack table on mobile */
                .settings-table, 
                .settings-table thead, 
                .settings-table tbody, 
                .settings-table th, 
                .settings-table td, 
                .settings-table tr {
                    display: block;
                }

                .settings-table thead tr {
                    position: absolute;
                    top: -9999px;
                    left: -9999px;
                }

                .settings-table tr {
                    border: 1px solid var(--border-color);
                    border-radius: var(--border-radius-md);
                    margin-bottom: 1rem;
                    padding: 1rem;
                    background: white;
                }

                .settings-table td {
                    border: none;
                    position: relative;
                    padding: 0.5rem 0;
                }

                .settings-table td:before {
                    content: attr(data-label) ": ";
                    font-weight: 600;
                    color: var(--text-primary);
                }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>
                    <i class="fas fa-cogs"></i>
                    Nastavení MPC optimalizátoru
                </h1>
                <a href="./" class="back-link">
                    <i class="fas fa-arrow-left"></i>
                    Zpět na dashboard
                </a>
            </div>

            <div class="form-container">
                <form method="post">
                    <table class="settings-table">
                        <thead>
                            <tr>
                                <th>Parametr</th>
                                <th>Hodnota</th>
                                <th>Výchozí</th>
                                <th>Jednotka</th>
                                <th>Rozsah</th>
                            </tr>
                        </thead>
                        <tbody>
    """
    for key, meta in spec.items():
        val = current.get(key, meta.get("default", ""))
        unit = meta.get("unit", "")
        rng = meta.get("range", None)
        default = meta.get("default", False if meta["type"] == "bool" else 0.0 if meta["type"] == "float" else None)
        is_modified = val != default
        row_class = " class='modified'" if is_modified else ""
        default_disp = "ano" if (meta["type"] == "bool" and default) else ("ne" if meta["type"] == "bool" else default)
        
        range_display = ""
        if rng:
            if isinstance(rng, list) and len(rng) == 2:
                range_display = f"[{rng[0]} - {rng[1]}]"
            else:
                range_display = str(rng)
        
        if meta["type"] == "bool":
            checked = "checked" if val else ""
            form_html += f"""
                            <tr{row_class}>
                                <td data-label="Parametr" class="parameter-name">{key}</td>
                                <td data-label="Hodnota">
                                    <input type="checkbox" name="{key}" {checked} class="form-checkbox">
                                </td>
                                <td data-label="Výchozí" class="default-value">{default_disp}</td>
                                <td data-label="Jednotka" class="unit">{unit}</td>
                                <td data-label="Rozsah" class="range">{range_display}</td>
                            </tr>"""
        else:
            minval = f"min='{rng[0]}'" if rng and len(rng) >= 2 and rng[0] is not None else ""
            maxval = f"max='{rng[1]}'" if rng and len(rng) >= 2 and rng[1] is not None else ""
            step = "step='any'"
            form_html += f"""
                            <tr{row_class}>
                                <td data-label="Parametr" class="parameter-name">{key}</td>
                                <td data-label="Hodnota">
                                    <input type="number" name="{key}" value="{val}" {minval} {maxval} {step} class="form-input">
                                </td>
                                <td data-label="Výchozí" class="default-value">{default_disp}</td>
                                <td data-label="Jednotka" class="unit">{unit}</td>
                                <td data-label="Rozsah" class="range">{range_display}</td>
                            </tr>"""
    form_html += """
                        </tbody>
                    </table>
                    
                    <button type="submit" class="btn-save">
                        <i class="fas fa-save"></i>
                        Uložit nastavení
                    </button>
                </form>
                
                <div style="margin-top: 2rem; padding: 1rem; background: rgba(59, 130, 246, 0.1); border-radius: var(--border-radius-md); border-left: 4px solid var(--primary-color);">
                    <h3 style="margin: 0 0 0.5rem 0; color: var(--primary-color); font-size: 1rem;">
                        <i class="fas fa-info-circle"></i> Informace
                    </h3>
                    <p style="margin: 0; font-size: 0.875rem; color: var(--text-secondary);">
                        Řádky označené žlutou barvou obsahují hodnoty odlišné od výchozího nastavení. 
                        <strong>Po uložení se optimalizace automaticky přepočítá s novými parametry</strong> - 
                        proces může trvat několik sekund. Budete přesměrováni na hlavní stránku s aktualizovanými výsledky.
                    </p>
                </div>
            </div>
        </div>
        
        <script>
            // Loading indicator when form is submitted
            const form = document.querySelector('form');
            const submitButton = document.querySelector('.btn-save');
            
            form.addEventListener('submit', function(e) {
                // Show loading state
                submitButton.disabled = true;
                submitButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Ukládám a přepočítávám...';
                
                // Add loading overlay to the whole page
                const overlay = document.createElement('div');
                overlay.style.cssText = `
                    position: fixed;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 100%;
                    background: rgba(0, 0, 0, 0.7);
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    z-index: 9999;
                    color: white;
                    font-size: 1.2rem;
                `;
                overlay.innerHTML = `
                    <div style="text-align: center;">
                        <i class="fas fa-spinner fa-spin" style="font-size: 2rem; margin-bottom: 1rem;"></i>
                        <div>Ukládám nastavení a přepočítávám optimalizaci...</div>
                        <div style="font-size: 0.9rem; margin-top: 0.5rem; opacity: 0.8;">Prosím počkejte, může to chvilku trvat.</div>
                    </div>
                `;
                document.body.appendChild(overlay);
            });
            
            // Auto-save on form change with debounce
            let saveTimeout;
            const inputs = form.querySelectorAll('input');
            
            inputs.forEach(input => {
                input.addEventListener('change', () => {
                    clearTimeout(saveTimeout);
                    // Visual feedback
                    const row = input.closest('tr');
                    if (row) {
                        row.style.background = 'rgba(59, 130, 246, 0.1)';
                        setTimeout(() => {
                            row.style.background = '';
                        }, 1000);
                    }
                });
            });
        </script>
    </body>
    </html>
    """
    return form_html
