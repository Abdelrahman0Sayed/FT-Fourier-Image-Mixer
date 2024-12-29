from dataclasses import dataclass
from abc import ABC, abstractmethod
import numpy as np
from matplotlib.figure import Figure
from mpl_toolkits.axes_grid1 import make_axes_locatable

@dataclass
class PlotConfig:
    cmap: str = 'RdBu_r'
    vmin: float = -60
    vmax: float = 0
    grid_color: str = '#404040'
    background_color: str = '#1e1e1e'
    text_color: str = 'white'

class BasePlot(ABC):
    def __init__(self, figure: Figure, config: PlotConfig):
        self.figure = figure
        self.config = config
    
    @abstractmethod
    def update(self, *args, **kwargs):
        pass
    
    def _setup_axis_style(self, ax):
        ax.set_facecolor(self.config.background_color)
        ax.tick_params(colors=self.config.text_color)
        ax.grid(True, color=self.config.grid_color, alpha=0.3)

    def clear(self):
        self.figure.clear()
    
class PatternPlot(BasePlot):
    def _show_beam_metrics(self, ax, theta, pattern_db):
        """Calculate and display beam pattern metrics."""
        # Find main lobe peak
        peak_idx = np.argmax(pattern_db)
        peak_angle = np.degrees(theta[peak_idx])
        
        # Calculate -3dB beam width
        beam_width = self._calculate_beam_width(theta, pattern_db)
        
        # Add annotations
        text_props = dict(color='white', fontsize=10, transform=ax.transAxes)
        ax.text(1.2, 0.95, f'Peak: {peak_angle:.1f}°', **text_props)
        ax.text(1.2, 0.90, f'Beam Width: {beam_width:.1f}°', **text_props)

    def _calculate_beam_width(self, theta, pattern_db):
        """Calculate -3dB beam width."""
        mask = pattern_db >= -3
        if not np.any(mask):
            return 0
        crossing_points = np.where(np.diff(mask))[0]
        if len(crossing_points) >= 2:
            return abs(np.degrees(theta[crossing_points[1]] - theta[crossing_points[0]]))
        return 0

    def update(self, theta, pattern, steering_angles, show_full_pattern=False):
        """Update the beam pattern visualization."""
        if pattern is None or len(pattern) == 0 or theta is None:
            print("Invalid pattern or theta data")
            self.clear()
            return

        # 1. Setup polar plot
        self.figure.clear()
        ax = self.figure.add_subplot(111, projection='polar')
        ax.set_theta_zero_location('N')
        ax.set_theta_direction(-1)

        # 2. Process pattern based on full/half view
        if show_full_pattern:
            theta_full = np.concatenate([theta, theta + np.pi])
            pattern_full = np.concatenate([pattern, pattern])
            theta = theta_full
            pattern = pattern_full

        # 3. Convert to dB scale
        pattern_db = 20 * np.log10(np.clip(np.abs(pattern), 1e-10, None))
        pattern_db = np.clip(pattern_db, -40, 0)
        normalized_pattern = pattern_db + 40

        # 4. Create masks for lobes
        main_lobe_mask = pattern_db >= -3
        side_lobe_mask = (pattern_db < -3) & (pattern_db >= -20)

        # 5. Plot patterns
        ax.fill_between(theta, 0, normalized_pattern,
                        where=main_lobe_mask,
                        color='#2196f3', alpha=0.3,
                        label='Main Lobe (-3dB)')
        ax.fill_between(theta, 0, normalized_pattern,
                        where=side_lobe_mask,
                        color='#ff9800', alpha=0.2,
                        label='Side Lobes')

        # 7. Configure angle markers
        angles = np.arange(90, 450, 15)
        ax.set_xticks(np.radians(angles % 360))
        ax.set_xticklabels([''] * len(angles))

        # 8. Add steering angle indicators
        if steering_angles:
            for angle in steering_angles:
                if angle != 0:
                    angle_rad = np.radians(angle)
                    ax.plot([angle_rad, angle_rad], [0, 40],
                        color='#ff5722', linestyle='--',
                        linewidth=1.5, alpha=0.7,
                        label=f'Steering {angle}°')

        # 9. Final styling
        ax.grid(True, color='white', alpha=0.1, linestyle=':')
        ax.set_ylim(0, 45)
        ax.set_title('Beam Pattern Analysis',
                    color=self.config.text_color,
                    pad=20, fontsize=14, fontweight='bold')
        
        # 10. Configure legend
        ax.legend(loc='upper right',
                bbox_to_anchor=(1.2, 1.1),
                facecolor='#2d2d2d',
                edgecolor='none',
                labelcolor=self.config.text_color)

        self.figure.tight_layout()
            

class InterferencePlot(BasePlot):
    def update(self, x, y, interference):
        # Input validation
        if interference is None or x is None or y is None:
            self.clear()
            return
            
        if not isinstance(interference, np.ndarray):
            print("Invalid interference data type")
            return
            
        # Data processing
        magnitude = np.abs(interference)
        max_value = np.max(magnitude)
        
        if max_value > 0:
            db_values = 20 * np.log10(magnitude / max_value)
            db_values = np.clip(db_values, -60, 0)
        else:
            print("Warning: Zero magnitude interference pattern")
            db_values = np.zeros_like(magnitude) - 60
            
        print(f"Interference stats - Min: {np.min(interference)}, Max: {np.max(interference)}")
        print(f"dB values - Min: {np.min(db_values)}, Max: {np.max(db_values)}")
        
        # Plot creation
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        im = ax.imshow(db_values,
                    extent=[x.min(), x.max(), y.min(), y.max()],
                    origin='lower',
                    cmap=self.config.cmap,
                    aspect='equal',
                    vmin=self.config.vmin,
                    vmax=self.config.vmax)
        
        # Styling
        ax.set_title('Interference Pattern (dB)', color=self.config.text_color, pad=10)
        ax.set_xlabel('X Position (λ)', color=self.config.text_color)
        ax.set_ylabel('Y Position (λ)', color=self.config.text_color)
        ax.grid(True, color='#404040', alpha=0.5, linestyle='--')
        ax.tick_params(colors=self.config.text_color)
        
        # Colorbar
        divider = make_axes_locatable(ax)
        cax = divider.append_axes("right", size="5%", pad=0.05)
        cbar = self.figure.colorbar(im, cax=cax, label='Relative Power (dB)')
        cbar.ax.yaxis.label.set_color(self.config.text_color)
        cbar.ax.tick_params(colors=self.config.text_color)
        
        # Final layout
        self.figure.tight_layout()


class ArrayGeometryPlot(BasePlot):
    def _set_axis_limits(self, ax, x_positions, y_positions, min_range=1.0):
        """Set axis limits with minimum range validation"""
        x_min, x_max = min(x_positions), max(x_positions)
        y_min, y_max = min(y_positions), max(y_positions)
        
        # Ensure minimum range
        if abs(x_max - x_min) < min_range:
            center = (x_max + x_min) / 2
            x_min = center - min_range/2
            x_max = center + min_range/2
            
        if abs(y_max - y_min) < min_range:
            center = (y_max + y_min) / 2
            y_min = center - min_range/2
            y_max = center + min_range/2
        
        padding = max(x_max - x_min, y_max - y_min) * 0.2
        ax.set_xlim(x_min - padding, x_max + padding)
        ax.set_ylim(y_min - padding, y_max + padding)


    def update(self, positions):
        if not positions:
            self.clear()
            return
            
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        x_positions = [p[0] for p in positions]
        y_positions = [p[1] for p in positions]
        
        # Check dimensionality
        unique_x = np.unique(x_positions)
        unique_y = np.unique(y_positions)
        is_linear = len(unique_x) == 1 or len(unique_y) == 1
        
        # Draw elements
        ax.scatter(x_positions, y_positions,
                c='#2196f3', marker='o', s=200,
                edgecolor='white', linewidth=2,
                alpha=0.8, zorder=3)
        
        # Add element labels
        for i, (x, y) in enumerate(positions):
            ax.annotate(f'{i + 1}', (x, y),
                    color='white', ha='center', va='center',
                    fontweight='bold', zorder=4)
            ax.annotate(f'({x:.1f}, {y:.1f})', (x, y),
                    xytext=(0, -25), textcoords='offset points',
                    ha='center', va='top',
                    color=self.config.text_color, fontsize=8)
        
        # Draw boundary based on geometry
        if len(positions) > 1:
            if is_linear:
                # Linear array - connect points directly
                sorted_idx = np.argsort(x_positions) if len(unique_x) > 1 else np.argsort(y_positions)
                ax.plot([x_positions[i] for i in sorted_idx],
                    [y_positions[i] for i in sorted_idx],
                    'w--', alpha=0.3, zorder=1)
            else:
                try:
                    # Try convex hull with QJ option for non-linear arrays
                    from scipy.spatial import ConvexHull
                    hull = ConvexHull(positions, qhull_options='QJ')
                    for simplex in hull.simplices:
                        ax.plot([positions[simplex[0]][0], positions[simplex[1]][0]],
                            [positions[simplex[0]][1], positions[simplex[1]][1]],
                            'w--', alpha=0.3, zorder=1)
                except Exception as e:
                    print(f"Falling back to simple boundary: {str(e)}")
                    # Fallback: Draw lines between consecutive points
                    ax.plot(x_positions + [x_positions[0]],
                        y_positions + [y_positions[0]],
                        'w--', alpha=0.3, zorder=1)
        
        # Style configuration
        self._setup_axis_style(ax)
        ax.set_aspect('equal')
        self._set_axis_limits(ax, x_positions, y_positions)
        self.figure.tight_layout()
