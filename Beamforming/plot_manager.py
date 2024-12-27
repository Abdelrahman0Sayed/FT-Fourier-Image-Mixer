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
    def update(self, theta, pattern, steering_angles, show_full_pattern=False):
        # Input validation
        if pattern is None or len(pattern) == 0 or theta is None:
            print("Invalid pattern or theta data")
            self.clear()
            return
        

        print(f'show_full_pattern: {show_full_pattern}')
        if show_full_pattern:
            # Create full 360° pattern
            theta_full = np.linspace(0, 2*np.pi, len(theta)*2)
            pattern_full = np.concatenate([pattern, np.flip(pattern)])
            theta = theta_full
            pattern = pattern_full
            
        print(f"Input stats:")
        print(f"- Pattern shape: {pattern.shape}")
        print(f"- Pattern values: {pattern[:5]}...")  # Debug first few values
        print(f"- Pattern unique values: {len(np.unique(pattern))}")
        
        # Complex pattern processing
        pattern_mag = np.abs(pattern)
        pattern_db = 20 * np.log10(np.clip(pattern_mag, 1e-10, np.max(pattern_mag)))
        pattern_db = np.clip(pattern_db, -40, 0)
        plot_pattern = pattern_db + 40
        
        print(f"Pattern processing:")
        print(f"- dB range: [{np.min(pattern_db):.1f}, {np.max(pattern_db):.1f}]")
        
        # Setup plot
        self.figure.clear()
        ax = self.figure.add_subplot(111, projection='polar')
        #x.set_theta_zero_location('N')
        #x.set_theta_direction(-1)
        
        # Define masks with better thresholds
        main_lobe_threshold = -3  # -3dB point
        side_lobe_threshold = -20
        
        main_lobe_mask = pattern_db >= main_lobe_threshold
        side_lobe_mask = (pattern_db < main_lobe_threshold) & (pattern_db >= side_lobe_threshold)

        # Base pattern plot
        ax.plot(theta, plot_pattern, 'w-', alpha=0.3, zorder=1, linewidth=1)

        # Fill patterns with proper order
        if np.any(main_lobe_mask):
            ax.fill_between(theta, 0, plot_pattern,
                          where=main_lobe_mask,
                          color='#2196f3', alpha=0.6,
                          label='Main Lobe',
                          zorder=3)

        if np.any(side_lobe_mask):
            ax.fill_between(theta, 0, plot_pattern,
                          where=side_lobe_mask,
                          color='#ff9800', alpha=0.4,
                          label='Side Lobes',
                          zorder=2)

        # Steering angles
        if steering_angles:
            for angle in steering_angles:
                if angle != 0:
                    angle_rad = np.radians(angle)
                    ax.plot([angle_rad, angle_rad], [0, 40],
                           color='#ff5722', linestyle='--',
                           linewidth=1.5, alpha=0.7,
                           label=f'Steering {angle}°',
                           zorder=4)

        # Grid and styling
        ax.grid(True, color='white', alpha=0.2, linestyle=':')
        
        # Angle labels
        angles = np.arange(0, 360, 15)
        ax.set_xticks(np.radians(angles))
        ax.set_xticklabels([f'{int(ang)}°' for ang in angles],
                        fontsize=8, color=self.config.text_color)
        
        # Magnitude labels  
        
        
        # Enhanced magnitude labels
        ax.set_yticks(np.linspace(0, 40, 5))
        magnitude_labels = [f'{int(db):d}' for db in np.linspace(-40, 0, 5)]
        ax.set_yticklabels(magnitude_labels, color=self.config.text_color)
        
        # Final styling
        ax.set_ylim(0, 45)
        ax.set_title('Beam Pattern Analysis',
                    color=self.config.text_color,
                    pad=20, fontsize=14, fontweight='bold')
        
        # Legend
        
        
        # Legend with better positioning
        ax.legend(loc='upper right',
                 bbox_to_anchor=(1.2, 1.1),
                 facecolor='#2d2d2d',
                 edgecolor='none',
                 labelcolor=self.config.text_color)
        
        self.figure.tight_layout()
        

class InterferencePlot(BasePlot):
    def update(self, x, y, interference):
        if interference is None or x is None or y is None:
            self.clear()
            return
            
        if not isinstance(interference, np.ndarray):
            print("Invalid interference data type")
            return
            
        print(f"Interference stats - Min: {np.min(interference)}, Max: {np.max(interference)}")
            
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        # Convert to dB with proper handling
        magnitude = np.abs(interference)
        max_value = np.max(magnitude)
        
        if max_value > 0:
            db_values = 20 * np.log10(magnitude / max_value)
            # Clip to reasonable dB range
            db_values = np.clip(db_values, -60, 0)
        else:
            print("Warning: Zero magnitude interference pattern")
            db_values = np.zeros_like(magnitude) - 60
            
        print(f"dB values - Min: {np.min(db_values)}, Max: {np.max(db_values)}")
        
        im = ax.imshow(db_values,
                      extent=[x.min(), x.max(), y.min(), y.max()],
                      origin='lower',
                      cmap=self.config.cmap,
                      aspect='equal',
                      vmin=self.config.vmin,
                      vmax=self.config.vmax)
        
        self._setup_axis_style(ax)
        ax.set_title('Interference Pattern (dB)', 
                    color=self.config.text_color, pad=10)
        ax.set_xlabel('X Position (λ)', color=self.config.text_color)
        ax.set_ylabel('Y Position (λ)', color=self.config.text_color)
        
        divider = make_axes_locatable(ax)
        cax = divider.append_axes("right", size="5%", pad=0.05)
        cbar = self.figure.colorbar(im, cax=cax, label='Relative Power (dB)')
        cbar.ax.yaxis.label.set_color(self.config.text_color)
        cbar.ax.tick_params(colors=self.config.text_color)
        
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
