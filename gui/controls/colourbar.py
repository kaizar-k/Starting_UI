from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.cm import ScalarMappable
from matplotlib.colors import Normalize
from matplotlib.figure import Figure


def create_turbo_colorbar(master, width=0.7, height=3.2, top_label="Max Pa", bottom_label="0 Pa"):
    """Create a fixed Turbo decorative legend with a top/bottom label scheme."""
    fig = Figure(figsize=(width, height), dpi=100)
    ax = fig.add_axes([0.25, 0.08, 0.25, 0.84])
    canvas = FigureCanvasTkAgg(fig, master=master)

    norm = Normalize(vmin=0.0, vmax=1.0)
    mappable = ScalarMappable(norm=norm, cmap="turbo")
    mappable.set_array([])
    colourbar = ax.figure.colorbar(mappable, cax=ax, orientation="vertical")
    colourbar.set_ticks([])
    colourbar.ax.set_title("")
    ax.text(0.5, 1.04, top_label, ha="center", va="bottom", fontsize=8, transform=ax.transAxes)
    ax.text(0.5, -0.04, bottom_label, ha="center", va="top", fontsize=8, transform=ax.transAxes)
    canvas.draw_idle()

    return fig, ax, canvas
