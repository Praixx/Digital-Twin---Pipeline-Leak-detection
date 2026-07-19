import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Load the environment variables from the .env file
current_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(current_dir, '.env')
load_dotenv(env_path)

# pull the supabasekeys
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Supabase credentials not found. Please set SUPABASE_URL and SUPABASE_KEY in your environment variables or .env file.")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def clear_simulation_logs():
    """Wipes data and resets the ID counter to 1."""
    return supabase.table("simulation_logs").delete().neq("id", 0).execute()

def upload_simulation_log(timestamp, pressure_data, flow_data):
    # Ensure pressure and flow are converted to standard lists for JSON compatibility
    data = {
        "timestamp": float(timestamp),
        "pressure": pressure_data.tolist() if hasattr(pressure_data, 'tolist') else pressure_data,
        "flow": flow_data.tolist() if hasattr(flow_data, 'tolist') else flow_data
    }
    return supabase.table("simulation_logs").insert(data).execute()




