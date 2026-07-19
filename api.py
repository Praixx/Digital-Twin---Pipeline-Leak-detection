from flask import Flask, request, jsonify
from flask_cors import CORS
import traceback
from leak_detection_engine import analyze_pipeline_rupture

app = Flask(__name__)
CORS(app)

@app.route('/simulate', methods=['POST'])
def simulate():
    try:
        data = request.json
        target_km = float(data['targetNode'])
        severity = float(data['severity'])
        
        # Convert km to node index accurately using round() and open up to Node 99
        target_idx = max(1, min(99, round(target_km / 12.2222)))
        
        print(f"\n🚀 [API] Executing Strike at Node {target_idx} ({target_km} km) at {severity} kg/s")
        
        # CRITICAL FIX: Pass all THREE arguments here!
        results = analyze_pipeline_rupture(target_idx, severity, target_km)
        return jsonify(results)
        
    except Exception as e:
        print(f"\n❌ [CRASH DETECTED]: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(port=5001, debug=True)