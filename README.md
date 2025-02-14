

# Beamforming Simulator & Fourier Transform Mixer

## Overview
This project combines two distinct yet fundamental applications:  
1. **Fourier Transform Mixer**: A desktop tool for analyzing the relative importance of Fourier transform components (magnitude, phase, real, and imaginary) in 2D signals.  
2. **Beamforming Simulator**: A simulation environment for visualizing and customizing 2D beamforming patterns, inspired by real-world applications like 5G communications, ultrasound, and tumor ablation.

---

## Features

### Part A: Fourier Transform Mixer
#### **1. Image Viewers**
- **Multiple Displays**: View four grayscale images simultaneously in independent viewports.
  - **Grayscale Conversion**: Automatically convert colored images to grayscale upon upload.
  - **Unified Size**: Automatically rescale images to the smallest dimensions among the uploaded ones.
  - **Component Display**: Toggle between FT Magnitude, Phase, Real, and Imaginary components using a combo-box.
  - **Image Browsing**: Replace any image dynamically through a double-click browse option.
- **Brightness/Contrast Adjustment**: Adjust image brightness and contrast in real-time via mouse dragging.

#### **2. Component Mixing**
- **Weighted FT Mixing**: Combine the Fourier transforms of all four images with customizable weights (using sliders) for magnitude and phase or real and imaginary components.
- **Region Selection**: Select and emphasize inner (low frequency) or outer (high frequency) regions of the FT using interactive rectangular tools. These selections are synchronized across all images.

##### Magnitude/Phase Mixing
![mag_phase_mix](images/mix1.png)

##### Real/Imaginary Mixing
![real_img_mix](images/real_img_mix.png)

#### **3. Real-Time Processing**
- **iFFT Reconstruction**: Perform inverse Fourier transform (iFFT) for visualization of results in designated output viewports.
- **Threaded Operations**: Cancel ongoing operations and restart with new settings to ensure smooth real-time adjustments.
- **Progress Bar**: Visual feedback for long-running processes.

##### **Demo**
https://github.com/user-attachments/assets/f85c529e-3b82-441c-ba72-cf4bb9d70742

---

### Part B: Beamforming Simulator
#### **1. Array Geometry Customization**
- **Array Types**: Support for linear and curved phased arrays with adjustable geometry parameters such as curvature and element spacing.
- **Real-Time Steering**: Adjust beam steering angles interactively to observe changes in the beam profile.

#### **2. Frequency and Delay Management**
- **Operating Frequencies**: Customize frequencies for each array unit in real-time, with presets for common applications.
- **Phase Delays/Shifts**: Manage system parameters like delays and shifts for enhanced beamforming accuracy.

#### **3. Visualization**
- **Beam Profile**: Real-time beam pattern visualization in polar coordinates.
- **Interference Maps**: View constructive and destructive interference fields.
- **Array Layout**: Interactive schematic representation of array unit configurations.

#### **4. Scenario Management**
- **Predefined Scenarios**: Simulate preconfigured scenarios such as:
  - **5G Communications**: Base station array configurations.
![5G](images/5G.png)
  - **Medical Ultrasound**: Probe geometry and beam characteristics.
![US](images/US.png)
  - **Tumor Ablation**: Ablation-specific arrays for targeted regions.
![Tumor](images/tumor.png)
- **Custom Scenarios**: Save, load, and fine-tune configurations with parameter files.


---

## Usage

### Fourier Transform Mixer
1. Load up to four grayscale images into the viewers.
2. Explore their Fourier transform components using the drop-down menu.
3. Use sliders to adjust the weights for mixing FT components.
4. Draw rectangular selections on FT components to specify inner or outer regions for reconstruction.
5. Visualize the resulting iFFT in the output viewports.

### Beamforming Simulator
1. Define array geometry and operating frequencies for phased arrays.
2. Adjust steering angles and observe the changes in beam and interference patterns.
3. Load and tweak scenarios to match specific use cases.


## **Setup**

- Clone the repo
```bash
git clone https://github.com/Abdelrahman0Sayed/FT-Fourier-Image-Mixer.git
```
- Enter Project Folder
```bash
cd FT-Fourier-Image-Mixer
```
- Install the requirements
```bash
pip install -r requirements.txt
```
- Run the Application
```bash
# Run Mixer
python MainClasses.py
# Run Beamforming
python beamforming.py
```

## Contributors <a name = "Contributors"></a>
<table>
  <tr>
    <td align="center">
    <a href="https://github.com/Abdelrahman0Sayed" target="_black">
    <img src="https://avatars.githubusercontent.com/u/113141265?v=4" width="150px;" alt="Abdelrahman Sayed Nasr"/>
    <br />
    <sub><b>Abdelrahman Sayed Nasr</b></sub></a>
    </td>
    <td align="center">
    <a href="https://github.com/MahmoudBL83" target="_black">
    <img src="https://avatars.githubusercontent.com/u/95527734?v=4" width="150px;" alt="Mahmoud Bahaa"/>
    <br />
    <sub><b>Mahmoud Bahaa</b></sub></a>
    </td>
    <td align="center">
    <a href="https://github.com/momowalid" target="_black">
    <img src="https://avatars.githubusercontent.com/u/127145133?v=4" width="150px;" alt="Mohamed Walid"/>
    <br />
    <sub><b>Mohamed Walid</b></sub></a>
    </td>
    <td align="center">
    <a href="https://github.com/Karim12Elbadwy" target="_black">
    <img src="https://avatars.githubusercontent.com/u/190773888?v=4" width="150px;" alt="Kareem El-Badawi"/>
    <br />
    <sub><b>Kareem El-Badawi</b></sub></a>
    </td>
    <td align="center">
    <a href="https://github.com/NadaMohamedElBasel" target="_black">
    <img src="https://avatars.githubusercontent.com/u/110432081?v=4" width="150px;" alt="Nada El-Basel"/>
    <br />
    <sub><b>Nada El-Basel</b></sub></a>
    </td>
      </tr>
