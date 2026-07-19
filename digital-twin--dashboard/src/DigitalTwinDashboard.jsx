import { useState } from "react";
import Plot from "react-plotly.js";
import {
  Activity,
  AlertTriangle,
  ShieldCheck,
  Zap,
  RefreshCw,
} from "lucide-react";

const DigitalTwinDashboard = () => {
  const [targetNode, setTargetNode] = useState(611);
  const [severity, setSeverity] = useState(3700);
  const [systemStatus, setSystemStatus] = useState("NOMINAL");
  const [isSimulating, setIsSimulating] = useState(false);

  // HUD Data Management - Initialized to hyphens!
  const [telemetry, setTelemetry] = useState({
    calc_km: "-",
    actual_km: "-",
    error_margin: "-",
    inlet_supply: "-",
    delivery_station: "-",
  });

  const [plotTraces, setPlotTraces] = useState([]);
  const [scadaTable, setScadaTable] = useState([]);

  const executeSimulation = async () => {
    setIsSimulating(true);
    setSystemStatus("CALCULATING...");

    try {
      const response = await fetch("http://localhost:5001/simulate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          targetNode: parseFloat(targetNode),
          severity: parseFloat(severity),
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        console.error("Backend Error:", data.error);
        setSystemStatus("ERROR");
        setIsSimulating(false);
        return;
      }

      // Update state dynamically from the Python backend payload
      setTelemetry({
        calc_km: data.telemetry.calc_km,
        actual_km: data.telemetry.actual_km,
        error_margin: data.telemetry.error_margin,
        inlet_supply: data.telemetry.inlet_supply,
        delivery_station: data.telemetry.delivery_station,
      });

      setSystemStatus(
        data.telemetry.status === "SECURE" ? "NOMINAL" : "RUPTURE",
      );

      const sampleTable = data.plot_data.scada_x.map((xVal, index) => ({
        km: xVal,
        dp: data.plot_data.scada_y[index],
      }));
      setScadaTable(sampleTable);

      // Dynamically calculate the highest point on the graph so vertical lines stretch to the ceiling
      const maxY = Math.max(
        ...data.plot_data.curve_y,
        ...data.plot_data.scada_y,
      );

      setPlotTraces([
        {
          x: data.plot_data.scada_x,
          y: data.plot_data.scada_y,
          mode: "markers",
          name: "SCADA Sensors",
          marker: { color: "#00ffcc", size: 10 },
        },
        {
          x: data.plot_data.wave_x,
          y: data.plot_data.wave_y,
          mode: "markers",
          name: "Active Wave Tip Sensors",
          marker: {
            color: "#ff00ff",
            size: 14,
            line: { color: "white", width: 1.5 },
          },
        },
        {
          x: data.plot_data.curve_x,
          y: data.plot_data.curve_y,
          mode: "lines",
          name: "Quadratic Wave Interpolation",
          line: { color: "#ffff00", width: 3, dash: "dash" },
        },
        {
          x: [data.telemetry.calc_km, data.telemetry.calc_km],
          y: [-10, maxY * 1.2], // Stretches from the bottom to 20% above the peak
          mode: "lines",
          name: `Calculated: ${data.telemetry.calc_km} km`,
          line: { color: "#ffffff", width: 2, dash: "dot" }, // Changed to white!
        },
        {
          x: [data.telemetry.actual_km, data.telemetry.actual_km],
          y: [-10, maxY * 1.2], // Stretches from the bottom to 20% above the peak
          mode: "lines",
          name: `Actual: ${data.telemetry.actual_km} km`,
          line: { color: "#ef4444", width: 2 },
        },
      ]);
    } catch (error) {
      console.error("API Connection Failed", error);
      setSystemStatus("OFFLINE");
    } finally {
      setIsSimulating(false);
    }
  };

  return (
    <div className="relative min-h-screen bg-slate-950 text-slate-200 p-6 font-sans">
      {isSimulating && (
        <div className="absolute inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex flex-col justify-center items-center">
          <div className="bg-slate-900 border border-slate-800 p-8 rounded-2xl flex flex-col items-center max-w-sm shadow-2xl text-center">
            <RefreshCw className="w-12 h-12 text-fuchsia-500 animate-spin mb-4" />
            <h3 className="text-xl font-bold text-white mb-2">
              Simulating Leak for Digital Twin
            </h3>
            
          </div>
        </div>
      )}

      <header className="flex justify-between items-center mb-8 border-b border-slate-800 pb-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-white">
            Digital Twin Dashboard (case for Nord Stream)
          </h1>
          <p className="text-slate-400 text-sm mt-1">
            Quadratic Acoustic Wave-Tip Triangulation
          </p>
        </div>
        <div
          className={`flex items-center px-4 py-2 rounded-full font-bold ${systemStatus === "NOMINAL" ? "bg-green-900/30 text-green-400" : "bg-red-900/30 text-red-400"}`}
        >
          {systemStatus === "NOMINAL" ? (
            <ShieldCheck className="mr-2" />
          ) : (
            <AlertTriangle className="mr-2 animate-pulse" />
          )}
          {systemStatus === "NOMINAL" ? "SYSTEM SECURE" : "ANOMALY DETECTED"}
        </div>
      </header>

      {/* Top HUD Metrics Panel Row with '-' default handling */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl">
          <p className="text-slate-400 text-xs font-semibold uppercase tracking-wider mb-1">
            Inlet Supply (RU)
          </p>
          <p className="text-2xl font-mono text-white">
            {telemetry.inlet_supply !== "-"
              ? telemetry.inlet_supply.toFixed(2)
              : "-"}{" "}
            <span className="text-sm text-slate-500">bar</span>
          </p>
        </div>
        <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl">
          <p className="text-slate-400 text-xs font-semibold uppercase tracking-wider mb-1">
            Delivery Station (GER)
          </p>
          <p className="text-2xl font-mono text-white">
            {telemetry.delivery_station !== "-"
              ? telemetry.delivery_station.toFixed(2)
              : "-"}{" "}
            <span className="text-sm text-slate-500">bar</span>
          </p>
        </div>
        <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl">
          <p className="text-slate-400 text-xs font-semibold uppercase tracking-wider mb-1">
            Triangulated Epicenter
          </p>
          <p className="text-2xl font-mono text-yellow-400">
            {telemetry.calc_km !== "-" ? telemetry.calc_km.toFixed(2) : "-"}{" "}
            <span className="text-sm text-slate-500">km</span>
          </p>
        </div>
        <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl">
          <p className="text-slate-400 text-xs font-semibold uppercase tracking-wider mb-1">
            Location Error Margin
          </p>
          <p className="text-2xl font-mono text-fuchsia-400">
            {telemetry.error_margin !== "-"
              ? telemetry.error_margin.toFixed(3)
              : "-"}{" "}
            <span className="text-sm text-slate-500">km</span>
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="flex flex-col gap-6">
          <div className="bg-slate-900 border border-slate-800 p-6 rounded-xl">
            <h2 className="text-lg font-bold text-white mb-4 flex items-center">
              <Zap className="mr-2 w-5 h-5 text-fuchsia-500" />
              Live Injection Controls
            </h2>

            <div className="mb-6">
              <div className="flex justify-between mb-2">
                <label className="text-sm font-medium text-slate-300">
                  Target Node (Rupture Site)
                </label>
                <span className="text-fuchsia-400 font-mono">
                  {targetNode} km
                </span>
              </div>
              <input
                type="range"
                min="100"
                max="1100"
                value={targetNode}
                onChange={(e) => setTargetNode(e.target.value)}
                disabled={isSimulating}
                className="w-full accent-fuchsia-500 disabled:opacity-50"
              />
            </div>

            <div className="mb-6">
              <div className="flex justify-between mb-2">
                <label className="text-sm font-medium text-slate-300">
                  Leak Severity
                </label>
                <span className="text-yellow-400 font-mono">
                  {severity} kg/s
                </span>
              </div>
              <input
                type="range"
                min="50"
                max="4000"
                step="50"
                value={severity}
                onChange={(e) => setSeverity(e.target.value)}
                disabled={isSimulating}
                className="w-full accent-yellow-500 disabled:opacity-50"
              />
            </div>

            <button
              onClick={executeSimulation}
              disabled={isSimulating}
              className="w-full bg-fuchsia-600 hover:bg-fuchsia-500 disabled:bg-slate-800 text-white font-bold py-3 rounded-lg transition-colors disabled:cursor-not-allowed"
            >
              {isSimulating ? "Processing..." : "Execute Simulation"}
            </button>
          </div>

          <div className="bg-slate-900 border border-slate-800 p-6 rounded-xl flex-1">
            <h2 className="text-lg font-bold text-white mb-4 flex items-center">
              <Activity className="mr-2 w-5 h-5 text-cyan-400" />
              Live SCADA Telemetry
            </h2>
            <div className="max-h-60 overflow-y-auto border border-slate-800 rounded-lg">
              <table className="w-full text-left border-collapse text-sm">
                <thead>
                  <tr className="bg-slate-950 text-slate-400 border-b border-slate-800 font-mono">
                    <th className="p-2.2 font-semibold">Sensor (km)</th>
                    <th className="p-2.2 font-semibold text-right">
                      Delta-P (bar)
                    </th>
                  </tr>
                </thead>
                <tbody className="font-mono">
                  {scadaTable.length > 0 ? (
                    scadaTable.map((row, index) => (
                      <tr
                        key={index}
                        className="border-b border-slate-800/50 hover:bg-slate-800/30"
                      >
                        <td className="p-2 text-slate-300">{row.km}</td>
                        <td
                          className={`p-2 text-right ${row.dp > 0.1 ? "text-cyan-400" : "text-slate-500"}`}
                        >
                          {row.dp.toFixed(3)}
                        </td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td
                        colSpan="2"
                        className="p-4 text-center text-slate-600 italic"
                      >
                        No telemetry active. Run simulation.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        <div className="lg:col-span-2 bg-slate-900 border border-slate-800 p-6 rounded-xl flex flex-col">
          <h2 className="text-lg font-bold text-white mb-4">
            Acoustic Wave-Tip Triangulation Plane
          </h2>
          <div className="w-full bg-slate-950 rounded-lg border border-slate-800 overflow-hidden flex items-center justify-center min-h-[460px] h-full">
            <Plot
              data={plotTraces}
              layout={{
                paper_bgcolor: "transparent",
                plot_bgcolor: "transparent",
                margin: { t: 30, r: 20, l: 60, b: 50 },
                xaxis: {
                  title: "Pipeline Distance (km)",
                  gridcolor: "#1e293b",
                  tickfont: { color: "#94a3b8" },
                  range: [0, 1222],
                },
                yaxis: {
                  title: "Pressure Drop (Delta-P) (bar)",
                  gridcolor: "#1e293b",
                  tickfont: { color: "#94a3b8" },
                  autorange: true,
                }, // Autorange ensures it hugs your new full-height lines
                font: { color: "#cbd5e1" },
                showlegend: true,
                legend: {
                  orientation: "h",
                  y: -0.18,
                  x: 0.5,
                  xanchor: "center",
                },
              }}
              useResizeHandler={true}
              style={{ width: "100%", height: "100%" }}
            />
          </div>
        </div>
      </div>
    </div>
  );
};

export default DigitalTwinDashboard;
