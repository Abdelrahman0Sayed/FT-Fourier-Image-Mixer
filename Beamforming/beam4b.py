import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, RadioButtons

# Default values
Nr = 8  # Initial number of elements # both geometries parameter
N_fft = 1024  #number of FFT bins Determines the angular resolution
theta_bins = np.arcsin(np.linspace(-1, 1, N_fft))  # Map the FFT bins to angles in radians  # half circle 
#theta_bins =np.linspace(-1*np.pi, np.pi, N_fft)  # full circle 
default_magnitude = 1
default_phases = np.zeros(64)  # Allocate space for up to 64 elements
default_frequencies = np.ones(10)  # Default frequencies (up to 10)
geometry_type = "Linear"  # Default geometry
angle_span = np.pi / 2  # Initial angle span for curvature (90 degrees)  # for curved geometry only #Total angle spanned by the curved array, in radians.
curvature_factor = 1  # Default curvature factor  # for curved geometry only # the "radius" or extent of the curve.(larger values create a more stretched curve)
frequency = 1e9  # 1 GHz signal frequency as initial setup,configuration and calculations
wavelength = 3e8 / frequency  # free space speed / frequency  # assuming electromagnetic waves(eg.5G ) so used speed of light # if acoustic waves(eg.Ultrasound) speed will change according to the medium
element_spacing = wavelength / 2  # Typical spacing is half the wavelength # for linear geometry only
steering_angle = 0  # Initial steering angle (radians)   # both geometries parameter
grid_size = 500
x = np.linspace(-10, 10, grid_size)
y = np.linspace(-10, 10, grid_size)
X, Y = np.meshgrid(x, y)
# Set up the figure and axes
fig = plt.figure('Beamforming Slider App', figsize=(14, 10))
plt.subplots_adjust(left=0.1, bottom=0.05, right=0.9, top=0.95)

# Polar plot for Beam Pattern 
ax_polar = plt.axes([0.1, 0.55, 0.35, 0.35], polar=True)
polar_plot, = ax_polar.plot(theta_bins, np.zeros(N_fft))
ax_polar.set_theta_zero_location('N') # make 0 degrees point up
ax_polar.set_theta_direction(-1) # increase clockwise
ax_polar.set_thetamin(0)#-90  #-1*np.pi
ax_polar.set_thetamax(360)#90  #np.pi
ax_polar.set_ylim([-30, 10]) # range of the radial axis in polar plot 

#  inference map 
ax_inference = plt.axes([0.55, 0.55, 0.4, 0.35])  
inference_plot = ax_inference.imshow(np.zeros_like(X), extent=(-10, 10, -10, 10), cmap='seismic', origin='lower')
ax_inference.set_title("2D Interference Pattern")
ax_inference.set_xlabel("X-axis")
ax_inference.set_ylabel("Y-axis")
plt.colorbar(inference_plot, ax=ax_inference, label="Wave Amplitude")

# Function to calculate steering vector phases
def calculate_steering_phases():
    positions = calculate_positions()
    phases = -2 * np.pi * positions * np.sin(steering_angle) / wavelength # generalization to arbitrary array geometries, Real-valued phase shifts (radians)
    #phases=np.exp(-2j * np.pi * (element_spacing/wavelength) * np.arange(Nr) * np.sin(steering_angle))         # Uniform(equally spaced elements.) Linear Arrays ONLY (ULA)Complex-valued steering vector (phasors).
    return phases

# Function to calculate the element positions based on geometry
def calculate_positions():
    if geometry_type == "Linear":
         #positions = np.linspace(0, (Nr - 1)* element_spacing , Nr)  # Apply element spacing positions are scaled to actual physical distances (e.g., meters).>distorted?!
         positions = np.linspace(0, (Nr - 1) , Nr)  #Generates Nr equally spaced positions starting from 0 up to (Nr - 1). positions are unitless
    elif geometry_type == "Curved":
        angles = np.linspace(-angle_span / 2, angle_span / 2, Nr) #Divides the angle range into Nr equally spaced points.Elements are placed symmetrically about the center of the curve.
        positions = curvature_factor * np.sin(angles)   #Maps the angular positions to physical positions along the curve.
    return positions

# Function to calculate the beam pattern
def beam_pattern():
    num_frequencies = len(default_frequencies)
    beam = np.zeros(N_fft, dtype=np.complex128)#(FFT) produces complex-valued outputs,includes phase and magnitude information of the signal across frequencies.
    positions = calculate_positions()
    
    for freq in default_frequencies:
        w_mags = np.full(Nr, default_magnitude)
        w_phases = default_phases[:Nr]
        w = w_mags * np.exp(1j * (w_phases + 2 * np.pi * freq * positions)) #Computes a complex exponential to represent the phase and frequency-dependent steering. 
                                                                            #Adds the phase shift due to each element's position relative to the signal's frequency.
                                                                            # Scales the steering weights by the element magnitudes.
                                                                            #These weights "steer" the beam toward or away from certain directions.
        w = np.conj(w)#Takes the complex conjugate of the steering weights, reversing the phase to "align" signals coming from the target direction.
        w_padded = np.concatenate((w, np.zeros(N_fft - Nr)))  # Pads the steering vector w with zeros to match the size of N_fft for the FFT.Zero padding improves frequency resolution in the FFT output.
    #     beam += np.fft.fftshift(np.fft.fft(w_padded) * Nr)#Converts the padded steering vector into the frequency domain.Rearranges the FFT output so that the zero-frequency component is centered.resulting beam pattern is scaled proportionally to the number of elements.accumulate contributions from all frequencies in default_frequencies
    
    # w_fft_dB = 10 * np.log10((np.abs(beam) ** 2) / (N_fft * num_frequencies))#The combined beamforming response is normalized and converted to a logarithmic scale (dB), representing of the power distribution(magnitude squared).
    w_fft_dB = 10*np.log10(np.abs(np.fft.fftshift(np.fft.fft(w_padded)))**2) # magnitude of fft in dB
    w_fft_dB -= np.max(w_fft_dB) # normalize to 0 dB at peak
    theta_max = theta_bins[np.argmax(w_fft_dB)]
    # ax_polar.plot([theta_max], [np.max(w_fft_dB)],'ro')
    # ax_polar.text(theta_max - 0.1, np.max(w_fft_dB) - 4, np.round(theta_max * 180 / np.pi))
    return w_fft_dB


def interference_pattern():
    positions = calculate_positions()
    wave_pattern = np.zeros_like(X, dtype=np.complex128)

    for idx, position in enumerate(positions):
        source_x = position * np.cos(steering_angle)  # Apply steering angle
        source_y = position * np.sin(steering_angle)
        r = np.sqrt((X - source_x)**2 + (Y - source_y)**2)
        phase_shift = default_phases[idx]
        #phase_shift = default_phases[idx] + np.pi / 2  # Adjust the phase shift to focus on the main lobe
        #phase_shift = default_phases[idx] + -2 * np.pi * r / wavelength 
        #wave_pattern += np.exp(1j * phase_shift)
        wave_pattern += np.exp(1j * (2 * np.pi * r - phase_shift))

    return np.real(wave_pattern)


# Containers for sliders
freq_slider_axes = []
freq_sliders = []

# Sliders for curvature customization
ax_slider_angle_span = plt.axes([0.1, 0.05, 0.35, 0.03])
slider_angle_span = Slider(ax_slider_angle_span, 'Angle Span (radians)', 0, np.pi, valinit=angle_span)

ax_slider_curvature_factor = plt.axes([0.55, 0.05, 0.35, 0.03])
slider_curvature_factor = Slider(ax_slider_curvature_factor, 'Curvature Factor', 0, 2, valinit=curvature_factor)

# Slider for controlling element spacing (Linear geometry)
ax_slider_spacing = plt.axes([0.1, 0.08, 0.35, 0.03])
slider_spacing = Slider(ax_slider_spacing, 'Element Spacing', 0.1, 1, valinit=element_spacing)

# Single slider for steering angle
ax_slider_steering = plt.axes([0.1, 0.02, 0.35, 0.03])
slider_steering = Slider(ax_slider_steering, 'Steering Angle(rad)for applied delays/shifts', -np.pi/2, np.pi/2, valinit=steering_angle)

# Slider for controlling the number of elements
ax_slider_nr = plt.axes([0.1, 0.5, 0.35, 0.03])
slider_nr = Slider(ax_slider_nr, 'Nr transmitters/receivers', 1, 16, valinit=Nr, valstep=1)

# Slider for controlling the number of frequencies
ax_slider_freq_count = plt.axes([0.55, 0.5, 0.35, 0.03])
slider_freq_count = Slider(ax_slider_freq_count, 'Nr Frequencies', 1, 2, valinit=len(default_frequencies), valstep=1)


ax_radio_geometry = plt.axes([0.85, 0.9, 0.1, 0.1])  
radio_geometry = RadioButtons(ax_radio_geometry, ('Linear', 'Curved'))

# Function to create frequency sliders dynamically
def create_freq_sliders():
    global freq_slider_axes, freq_sliders
    for ax in freq_slider_axes:
        ax.remove()
    freq_slider_axes.clear()
    freq_sliders.clear()

    num_frequencies = int(slider_freq_count.val)
    slider_height = 0.15 / max(num_frequencies, 5)
    for i in range(num_frequencies):
        ax = plt.axes([0.55, 0.1 - i * slider_height, 0.35, slider_height - 0.005])
        slider = Slider(ax, f'Freq {i + 1}', 1, 10, valinit=default_frequencies[i])
        freq_slider_axes.append(ax)
        freq_sliders.append(slider)
        slider.on_changed(update)
    plt.draw()

# Update function
def update(val):
    global Nr, default_frequencies, geometry_type, angle_span, curvature_factor, steering_angle, element_spacing
    Nr = int(slider_nr.val)
    default_frequencies = np.array([slider.val for slider in freq_sliders])
    geometry_type = radio_geometry.value_selected  # Update geometry type
    angle_span = slider_angle_span.val  # Update angle span
    steering_angle = slider_steering.val  # Update steering angle
    curvature_factor = slider_curvature_factor.val  # Update curvature factor
    element_spacing = slider_spacing.val  # Update element spacing
    # Calculate steering phases
    default_phases[:Nr] = calculate_steering_phases()
    
    # Update plots
    w_fft_dB = beam_pattern()
   

    ax_polar.clear()  # Clear the previous polar plot to avoid overlapping
    ax_polar.plot(theta_bins, w_fft_dB)  # Plot the new beam pattern
    ax_polar.set_title("Beam Pattern")
    ax_polar.set_theta_zero_location('N')  # Set zero location to North
    ax_polar.set_theta_direction(-1)  # Set counterclockwise direction
    ax_polar.set_ylim([-30, 10])  # Set polar plot limits

    # Update interference map
    wave_pattern_real = interference_pattern()
    inference_plot.set_data(wave_pattern_real)
    inference_plot.set_clim(wave_pattern_real.min(), wave_pattern_real.max())


    if len(freq_sliders) != int(slider_freq_count.val):
        create_freq_sliders()
    
    fig.canvas.draw_idle()


# Initialize
slider_nr.on_changed(update)
slider_freq_count.on_changed(update)
radio_geometry.on_clicked(update)
slider_angle_span.on_changed(update)
slider_curvature_factor.on_changed(update)
slider_steering.on_changed(update)


# create_phase_sliders()
create_freq_sliders()
update(None)

plt.show()

