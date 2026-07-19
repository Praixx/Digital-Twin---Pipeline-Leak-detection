import numpy as np
from scada_sensor_stream import generate_scada_telementry

def compute_delta_p(scada_data, sensor_key):
    signal = scada_data[sensor_key]
    return np.mean(signal[:15]) - np.mean(signal[-300:])

def fit_quadratic_wave_tip(positions, deltas):
    pos = np.array(positions)
    y = np.array(deltas)
    peak_idx = np.argmax(y)

    if peak_idx == 0: idxs = [0, 1, 2]
    elif peak_idx == len(pos) - 1: idxs = [-3, -2, -1]
    else: idxs = [peak_idx - 1, peak_idx, peak_idx + 1]

    x_3, y_3 = pos[idxs], y[idxs]
    coeffs = np.polyfit(x_3, y_3, 2)
    a, b, c = coeffs

    calc_km = -b / (2 * a) if a < -1e-7 else pos[peak_idx]
    calc_km = max(0.0, min(1222.0, calc_km))
    return calc_km, x_3, y_3, coeffs

def analyze_pipeline_rupture(target_node_idx, leak_severity, exact_target_km):
    scada_data, ACTUAL_RUPTURE_NODE = generate_scada_telementry(target_node_idx, leak_severity)
    
    
    ACTUAL_RUPTURE_KM = exact_target_km

    sensor_positions = [100, 200, 300, 400, 500, 700, 800, 900, 1000, 1100]
    # ... rest of the code remains exactly the same
    delta_pressures = [compute_delta_p(scada_data, f"sensor_{pos}") for pos in sensor_positions]

    calc_km, x_3, y_3, coeffs = fit_quadratic_wave_tip(sensor_positions, delta_pressures)
    max_drop = np.polyval(coeffs, calc_km)
    error_distance = abs(calc_km - ACTUAL_RUPTURE_KM)

    curve_x = np.linspace(min(sensor_positions), max(sensor_positions), 200)
    curve_y = np.polyval(coeffs, curve_x)
    valid_idx = curve_y > -0.05

    print(f" Triangulated Leak at {calc_km:.2f} km")
    
    
    dynamic_inlet = 220.00
    dynamic_delivery = 100.00 - compute_delta_p(scada_data, "sensor_1100")
    
    return {
        "telemetry": {
            "actual_km": round(ACTUAL_RUPTURE_KM, 2),
            "calc_km": round(calc_km, 2),
            "error_margin": round(error_distance, 4),
            "max_drop": round(max_drop, 3),
            "inlet_supply": round(dynamic_inlet, 2),        
            "delivery_station": round(dynamic_delivery, 2), 
            "status": "SECURE" if error_distance < 20.0 else "ANOMALY"
        },
        "plot_data": {
            "scada_x": sensor_positions,
            "scada_y": delta_pressures,
            "wave_x": x_3.tolist(),
            "wave_y": y_3.tolist(),
            "curve_x": curve_x[valid_idx].tolist(),
            "curve_y": curve_y[valid_idx].tolist()
        }
    }