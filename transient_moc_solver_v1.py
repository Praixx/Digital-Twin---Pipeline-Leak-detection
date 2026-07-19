import numpy as np


def execute_attacker_function(leak_array, target_node, severity_kg_s, current_time, activation_time=10.0):
    """
    Simulates a cyber-physical attack or catastrophic structural failure.
    Targets a specific segment and dynamically drops its mass.
    """
    if current_time >= activation_time:
        leak_array[target_node] = severity_kg_s
    return leak_array


def run_transient_simulation():
    # 1. Physical & Spatial Constraints
    L = 100000          # length of the pipeline
    Nx = 100            # total number of nodes
    dx = L / Nx         # distance between nodes s
    
    c = 340.0           # speed of sound in fluid (m/s)
    rho = 1000.0        # fluid density (kg/m3)
    D = 1.153           # internal diameter (m)
    A = np.pi * (D**2) / 4.0  #internal area of a pipe
    f = 0.012           # friction factor
    
    # 2. CFL Condition
    dt = dx / c         
    t_total = 60.0      
    Nt = int(t_total / dt) + 1  #total loop count
    
    # 3. Initialize Space-Time Arrays
    P = np.zeros((Nt, Nx))  #pressure arrray
    M = np.zeros((Nt, Nx))  #mass flow array
    
    # 4. Inject Phase 2 Steady-State Baseline
    P_start = 220.0 * 1e5  
    P_end = 100.0 * 1e5    
    
    for i in range(Nx):
        x_ratio = i / (Nx - 1)
        P[0, i] = P_start - x_ratio * (P_start - P_end)
    
    
    R_total = (8.0 * f * L * rho) / ((np.pi**2) * (D**5))
    Q_steady = np.sqrt((P_start - P_end) / R_total)
    M[0, :] = Q_steady

    Z = c / A   #impendence
    R_coef = (8.0 * f * dx * rho) / ((np.pi**2) * (D**5))

    print(f"MOC Engine Simulating {L/1000:.0f}km pipeline.")
    print(f"Time Step (dt): {dt:.4f} seconds | Total Time Steps: {Nt}")
    print("-" * 65)

    # 5. The Transient Time Loop (IMPLICIT FRICTION)
    for t in range(0, Nt - 1):
        
        # Step 11: Deploy the Attacker Function
        leak_array = np.zeros(Nx)
        leak_array = execute_attacker_function(
            leak_array=leak_array, 
            target_node=50, 
            severity_kg_s=150.0, 
            current_time=t * dt, 
            activation_time=10.0
        )
            
        # Interior Nodes Sweep
        for x in range(1, Nx - 1):
            # to calculate characteristic lines 
            C_plus = P[t, x-1] + M[t, x-1] * Z
            C_minus = P[t, x+1] - M[t, x+1] * Z
            
            #  Implicit Friction Dampener (Averaged from adjacent nodes)
            implicit_friction = R_coef * (abs(M[t, x-1]) + abs(M[t, x+1])) / 2.0
            
            # Solve for new state 
            P[t+1, x] = ((C_plus + C_minus) / 2.0) - (leak_array[x] * Z / 2.0)
            M[t+1, x] = ((C_plus - C_minus) / (2.0 * (Z + implicit_friction))) - (leak_array[x] / 2.0)

        # Left Boundary (Inlet Supply Station)
        P[t+1, 0] = P_start
        C_minus_boundary = P[t, 1] - M[t, 1] * Z
        implicit_fric_0 = R_coef * abs(M[t, 1])
        M[t+1, 0] = (P_start - C_minus_boundary) / (Z + implicit_fric_0)
        
        # Right Boundary (Outlet Delivery Station)
        P[t+1, -1] = P_end
        C_plus_boundary = P[t, -2] + M[t, -2] * Z
        implicit_fric_end = R_coef * abs(M[t, -2])
        M[t+1, -1] = (C_plus_boundary - P_end) / (Z + implicit_fric_end)

        # Log updates
        
        current_time = (t + 1) * dt
        
        # System state flags based on the 10-second rupture strike marker
        status = "NOMINAL" if current_time <= 10.0 else "RUPTURE!!!"
        
        # This will now print on every loop iteration automatically
        print(f"[{status}] Time: {current_time:>5.2f}s | Midpoint P: {P[t+1, 50]/1e5:>6.2f} bar | Midpoint Flow: {M[t+1, 50]:>7.2f} kg/s")

    print("-" * 65)
    print("✓ Transient Simulation Complete.")
    return P / 1e5, M, dt

if __name__ == "__main__":
    P_matrix, M_matrix, timestep = run_transient_simulation()