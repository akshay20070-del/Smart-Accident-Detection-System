"""
Script to generate high-resolution Block Diagram and Circuit Diagram PNGs
for the Smart Accident Detection and Emergency Alert System.
"""

import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# Ensure target directory exists
DIAGRAMS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "hardware", "diagrams"))
os.makedirs(DIAGRAMS_DIR, exist_ok=True)

def generate_block_diagram():
    fig, ax = plt.subplots(figsize=(14, 8), dpi=300)
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 9)
    ax.axis("off")

    # Title
    ax.text(7, 8.5, "SMART ACCIDENT DETECTION & EMERGENCY ALERT SYSTEM", 
            ha="center", va="center", fontsize=15, fontweight="bold", color="#1E3A8A")
    ax.text(7, 8.1, "SYSTEM ARCHITECTURE & HARDWARE BLOCK DIAGRAM", 
            ha="center", va="center", fontsize=11, fontweight="semibold", color="#4B5563")

    # Helper function to draw rounded boxes
    def draw_box(x, y, w, h, title, subtitle, color, text_color="black"):
        rect = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.15", 
                                      ec="#334155", fc=color, lw=2, zorder=2)
        ax.add_patch(rect)
        ax.text(x + w/2, y + h*0.65, title, ha="center", va="center", 
                fontsize=11, fontweight="bold", color=text_color, zorder=3)
        ax.text(x + w/2, y + h*0.35, subtitle, ha="center", va="center", 
                fontsize=8.5, color=text_color, zorder=3)

    # 1. Central MCU Block
    mcu = patches.FancyBboxPatch((5.0, 2.8), 4.0, 4.2, boxstyle="round,pad=0.2", 
                                ec="#1E3A8A", fc="#EFF6FF", lw=2.5, zorder=2)
    ax.add_patch(mcu)
    ax.text(7.0, 6.5, "CENTRAL PROCESSING UNIT", ha="center", va="center", fontsize=12, fontweight="bold", color="#1E3A8A")
    ax.text(7.0, 6.1, "ESP32 Dev Module (Xtensa 32-bit)", ha="center", va="center", fontsize=9.5, fontweight="semibold", color="#1F2937")

    inner_tasks = [
        "• Vector Magnitude: A = sqrt(x² + y² + z²)",
        "• Consecutive Spike Filter (Noise Rejection)",
        "• Threshold State Machine (Normal/Warning/Alert)",
        "• GPS NMEA 0183 Telemetry Parser",
        "• USB Serial JSON Line Encoder @ 115200 Baud"
    ]
    for i, task in enumerate(inner_tasks):
        ax.text(5.2, 5.5 - i*0.5, task, fontsize=8.5, color="#374151")

    # 2. Input Sensors (Left)
    draw_box(0.5, 5.2, 3.2, 1.4, "MPU6050 IMU SENSOR", "3-Axis Accel + Gyro (I2C Bus)\nSDA: GPIO21 | SCL: GPIO22", "#E0F2FE")
    draw_box(0.5, 3.0, 3.2, 1.4, "NEO-6M GPS MODULE", "Satellite Trilateration\nUART2: TX->GPIO16, RX->GPIO17", "#DCFCE7")
    draw_box(0.5, 0.8, 3.2, 1.4, "MANUAL CANCEL BUTTON", "Driver Alert Cancellation\nActive LOW (GPIO 15 Pull-up)", "#FEF3C7")

    # 3. Power Supply (Top)
    draw_box(5.0, 7.3, 4.0, 0.9, "POWER SUPPLY UNIT", "USB 5V / 18650 Li-ion -> LM2596 Buck (4.0V)", "#FEE2E2")

    # 4. Outputs & Interfaces (Right)
    draw_box(10.3, 5.2, 3.2, 1.4, "PC DASHBOARD / SOFTWARE", "Streamlit Real-Time Monitor\nUSB Serial Interface (COM Port)", "#E0E7FF")
    draw_box(10.3, 3.0, 3.2, 1.4, "ALERT PERIPHERALS", "Active Buzzer (GPIO 4)\nStatus LED (GPIO 2)", "#FCE7F3")
    draw_box(10.3, 0.8, 3.2, 1.4, "SIM800L GSM (OPTIONAL)", "Automated SMS Dispatch\nUART1 (GPIO 26/27) | Ext 4V", "#F3F4F6")

    # Connectors / Arrows
    arrow_props = dict(arrowstyle="->", lw=2, color="#475569")
    
    # Inputs to MCU
    ax.annotate("", xy=(5.0, 5.9), xytext=(3.7, 5.9), arrowprops=arrow_props)
    ax.text(4.35, 6.1, "I2C Bus", ha="center", fontsize=8, color="#2563EB", fontweight="bold")
    
    ax.annotate("", xy=(5.0, 3.7), xytext=(3.7, 3.7), arrowprops=arrow_props)
    ax.text(4.35, 3.9, "UART2", ha="center", fontsize=8, color="#16A34A", fontweight="bold")

    ax.annotate("", xy=(5.0, 1.5), xytext=(3.7, 1.5), arrowprops=arrow_props)
    ax.text(4.35, 1.7, "GPIO15", ha="center", fontsize=8, color="#D97706", fontweight="bold")

    # Power to MCU
    ax.annotate("", xy=(7.0, 7.0), xytext=(7.0, 7.3), arrowprops=arrow_props)

    # MCU to Outputs
    ax.annotate("", xy=(10.3, 5.9), xytext=(9.0, 5.9), arrowprops=dict(arrowstyle="<->", lw=2, color="#475569"))
    ax.text(9.65, 6.1, "USB CDC", ha="center", fontsize=8, color="#4F46E5", fontweight="bold")

    ax.annotate("", xy=(10.3, 3.7), xytext=(9.0, 3.7), arrowprops=arrow_props)
    ax.text(9.65, 3.9, "Digital Out", ha="center", fontsize=8, color="#DB2777", fontweight="bold")

    ax.annotate("", xy=(10.3, 1.5), xytext=(9.0, 1.5), arrowprops=arrow_props)
    ax.text(9.65, 1.7, "AT UART", ha="center", fontsize=8, color="#64748B", fontweight="bold")

    plt.tight_layout()
    block_path = os.path.join(DIAGRAMS_DIR, "block_diagram.png")
    plt.savefig(block_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Generated Block Diagram at: {block_path}")

def generate_circuit_diagram():
    fig, ax = plt.subplots(figsize=(14, 8), dpi=300)
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 9)
    ax.axis("off")

    ax.text(7, 8.5, "SMART ACCIDENT DETECTION SYSTEM - SCHEMATIC WIRING DIAGRAM", 
            ha="center", va="center", fontsize=14, fontweight="bold", color="#0F172A")

    # Central ESP32 Pinout box
    esp = patches.Rectangle((4.5, 1.2), 5.0, 6.5, ec="#1E3A8A", fc="#F8FAFC", lw=2.5)
    ax.add_patch(esp)
    ax.text(7.0, 7.3, "ESP32 DEVELOPMENT BOARD", ha="center", va="center", fontsize=12, fontweight="bold", color="#1E3A8A")
    ax.text(7.0, 6.9, "(ESP32-WROOM-32 / NodeMCU-32S)", ha="center", va="center", fontsize=9, color="#64748B")

    # Left & Right pins on ESP32
    left_pins = ["3V3", "GND", "GPIO 21 (SDA)", "GPIO 22 (SCL)", "GPIO 16 (RX2)", "GPIO 17 (TX2)", "GPIO 15 (BTN)"]
    for i, p in enumerate(left_pins):
        y_pos = 6.2 - i * 0.75
        ax.plot([4.2, 4.5], [y_pos, y_pos], color="#334155", lw=2)
        ax.text(4.6, y_pos, p, va="center", fontsize=8.5, fontweight="bold", color="#1E293B")

    right_pins = ["VIN / 5V", "GND", "GPIO 4 (BUZ)", "GPIO 2 (LED)", "GPIO 26 (RX1)*", "GPIO 27 (TX1)*", "EN / RESET"]
    for i, p in enumerate(right_pins):
        y_pos = 6.2 - i * 0.75
        ax.plot([9.5, 9.8], [y_pos, y_pos], color="#334155", lw=2)
        ax.text(9.4, y_pos, p, ha="right", va="center", fontsize=8.5, fontweight="bold", color="#1E293B")

    # Helper for peripheral boxes
    def draw_peri(x, y, w, h, name, pins, col):
        rect = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.1", ec="#475569", fc=col, lw=2)
        ax.add_patch(rect)
        ax.text(x + w/2, y + h - 0.25, name, ha="center", fontsize=10, fontweight="bold")
        for idx, (p_name, p_conn) in enumerate(pins):
            p_y = y + h - 0.65 - idx*0.35
            ax.text(x + 0.15, p_y, f"{p_name}: {p_conn}", fontsize=7.5, color="#1F2937")

    # 1. MPU6050
    draw_peri(0.5, 5.0, 3.2, 2.2, "MPU6050 SENSOR", [
        ("VCC", "-> ESP32 3V3"),
        ("GND", "-> ESP32 GND"),
        ("SCL", "-> ESP32 GPIO 22"),
        ("SDA", "-> ESP32 GPIO 21"),
        ("AD0", "-> GND (Addr 0x68)")
    ], "#E0F2FE")

    # 2. NEO-6M GPS
    draw_peri(0.5, 2.2, 3.2, 2.0, "NEO-6M GPS MODULE", [
        ("VCC", "-> ESP32 3V3"),
        ("GND", "-> ESP32 GND"),
        ("TXD", "-> ESP32 GPIO 16 (RX2)"),
        ("RXD", "-> ESP32 GPIO 17 (TX2)")
    ], "#DCFCE7")

    # 3. Cancel Button & Buzzer (Right)
    draw_peri(10.3, 5.0, 3.2, 2.0, "AUDIO & BUTTON I/O", [
        ("Buzzer (+)", "-> GPIO 4"),
        ("Buzzer (-)", "-> GND"),
        ("Btn Pin 1", "-> GPIO 15 (Pullup)"),
        ("Btn Pin 2", "-> GND")
    ], "#FEF3C7")

    # 4. Optional SIM800L
    draw_peri(10.3, 1.8, 3.2, 2.4, "SIM800L GSM (OPTIONAL)", [
        ("VCC", "-> 4.0V EXTERNAL ONLY"),
        ("GND", "-> COMMON SYSTEM GND"),
        ("TXD", "-> ESP32 GPIO 26"),
        ("RXD", "-> ESP32 GPIO 27"),
        ("NOTE", "Requires 2A Buck/18650")
    ], "#FEE2E2")

    # Note footer
    ax.text(7.0, 0.5, "Notice: All ground references (GND) must be tied together. Do NOT power SIM800L from ESP32 pins.",
            ha="center", fontsize=9, fontstyle="italic", color="#DC2626")

    plt.tight_layout()
    circuit_path = os.path.join(DIAGRAMS_DIR, "circuit_diagram.png")
    plt.savefig(circuit_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Generated Circuit Diagram at: {circuit_path}")

if __name__ == "__main__":
    generate_block_diagram()
    generate_circuit_diagram()
