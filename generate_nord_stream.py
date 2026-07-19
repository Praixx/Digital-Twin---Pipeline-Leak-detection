import json

def generate_nord_stream_macro_data(filename="nord_stream_config.json"):
    total_length = 1222     #total length of nord stream in km
    segment_length_m = 1000
    diameter_m = 1.153
    friction_factor = 0.012

    nodes = []
    edges = []

    print(f"Generating {total_length} nodes and edges for the Nord Stream macro-grid...")

    for i in range(total_length + 1):
        #1. define the supply node (vyborg, russia)
        if i == 0:
            nodes.append({
                "id": f"NS_Node_{i}",
                "type": "supply",
                "x_cord": i * segment_length_m,
                "boundary_pressure_bar": 220
            })
        elif i == total_length:
            nodes.append({
                "id": f"NS_Node_{i}",
                "type": "delivery",
                "x_cord": i * segment_length_m,
                "boundary_pressure_bar": 110
            })
        else:
            nodes.append({
                "id": f"NS_Node_{i}",
                "type": "junction",
                "x_cord": i * segment_length_m,
                "boundary_pressure_bar": None
            })
        if i < total_length:
            edges.append({
                "id": f"NS_Seg_{i}",
                "source": f"NS_Node_{i}",
                "target": f"NS_Node_{i+1}",
                "length_m": segment_length_m,
                "diameter_m": diameter_m,
                "friction_factor": friction_factor
            })
    # Package into our generic schema format
    macro_grid = {
        "network_id": "nord_stream_macro_1222km",
        "nodes": nodes,
        "edges": edges
    }

    # Export the massive JSON file
    with open(filename, "w") as f:
        json.dump(macro_grid, f, indent=2)
        
    print(f"✓ Success: {filename} generated. It contains {len(nodes)} nodes and {len(edges)} pipes.")

if __name__ == "__main__":
    generate_nord_stream_macro_data()