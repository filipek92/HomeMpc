import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime, timedelta

def presentation_matplotlib(solution, show=True, save_path=None):
    times = [datetime.fromisoformat(t) for t in solution["times"]]
    ts = {**solution["inputs"], **solution["outputs"]}

    fig, axs = plt.subplots(4, 1, figsize=(16, 12), sharex=True)

    # 1. Stavy (SoC)
    axs[0].plot([t + timedelta(hours=1) for t in times], ts["B_SOC_percent"], label="SoC baterie", color="#4db6ac")
    axs[0].plot([t + timedelta(hours=1) for t in times], ts["H_SOC_percent"], label="SoC bojleru", color="#9d770f")
    axs[0].set_ylabel("Energie [%]")
    axs[0].legend()
    axs[0].set_title("Stavy (SoC)")

    # 2. Výkony
    bar_keys = [
        ("B_charge", "Nabíjení baterie", "#f06292", 0.7),
        ("B_discharge", "Vybíjení baterie", "#4db6ac", 0.7, True),
        ("G_buy", "Nákup ze sítě", "#488fc2", 0.5),
        ("G_sell", "Prodej do sítě", "#8353d1", 0.5, True),
    ]
    n_bars = len(bar_keys)
    width = 0.18  # šířka jednoho sloupce
    offsets = np.linspace(-width*n_bars/2, width*n_bars/2, n_bars, endpoint=False)
    for i, (key, label, color, alpha, *invert) in enumerate(bar_keys):
        vals = -np.array(ts[key]) if invert and invert[0] else np.array(ts[key])
        axs[1].bar(
            [t + timedelta(hours=offsets[i]) for t in times],
            vals,
            width=width/18,
            label=label,
            color=color,
            alpha=alpha,
            align="center",
        )
    axs[1].step(times, ts["H_in"], label="Ohřev", color="#c97a94", where="mid")
    axs[1].step(times, -np.array(ts["H_out"]), label="Výstup z bojleru", color="#0f9d58", where="mid")
    axs[1].step(times, ts["fve_pred"], label="FVE výroba", color="#ff9800", where="mid")
    axs[1].step(times, ts["load_pred"], label="Spotřeba", color="#488fc2", where="mid")
    axs[1].set_ylabel("Výkon [kW]")
    axs[1].legend(ncol=4)
    axs[1].set_title("Výkony")

    # 3. Ceny
    axs[2].step(times, ts["buy_price"], label="Cena nákup", color="#488fc2", where="mid")
    axs[2].step(times, ts["sell_price"], label="Cena prodej", color="#8353d1", where="mid")
    axs[2].set_ylabel("Cena [Kč/kWh]")
    axs[2].legend()
    axs[2].set_title("Ceny elektřiny")

    # 4. Tepelné ztráty a venkovní teplota
    axs[3].plot(times, ts["heating_demand"], label="Tepelné ztráty", color="#0f9d58")
    axs[3].plot(times, ts["outdoor_temps"], label="Venkovní teplota", color="#ff9800")
    axs[3].set_ylabel("kWh, °C")
    axs[3].legend()
    axs[3].set_title("Tepelné ztráty a venkovní teplota")

    plt.xlabel("Čas")
    plt.tight_layout()
    if save_path:
        plt.savefig(save_path)
    if show:
        plt.show()
    plt.close(fig)
