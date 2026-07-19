import numpy as np
import json


#1. load the pipeline architecture

# with open ("network_config.json", "r") as file:
#     network_data = json.load(file)
with open("nord_stream_config.json", "r") as file:
    network_data = json.load(file)
    
#calculate pipe friction resistance(R)
def calculate_hydraulic_resistance(length, diameter, friction_factor, density=1000):
    #the formular is R = (8 * f * L * rho) / (pi^2 * D^5)
    return (8.0 * friction_factor * length * density) / ((np.pi**2) * (diameter**5))

def steady_solver_state(network):
    #extract boundary conditions from the boundary conditions
    p0 = network["nodes"][0]["boundary_pressure_bar"] * 1e5  # Convert bar to Pascals
    p2 = network["nodes"][2]["boundary_pressure_bar"] * 1e5  # Convert bar to Pascals

    #extract pipe propoerties
    pipe_a = network["edges"][0]
    pipe_b = network["edges"][1]

    #calculate hydraulic resistance for each pipe
    r_a = calculate_hydraulic_resistance(
    length=pipe_a["length_m"],          
    diameter=pipe_a["diameter_m"],      
    friction_factor=pipe_a["friction_factor"]
    )   

    r_b = calculate_hydraulic_resistance(
    length=pipe_b["length_m"],          
    diameter=pipe_b["diameter_m"],     
    friction_factor=pipe_b["friction_factor"]
    )

    #2. Newton-Rapson solver

    p1_guess = 85.0 * 1e5  # inital guess for node 1 (converted to Pascals)
    tolerance = 1e-6
    max_iteration = 50  
    epsilon = 1e-8      #tiny number to be added to flowrate incase its 0 so as not to break it

    print(f"Starting Newton-Raphson Solver for Node_1...")
    print(f"{'Iteration':<10} | {'P1 Guess (bar)':<15} | {'Mass Error F(P) [kg/s]':<25} | {'Jacobian (Slope)'}")
    print("-" * 75)


    for iteration in range(max_iteration):
        #3 calculate flow Q using Darcy-Weisbach methond: Q = sgn(change in p) * sqrt(|change in p| / R)
        dp_a = (p0 - p1_guess) 
        q_a = np.sign(dp_a) * np.sqrt(abs(dp_a) / r_a)

        dp_b = (p1_guess - p2) 
        q_b = np.sign(dp_b) * np.sqrt(abs(dp_b) / r_b)

        #4. using conservation of mass, calculate the residual F(P1) = Q_in - Q_out
        #residual = q_a - q_b
        leak_rate = 0.02  # Simulating a 0.02 kg/s rupture at node_1
        residual = q_a - q_b - leak_rate


        # to check if we have hit equilibrium
        if abs(residual) < tolerance:
            final_pressure = p1_guess / 1e5  # Convert back to bar for output

            print("-" * 75)
            print(f"✓ Equilibrium Achieved in {iteration} iterations!")
            print(f"► Final Pressure at node_1: {final_pressure:.6f} bar")
            print(f"► Steady-State Flow Rate:   {q_a:.6f} kg/s")
            return final_pressure
        
        #To calculate the Analytical jacobian(J)
        dq_a_dp1 = -1.0 /(2.0 * r_a * (abs(q_a + epsilon)))
        dq_b_dp1 = 1.0 /(2.0 * r_b * (abs(q_b + epsilon)))

        jacobian = dq_a_dp1 - dq_b_dp1
        print(f"{iteration:<10} | {p1_guess:<15.6f} | {residual:<25.6f} | {jacobian:.6f}")

        #6. to adjust the the value of the p1_guess
        delta_p1 = -residual / jacobian
        p1_guess += delta_p1

    raise RuntimeError("Solver iverged or failed o hit tolerance")

final_pressure = steady_solver_state(network_data)    