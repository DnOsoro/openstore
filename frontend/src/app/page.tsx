"use client";

import { useState, useEffect } from "react";
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid, LineChart, Line } from "recharts";
import { Play, ShieldCheck, AlertCircle, Database, Sparkles } from "lucide-react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function Home() {
  const [prompt, setPrompt] = useState("");
  const [loading, setLoading] = useState(false);
  const [aiData, setAiData] = useState<any>(null);
  const [monthlyData, setMonthlyData] = useState<any[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchMonthlyRevenue();
  }, []);

  const fetchMonthlyRevenue = async () => {
    try {
      const res = await fetch(`${API_URL}/api/v1/analytics/monthly-revenue`);
      if (res.ok) {
        const json = await res.json();
        setMonthlyData(json.data || []);
      }
    } catch (err) {
      console.error("Failed to load monthly revenue", err);
    }
  };

  const handleAiQuery = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!prompt.trim()) return;

    setLoading(true);
    setError(null);
    setAiData(null);

    try {
      const res = await fetch(`${API_URL}/api/v1/ai-query`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt }),
      });

      const json = await res.json();

      if (res.ok) {
        setAiData(json);
      } else {
        setError(json.detail || "Query execution failed.");
      }
    } catch (err: any) {
      setError(`Failed to connect to server: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-slate-900 text-slate-100 p-8 space-y-8 font-sans">
      <header className="flex justify-between items-center border-b border-slate-800 pb-4">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2 text-indigo-400">
            <Database className="w-7 h-7" /> OpenStore AI Analytics
          </h1>
          <p className="text-slate-400 text-sm">PostgreSQL + OpenRouter + Guardrailed SQL Execution</p>
        </div>
        <div className="flex items-center gap-2 bg-emerald-950 text-emerald-400 border border-emerald-800 px-3 py-1 rounded-full text-xs font-semibold">
          <ShieldCheck className="w-4 h-4" /> Guardrails Active
        </div>
      </header>

      <section className="bg-slate-800 border border-slate-700 rounded-xl p-6 shadow-xl space-y-4">
        <h2 className="text-lg font-semibold flex items-center gap-2 text-amber-400">
          <Sparkles className="w-5 h-5" /> Ask Natural Language AI Query
        </h2>
        <form onSubmit={handleAiQuery} className="flex gap-3">
          <input
            type="text"
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="e.g. Show top 5 cities by total revenue"
            className="flex-1 bg-slate-900 border border-slate-700 rounded-lg px-4 py-3 text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
          <button
            type="submit"
            disabled={loading}
            className="bg-indigo-600 hover:bg-indigo-500 text-white font-medium px-6 py-3 rounded-lg flex items-center gap-2 disabled:opacity-50 transition"
          >
            {loading ? "Processing..." : <><Play className="w-4 h-4 fill-current" /> Execute</>}
          </button>
        </form>

        {error && (
          <div className="bg-rose-950/80 border border-rose-800 text-rose-300 p-4 rounded-lg flex items-center gap-3 text-sm">
            <AlertCircle className="w-5 h-5 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {aiData && (
          <div className="space-y-4 mt-4 border-t border-slate-700 pt-4">
            <div>
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Validated SQL Query</span>
              <pre className="bg-slate-950 border border-slate-800 text-amber-300 p-3 rounded-lg text-sm font-mono overflow-x-auto mt-1">
                {aiData.validated_sql || aiData.generated_sql}
              </pre>
            </div>

            {aiData.data && aiData.data.length > 0 && (
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 pt-2">
                <div className="bg-slate-900 border border-slate-800 rounded-lg p-4 max-h-80 overflow-y-auto">
                  <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-2">Results Table ({aiData.rows_returned} rows)</span>
                  <table className="w-full text-left text-sm border-collapse">
                    <thead>
                      <tr className="border-b border-slate-800 text-slate-400">
                        {Object.keys(aiData.data[0]).map((key) => (
                          <th key={key} className="p-2 capitalize">{key.replace("_", " ")}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {aiData.data.map((row: any, idx: number) => (
                        <tr key={idx} className="border-b border-slate-800/50 hover:bg-slate-800/40">
                          {Object.values(row).map((val: any, i: number) => (
                            <td key={i} className="p-2 font-mono text-xs">{String(val)}</td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                <div className="bg-slate-900 border border-slate-800 rounded-lg p-4 h-80">
                  <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-2">Visualization</span>
                  <ResponsiveContainer width="100%" height="90%">
                    <BarChart data={aiData.data}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                      <XAxis dataKey={Object.keys(aiData.data[0])[0]} stroke="#94a3b8" tick={{ fontSize: 11 }} />
                      <YAxis stroke="#94a3b8" tick={{ fontSize: 11 }} />
                      <Tooltip contentStyle={{ backgroundColor: "#0f172a", borderColor: "#334155" }} />
                      <Bar dataKey={Object.keys(aiData.data[0])[1]} fill="#6366f1" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>
            )}
          </div>
        )}
      </section>

      {monthlyData.length > 0 && (
        <section className="bg-slate-800 border border-slate-700 rounded-xl p-6 shadow-xl space-y-4">
          <h2 className="text-lg font-semibold text-slate-200">📈 Monthly Revenue Trend</h2>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={monthlyData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis dataKey="year_month" stroke="#94a3b8" />
                <YAxis stroke="#94a3b8" />
                <Tooltip contentStyle={{ backgroundColor: "#0f172a", borderColor: "#334155" }} />
                <Line type="monotone" dataKey="total_revenue" stroke="#10b981" strokeWidth={2} dot={{ r: 3 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </section>
      )}
    </main>
  );
}
