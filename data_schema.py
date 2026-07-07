import json


#load pipe network data
with open("network_config.json", "r") as file:
    pipe_network_data = file.read()

def parse_pipeline_graph(json_str):
    data = json.loads(json_str)

    #extract structural set
    nodes = { n["id"] : n for n in data["nodes"]}    #extract the node data from the json
    edges = data["edges"]   

    print(f"Parsing Network: {data['network_id']}")
    print("node vertices")

    unknown_nodes = []
    fixed_nodes = []

    # search through the nodes and those with no bounday_pressure_bar is added to unknown_nodes and vice versa
    for node_id, node in nodes.items():
        if node["boundary_pressure_bar"] is None:
            unknown_nodes.append(node_id)
            print(f"{node_id} [{node['type'].upper()}] Pressure is unknown(solve via Newton-Raphson)  ")
        else:
            fixed_nodes.append(node_id)
            print(f"{node_id} [{node['type'].upper()}]: Fixed Boundary Pressure = {node['boundary_pressure_bar']} bar")

    
    for edge in edges:
        src, tgt = edge["source"], edge["target"]
        if src not in nodes or tgt not in nodes:
            raise ValueError(f"Topological Error: Edge{edge['id']} doesnt connect to any node ")
        
        print(f"• {edge['id']}: Elements flow from {src} (x={nodes[src]['x_cord']}m) → {tgt} (x={nodes[tgt]['x_cord']}m)")
    
    return{
        "network_id": data["network_id"],
        "nodes": nodes,
        "edges": edges,
        "Unknown_pressure": unknown_nodes,
        "Fixed_pressure": fixed_nodes
    }
     
network = parse_pipeline_graph(pipe_network_data)