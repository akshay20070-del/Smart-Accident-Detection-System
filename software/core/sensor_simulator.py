"""
Sensor Simulator Module.

Simulates 3-axis accelerometer readings (X, Y, Z in m/s^2) for various driving conditions:
- Stationary / Idling
- Normal Cruising
- Turning / Cornering
- Road Bumps & Potholes
- Sudden High-G Impact (Accident Collision)
"""

import random
from typing import Dict, Tuple


class SensorSimulator:
    """
    Generates synthetic accelerometer data representing realistic vehicular motion.
    Earth gravity along Z-axis is ~9.8 m/s^2 when vehicle is horizontal.
    """

    def __init__(self, sample_interval: float = 0.5):
        """
        Initialize the sensor simulator.

        Args:
            sample_interval: Simulation interval in seconds between samples.
        """
        self.sample_interval = sample_interval
        self.impact_active: bool = False
        self.impact_counter: int = 0
        self.current_mode: str = "NORMAL_CRUISE"

    def trigger_impact(self, duration_steps: int = 3) -> None:
        """
        Manually trigger a severe collision simulation.

        Args:
            duration_steps: Number of consecutive samples where high-G spike persists.
        """
        self.impact_active = True
        self.impact_counter = duration_steps

    def get_reading(self) -> Dict[str, float]:
        """
        Generate the next synthetic (X, Y, Z) acceleration reading in m/s^2.

        Returns:
            Dictionary with 'x', 'y', 'z', and simulated 'motion_type'.
        """
        # If an impact event is triggered
        if self.impact_active and self.impact_counter > 0:
            self.impact_counter -= 1
            if self.impact_counter <= 0:
                self.impact_active = False

            # Severe impact spike: 30 to 55 m/s^2 along dominant collision axis
            # Realistic crash: violent frontal/side deceleration and tilt
            crash_axis = random.choice(["frontal", "side", "rollover"])
            if crash_axis == "frontal":
                x = random.uniform(32.0, 48.0) * random.choice([-1, 1])
                y = random.uniform(-6.0, 6.0)
                z = random.uniform(12.0, 25.0)
            elif crash_axis == "side":
                x = random.uniform(-8.0, 8.0)
                y = random.uniform(30.0, 46.0) * random.choice([-1, 1])
                z = random.uniform(10.0, 22.0)
            else:  # rollover
                x = random.uniform(22.0, 35.0)
                y = random.uniform(25.0, 38.0)
                z = random.uniform(-15.0, 28.0)

            return {
                "x": round(x, 2),
                "y": round(y, 2),
                "z": round(z, 2),
                "motion_type": "COLLISION_IMPACT",
            }

        # Normal Driving Simulation with minor sensor noise
        noise_x = random.gauss(0.0, 0.15)
        noise_y = random.gauss(0.0, 0.15)
        noise_z = random.gauss(9.80, 0.20)

        # Select synthetic vehicular motion scenario
        scenario = random.choices(
            population=["CRUISE", "MINOR_TURN", "ROAD_BUMP", "BRAKING"],
            weights=[0.70, 0.15, 0.10, 0.05],
            k=1,
        )[0]

        if scenario == "CRUISE":
            x = noise_x
            y = noise_y
            z = noise_z
        elif scenario == "MINOR_TURN":
            # Lateral acceleration during a moderate turn
            x = noise_x
            y = random.uniform(1.2, 2.8) * random.choice([-1, 1]) + noise_y
            z = noise_z
        elif scenario == "ROAD_BUMP":
            # Brief vertical bump (does not breach severe accident threshold)
            x = noise_x
            y = noise_y
            z = random.uniform(12.0, 16.5)
        elif scenario == "BRAKING":
            # Longitudinal deceleration during braking
            x = random.uniform(-3.5, -1.8) + noise_x
            y = noise_y
            z = noise_z
        else:
            x, y, z = noise_x, noise_y, noise_z

        return {
            "x": round(x, 2),
            "y": round(y, 2),
            "z": round(z, 2),
            "motion_type": scenario,
        }
