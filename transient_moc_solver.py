import numpy as np
import json
from db_client import upload_simulation_log, clear_simulation_logs

def execute_attacker_function(leak_array, target_node, severity_kg_s, current_time, activation_time=50.0):
    if current_time >= activation_time:
        leak_array[target_node] = severity_kg_s
    return leak_array

def run_transient_simulation(target_node_idx, leak_severity):
    try:
        clear_simulation_logs()
    except Exception as e:
        print("!!! Could not clear Supabase. Running locally...")

    with open("nord_stream_config.json", "r") as file:
        network = json.load(file)

    nodes, edges = network["nodes"], network["edges"]
    Nx = len(nodes)
    dx = edges[0]["length_m"]
    L = dx * (Nx - 1)
    c, rho, D = 340.0, 1000.0, edges[0]["diameter_m"]
    A = np.pi * (D**2) / 4.0
    f = edges[0]["friction_factor"]

    dt = dx / c
    Nt = int(1800.0 / dt) + 1

    P = np.zeros((Nt, Nx))
    M = np.zeros((Nt, Nx))

    P_start = nodes[0]["boundary_pressure_bar"] * 1e5
    P_end = nodes[-1]["boundary_pressure_bar"] * 1e5

    for i in range(Nx):
        P[0, i] = P_start - (i / (Nx - 1)) * (P_start - P_end)

    R_total = (8.0 * f * L * rho) / ((np.pi**2) * (D**5))
    M[0, :] = np.sqrt((P_start - P_end) / R_total)

    Z = c / A
    R_coef = (8.0 * f * dx * rho) / ((np.pi**2) * (D**5))

    for t in range(0, Nt - 1):
        current_time = (t + 1) * dt
        leak_array = execute_attacker_function(np.zeros(Nx), target_node_idx, leak_severity, current_time)
        
        for x in range(1, Nx - 1):
            C_plus = P[t, x-1] + M[t, x-1] * Z
            C_minus = P[t, x+1] - M[t, x+1] * Z
            implicit_friction = R_coef * (abs(M[t, x-1]) + abs(M[t, x+1])) / 2.0
            
            P[t+1, x] = ((C_plus + C_minus) / 2.0) - (leak_array[x] * Z / 2.0)
            M[t+1, x] = ((C_plus - C_minus) / (2.0 * (Z + implicit_friction))) - (leak_array[x] / 2.0)

        P[t+1, 0] = P_start
        M[t+1, 0] = (P_start - (P[t, 1] - M[t, 1] * Z)) / (Z + R_coef * abs(M[t, 1]))
        P[t+1, -1] = P_end
        M[t+1, -1] = ((P[t, -2] + M[t, -2] * Z) - P_end) / (Z + R_coef * abs(M[t, -2]))

        if t % 60 == 0:
            try:
                upload_simulation_log(current_time, P[t+1, :], M[t+1, :])
            except:
                pass
    
    #  Return target_node_idx instead of random_target_node
    return P / 1e5, dt, Nt, Nx, target_node_idx
    