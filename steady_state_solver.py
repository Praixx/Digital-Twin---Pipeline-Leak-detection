import numpy as np
import json

#load the pipeline architecture
with open("nord_stream_config.json", "r") as file:
    network_data = json.load(file)

def calculate_hydraulic_resistance(length, diameter, friction_factor, density=1000):
    """Calculates fixed structural resistance 'R'."""
    return (8.0 * friction_factor * length * density) / ((np.pi**2) * (diameter**5))

def steady_solver_state(network):

    nodes = network["nodes"]
    edges = network["edges"]

    # 1. Map dynamic topology
    node_idx = {n["id"]: i for i, n in enumerate(nodes)}
    n_nodes = len(nodes)
    
    # Isolate unknown variables (Junctions) every node except 0 and  1222
    junction_indices = [i for i, n in enumerate(nodes) if n["type"].lower() == "junction"]
    n_junctions = len(junction_indices)
    
    # # 2. Initialize global pressure array (Pascals)
    # P = np.zeros(n_nodes)
    # for i, n in enumerate(nodes):
    #     if n["type"].lower() in ["supply", "delivery"]:
    #         P[i] = n["boundary_pressure_bar"] * 1e5
    #     else:
    #         P[i] = 85.0 * 1e5 # Global starting guess

    # 2. Initialize global pressure array (Pascals) with a Linear Profile
    P = np.zeros(n_nodes)
    
    # Extract boundary positions and values
    x_start = nodes[0]["x_cord"]
    x_end = nodes[-1]["x_cord"]
    p_start_pa = nodes[0]["boundary_pressure_bar"] * 1e5
    p_end_pa = nodes[-1]["boundary_pressure_bar"] * 1e5

    for i, n in enumerate(nodes):
        if n["type"].lower() in ["supply", "delivery"]:
            P[i] = n["boundary_pressure_bar"] * 1e5
        else:
            # calculate the linear pressure drop based on distance
            x_ratio = (n["x_cord"] - x_start) / (x_end - x_start)
            P[i] = p_start_pa - x_ratio * (p_start_pa - p_end_pa)

    # 3. Vectorize structural constants (R) and edge mappings
    R = np.array([calculate_hydraulic_resistance(e["length_m"], e["diameter_m"], e["friction_factor"]) for e in edges])
    src_idx = np.array([node_idx[e["source"]] for e in edges])
    tgt_idx = np.array([node_idx[e["target"]] for e in edges])

    #2. Newton-Rapson solver
    tolerance = 1e-6
    epsilon = 1e-8
    max_iteration = 50

    print(f"Initializing {n_junctions}x{n_junctions} Jacobian Matrix...")
    print(f"Starting Newton-Raphson Solver")
    print(f"{'Iteration':<10} | {'P Guess (bar)(leak A)':<15} | {'Mass Error F(P)(leak A) [kg/s]':<25} | {'Jacobian (Slope)'}")
    print("-" * 75)

    for iteration in range(max_iteration):
        # 4. Vectorized Flow Calculation
        # calculate flow Q using Darcy-Weisbach methond: Q = sgn(change in p) * sqrt(|change in p| / R)

        dP = P[src_idx] - P[tgt_idx]
        Q = np.sign(dP) * np.sqrt(np.abs(dP) / R)
        
        # 5. Evaluate Mass Residuals
        residuals = np.zeros(n_nodes)
        np.add.at(residuals, tgt_idx, Q)  
        np.add.at(residuals, src_idx, -Q) 
        
        # Simulating MULTIPLE LEAK INJECTION 
        # Simulating a 0.2 kg/s leak at km 300, and a 0.4 kg/s leak at km 900
        leak_node_A = 300
        leak_node_B = 900
        residuals[leak_node_A] -= 0.2
        residuals[leak_node_B] -= 0.4
        
        F = residuals[junction_indices] 
        
        # to check if we have hit equilibrium
        max_error = np.max(np.abs(F))
        if max_error < tolerance:
            print("-" * 75)
            print(f" Equilibrium Achieved in {iteration} iterations!")
            print(f" Max System Mass Error: {max_error:.8f} kg/s")
            print(f" Total Steady-State Output Flow: {Q[-1]:.6f} kg/s")
            return P / 1e5 

        # 6. Build the N x N Analytical Jacobian
        J = np.zeros((n_junctions, n_junctions))
        dQ_ddP = 1.0 / (2.0 * R * (np.abs(Q) + epsilon))
        junc_map = {idx: j for j, idx in enumerate(junction_indices)}
        
        for e in range(len(edges)):
            s = src_idx[e]
            t = tgt_idx[e]
            dq = dQ_ddP[e]
            
            if s in junc_map:
                J[junc_map[s], junc_map[s]] += -dq
                if t in junc_map:
                    J[junc_map[s], junc_map[t]] += dq
            if t in junc_map:
                J[junc_map[t], junc_map[t]] += -dq
                if s in junc_map:
                    J[junc_map[t], junc_map[s]] += dq
                    
        
        # Track the specific metrics for Node 300 to match the Phase 1 UI
        track_junc_idx = junc_map[leak_node_A]
        track_p_bar = P[leak_node_A] / 1e5
        track_error = F[track_junc_idx]
        track_jacobian = J[track_junc_idx, track_junc_idx]
        
        print(f"{iteration:<10} | {track_p_bar:<15.6f} | {track_error:<25.6f} | {track_jacobian:.6f}")
        
        # 7. Linear Algebra execution 
        delta_P_junc = -np.linalg.solve(J, F)
        
        # Update matrix
        for j, idx in enumerate(junction_indices):
            P[idx] += delta_P_junc[j]

    raise RuntimeError("Matrix Diverged: Failed to hit tolerance.")

# Execute the engine 
solved_pressures_bar = steady_solver_state(network_data)


print("\n" + "-"*75)
print("  MACRO-GRID TELEMETRY EXTRACT | 5 Key Nodes")
print("-"*75)
print(f"Node 0    (Supply)      : {solved_pressures_bar[0]:.2f} bar (Fixed Boundary)")
print(f"Node 300  (Leak Anomaly A)  : {solved_pressures_bar[300]:.2f} bar")
print(f"Node 611  (Pipeline Center) : {solved_pressures_bar[611]:.2f} bar")
print(f"Node 900  (Leak Anomaly B)  : {solved_pressures_bar[900]:.2f} bar")
print(f"Node 1221 (Delivery)  : {solved_pressures_bar[-1]:.2f} bar (Fixed Boundary)")
print("-"*75)