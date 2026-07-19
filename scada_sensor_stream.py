import numpy as np
from transient_moc_solver import run_transient_simulation

def generate_scada_telementry(target_node_idx, leak_severity):
    print("📡 [SCADA] Booting MOC engine...")
    P_matrix, dt, Nt, Nx, target_node = run_transient_simulation(target_node_idx, leak_severity)

    sensor_locations = [100, 200, 300, 400, 500, 700, 800, 900, 1000, 1100]
    scada_database = {} 
    
    time_array = np.array([t * dt for t in range(Nt)])
    scada_database["timestamps"] = time_array

    noise_std_dev = 1
    for loc in sensor_locations:
        # Convert the physical km (100-1100) into a valid array index (0-99)
        node_idx = min(Nx - 1, int(loc / 12.22))
        
        prefect_pressure = P_matrix[:, node_idx]
        sensor_noises = np.random.normal(0, noise_std_dev, Nt)
        scada_database[f"sensor_{loc}"] = prefect_pressure + sensor_noises
    
    print("✓ [SCADA] Telemetry Extraction Complete.")
    return scada_database, target_node