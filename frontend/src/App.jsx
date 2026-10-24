import { useEffect, useMemo, useState } from "react";

import {
  Wind,
  Activity,
  TrendingUp,
  AlertTriangle,
  CalendarDays,
  RefreshCw,
  Download,
} from "lucide-react";

import {
  ResponsiveContainer,
  LineChart,
  Line,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  BarChart,
  Bar,
} from "recharts";

import { fetchAnalysis } from "./services/api";

import "./index.css";


function MetricCard({ title, value, unit, icon: Icon }) {
  return (
    <div className="metric-card">
      <div className="metric-header">
        <span>{title}</span>
        <Icon size={20} />
      </div>

      <div className="metric-value">
        {value ?? "—"}
        {value != null && unit && (
          <span className="metric-unit"> {unit}</span>
        )}
      </div>
    </div>
  );
}


function formatTime(value) {
  return new Date(value).toLocaleString("en-GB", {
    timeZone: "UTC",
    day: "2-digit",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  });
}


function downloadCSV(records) {
  if (!records.length) return;

  const columns = [
    "startTime",
    "publishTime",
    "decisionCutoff",
    "forecast",
    "actual",
    "error",
    "absoluteError",
  ];

  const rows = [
    columns.join(","),
    ...records.map((record) =>
      columns.map((key) => record[key]).join(",")
    ),
  ];

  const blob = new Blob([rows.join("\n")], {
    type: "text/csv;charset=utf-8",
  });

  const url = URL.createObjectURL(blob);

  const link = document.createElement("a");
  link.href = url;
  link.download = "windscope-analysis.csv";
  link.click();

  URL.revokeObjectURL(url);
}


export default function App() {
  const [startDate, setStartDate] = useState("2026-01-02");
  const [endDate, setEndDate] = useState("2026-02-01");

  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [refreshKey, setRefreshKey] = useState(0);

  useEffect(() => {
    let active = true;

    async function load() {
      setLoading(true);
      setError("");

      try {
        const result = await fetchAnalysis(startDate, endDate);

        if (active) {
          setData(result);
        }
      } catch (err) {
        if (active) {
          setData(null);
          setError(err.message);
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    load();

    return () => {
      active = false;
    };
  }, [startDate, endDate, refreshKey]);


  const records = data?.records || [];
  const metrics = data?.metrics || {};

  const chartData = useMemo(() => {
    return records.map((row) => ({
      ...row,
      label: formatTime(row.startTime),
    }));
  }, [records]);


  return (
    <div className="app">
      <aside className="sidebar">
        <div className="brand">
          <Wind size={28} />
          <div>
            <h2>WindScope</h2>
            <p>Energy Intelligence</p>
          </div>
        </div>

        <nav>
          <div className="nav-item active">
            <Activity size={18} />
            Forecast Analytics
          </div>
        </nav>

        <div className="sidebar-footer">
          <p>UK Wind Generation</p>
          <span>Powered by Elexon BMRS</span>
        </div>
      </aside>


      <main className="main-content">
        <header className="topbar">
          <div>
            <div className="eyebrow">
              ENERGY PROCUREMENT INTELLIGENCE
            </div>

            <h1>Wind Generation Analytics</h1>

            <p className="subtitle">
              Historical day-ahead forecasts and accuracy
              analysis for January 2026
            </p>
          </div>

          <div className="status-badge">
            Historical Analysis
          </div>
        </header>


        <section className="filter-bar">
          <div className="filter-title">
            <CalendarDays size={18} />
            Decision Date Range
          </div>

          <div className="filter-controls">
            <input
              type="date"
              min="2026-01-01"
              max="2026-02-01"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
            />

            <span>to</span>

            <input
              type="date"
              min="2026-01-01"
              max="2026-02-01"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
            />

            <button
              className="secondary-btn"
              onClick={() => setRefreshKey((x) => x + 1)}
            >
              <RefreshCw size={16} />
              Refresh
            </button>

            <button
              className="primary-btn"
              disabled={!records.length}
              onClick={() => downloadCSV(records)}
            >
              <Download size={16} />
              Export CSV
            </button>
          </div>
        </section>


        {loading && (
          <div className="message">
            Loading wind generation analysis...
          </div>
        )}

        {error && (
          <div className="message error">
            <AlertTriangle size={18} />
            {error}
          </div>
        )}

        {!loading && !error && (
          <>
            <section className="metrics-grid">
              <MetricCard
                title="Mean Forecast"
                value={metrics.meanForecast}
                unit="MW"
                icon={Wind}
              />

              <MetricCard
                title="Mean Actual"
                value={metrics.meanActual}
                unit="MW"
                icon={Activity}
              />

              <MetricCard
                title="Mean Absolute Error"
                value={metrics.mae}
                unit="MW"
                icon={TrendingUp}
              />

              <MetricCard
                title="Root Mean Squared Error"
                value={metrics.rmse}
                unit="MW"
                icon={AlertTriangle}
              />
            </section>


            <section className="secondary-metrics">
              <div>
                <span>Forecast Bias</span>
                <strong>
                  {metrics.bias ?? "—"} MW
                </strong>
              </div>

              <div>
                <span>MAPE</span>
                <strong>
                  {metrics.mape ?? "—"}%
                </strong>
              </div>

              <div>
                <span>Matched Intervals</span>
                <strong>
                  {metrics.count ?? 0}
                </strong>
              </div>
            </section>


            <section className="chart-card">
              <div className="section-header">
                <div>
                  <h2>Forecast vs Actual Generation</h2>
                  <p>
                    Wind power generation across matched
                    delivery intervals (MW)
                  </p>
                </div>
              </div>

              <div className="chart-container">
                {chartData.length ? (
                  <ResponsiveContainer width="100%" height={340}>
                    <LineChart data={chartData}>
                      <CartesianGrid
                        strokeDasharray="3 3"
                        stroke="#e5e7eb"
                      />

                      <XAxis
                        dataKey="label"
                        minTickGap={50}
                        tick={{ fontSize: 11 }}
                      />

                      <YAxis
                        tick={{ fontSize: 12 }}
                        label={{
                          value: "MW",
                          angle: -90,
                          position: "insideLeft",
                        }}
                      />

                      <Tooltip />
                      <Legend />

                      <Line
                        type="monotone"
                        dataKey="forecast"
                        name="Forecast"
                        stroke="#2563eb"
                        strokeWidth={2}
                        dot={false}
                      />

                      <Line
                        type="monotone"
                        dataKey="actual"
                        name="Actual"
                        stroke="#10b981"
                        strokeWidth={2}
                        dot={false}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="empty-state">
                    No matched records for this period.
                  </div>
                )}
              </div>
            </section>


            <section className="chart-card">
              <div className="section-header">
                <div>
                  <h2>Forecast Error Analysis</h2>
                  <p>
                    Signed forecast error: forecast minus
                    actual (MW)
                  </p>
                </div>
              </div>

              <div className="chart-container">
                {chartData.length ? (
                  <ResponsiveContainer width="100%" height={280}>
                    <BarChart data={chartData}>
                      <CartesianGrid strokeDasharray="3 3" />

                      <XAxis
                        dataKey="label"
                        minTickGap={50}
                        tick={{ fontSize: 11 }}
                      />

                      <YAxis />
                      <Tooltip />

                      <Bar
                        dataKey="error"
                        name="Forecast Error"
                        fill="#f59e0b"
                      />
                    </BarChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="empty-state">
                    No error data available.
                  </div>
                )}
              </div>
            </section>


            <section className="table-card">
              <div className="section-header">
                <div>
                  <h2>Detailed Generation Records</h2>
                  <p>
                    Forecasts selected using the day-ahead
                    decision cutoff
                  </p>
                </div>
              </div>

              <div className="table-wrapper">
                <table>
                  <thead>
                    <tr>
                      <th>Delivery Time (UTC)</th>
                      <th>Forecast (MW)</th>
                      <th>Actual (MW)</th>
                      <th>Error (MW)</th>
                      <th>Published (UTC)</th>
                    </tr>
                  </thead>

                  <tbody>
                    {records.slice(0, 100).map((row) => (
                      <tr key={row.startTime}>
                        <td>{formatTime(row.startTime)}</td>
                        <td>{row.forecast}</td>
                        <td>{row.actual}</td>

                        <td
                          className={
                            row.error > 0
                              ? "positive-error"
                              : "negative-error"
                          }
                        >
                          {row.error}
                        </td>

                        <td>{formatTime(row.publishTime)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              <p className="table-note">
                Showing up to 100 records.
                Export CSV for the complete selected dataset.
              </p>
            </section>


            <footer>
              <p>
                Source: Elexon BMRS — FUELHH and WINDFOR
              </p>

              <p>
                Method: Latest eligible forecast before
                12:00 UTC on the preceding day.
              </p>

              <p>
                Historical pilot analysis, not live trading advice.
              </p>
            </footer>
          </>
        )}
      </main>
    </div>
  );
}