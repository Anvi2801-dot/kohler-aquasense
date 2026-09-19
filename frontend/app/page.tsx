"use client";

import { useEffect, useState, useCallback } from "react";
import {
  Activity,
  Building2,
  CheckCircle2,
  ShieldCheck,
  Wrench,
  Wifi,
  WifiOff,
} from "lucide-react";

import Header from "../components/HeaderKPIs";
import SpatialFloorPlan from "../components/SpatialMap";
import TechnicianPortal from "../components/TechPortal";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

type Persona = "executive" | "technician";

type FixtureStatus = "NORMAL" | "LEAK" | "HYGIENE_WARNING";

interface Fixture {
  fixture_id: string;
  fixture_name: string;
  type: "Sink" | "Urinal" | "Stall";
  water_flow_lpm: number;
  occupancy_count_10m: number;
  pressure_psi: number;
  status: FixtureStatus;
  hygiene_score: number;
  timestamp?: string;
  last_cleaned?: string;
}

interface TelemetryResponse {
  timestamp: string;
  facility: string;
  fixture_count: number;
  fixtures: Fixture[];
}

export default function HomePage() {
  const [persona, setPersona] = useState<Persona>("executive");

  const [fixtures, setFixtures] = useState<Fixture[]>([]);
  const [backendOnline, setBackendOnline] = useState(false);

  const [healthScore, setHealthScore] = useState(94);
  const [waterEfficiency, setWaterEfficiency] = useState(96);
  const [hygieneCompliance, setHygieneCompliance] = useState(91);

  // Fetch telemetry using cached endpoint on initial loads/switches to avoid state reset
  const fetchTelemetry = useCallback(async (isInitial = false) => {
    try {
      const endpoint = isInitial ? "/api/telemetry/cached" : "/api/telemetry";
      const response = await fetch(`${API_URL}${endpoint}`, {
        cache: "no-store",
      });

      if (!response.ok) {
        throw new Error("Telemetry request failed");
      }

      const data: TelemetryResponse = await response.json();

      setFixtures(data.fixtures);
      setBackendOnline(true);

      calculateHealth(data.fixtures);
    } catch {
      setBackendOnline(false);
    }
  }, []);

  useEffect(() => {
    // Immediate fetch on mount using cached state to prevent flicker
    fetchTelemetry(true);

    const interval = setInterval(() => {
      fetchTelemetry(false);
    }, 5000);

    return () => clearInterval(interval);
  }, [fetchTelemetry]);

  function calculateHealth(data: Fixture[]) {
    if (!data.length) return;

    const normal = data.filter(
      (fixture) => fixture.status === "NORMAL"
    ).length;

    const hygieneWarnings = data.filter(
      (fixture) => fixture.status === "HYGIENE_WARNING"
    ).length;

    const leaks = data.filter(
      (fixture) => fixture.status === "LEAK"
    ).length;

    const averageHygiene =
      data.reduce(
        (sum, fixture) => sum + fixture.hygiene_score,
        0
      ) / data.length;

    const availability =
      ((normal + hygieneWarnings) / data.length) * 100;

    const calculatedHealth = Math.max(
      0,
      Math.min(
        100,
        Math.round(
          averageHygiene * 0.6 +
            availability * 0.4 -
            leaks * 8
        )
      )
    );

    setHealthScore(calculatedHealth);

    setHygieneCompliance(
      Math.round(averageHygiene)
    );

    setWaterEfficiency(
      Math.max(
        70,
        Math.min(
          100,
          Math.round(100 - leaks * 3)
        )
      )
    );
  }

  const normalCount = fixtures.filter(
    (fixture) => fixture.status === "NORMAL"
  ).length;

  const warningCount = fixtures.filter(
    (fixture) => fixture.status === "HYGIENE_WARNING"
  ).length;

  const leakCount = fixtures.filter(
    (fixture) => fixture.status === "LEAK"
  ).length;

  const activeIssues = fixtures.filter(
    (fixture) => fixture.status !== "NORMAL"
  );

  return (
    <main className="min-h-screen bg-[#0b0f19] text-white">

      {/* ================================================== */}
      {/* HEADER + KPI STRIP */}
      {/* ================================================== */}

      <Header />

      {/* ================================================== */}
      {/* MAIN APPLICATION */}
      {/* ================================================== */}

      <div className="mx-auto max-w-[1600px] px-6 py-6 lg:px-8">

        {/* ================================================== */}
        {/* FACILITY TITLE + PERSONA SWITCHER */}
        {/* ================================================== */}

        <div className="mb-6 flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">

          <div>
            <div className="flex items-center gap-2">
              <p className="text-xs font-medium uppercase tracking-[0.18em] text-sky-400">
                Facility Command Center
              </p>

              <span
                className={`flex items-center gap-1.5 rounded-full border px-2 py-0.5 text-[10px] font-medium ${
                  backendOnline
                    ? "border-emerald-500/20 bg-emerald-500/10 text-emerald-400"
                    : "border-red-500/20 bg-red-500/10 text-red-400"
                }`}
              >
                {backendOnline ? (
                  <>
                    <Wifi size={10} />
                    LIVE
                  </>
                ) : (
                  <>
                    <WifiOff size={10} />
                    OFFLINE
                  </>
                )}
              </span>
            </div>

            <h2 className="mt-1 text-xl font-semibold tracking-tight text-white">
              Pune International Airport (PNQ) — NITB Departure Zone 3
            </h2>

            <p className="mt-1 text-sm text-slate-500">
              Real-time commercial fixture intelligence
            </p>
          </div>

          {/* Persona Switcher */}

          <div className="flex rounded-lg border border-[#1f2937] bg-[#111827] p-1">

            <button
              onClick={() => {
                setPersona("executive");
                fetchTelemetry(true);
              }}
              className={`flex items-center gap-2 rounded-md px-4 py-2 text-sm font-medium transition ${
                persona === "executive"
                  ? "bg-[#1f2937] text-white shadow"
                  : "text-slate-500 hover:text-slate-300"
              }`}
            >
              <Building2 size={16} />
              Executive View
            </button>

            <button
              onClick={() => setPersona("technician")}
              className={`flex items-center gap-2 rounded-md px-4 py-2 text-sm font-medium transition ${
                persona === "technician"
                  ? "bg-[#1f2937] text-white shadow"
                  : "text-slate-500 hover:text-slate-300"
              }`}
            >
              <Wrench size={16} />
              Field Technician Portal - Marcus
            </button>

          </div>
        </div>

        {/* ================================================== */}
        {/* EXECUTIVE VIEW */}
        {/* ================================================== */}

        {persona === "executive" && (
          <section className="space-y-6">

            {/* OPERATIONAL OVERVIEW */}

            <div className="grid grid-cols-1 gap-6 xl:grid-cols-3">

              <div className="rounded-xl border border-[#1f2937] bg-[#111827] p-6 xl:col-span-2">

                <div className="flex items-center justify-between">

                  <div>
                    <p className="text-xs uppercase tracking-[0.15em] text-slate-500">
                      Operational Overview
                    </p>

                    <h3 className="mt-1 text-lg font-semibold">
                      Commercial Fixture Fleet
                    </h3>
                  </div>

                  <div className="flex items-center gap-2 text-xs text-emerald-400">
                    <span className="h-2 w-2 animate-pulse rounded-full bg-emerald-400" />
                    Live telemetry
                  </div>

                </div>

                {/* LIVE STATUS COUNTERS */}

                <div className="mt-8 grid grid-cols-3 gap-4">

                  <StatusBlock
                    label="Normal"
                    value={String(normalCount)}
                    status="normal"
                  />

                  <StatusBlock
                    label="Hygiene Warning"
                    value={String(warningCount)}
                    status="warning"
                  />

                  <StatusBlock
                    label="Active Leak"
                    value={String(leakCount)}
                    status="critical"
                  />

                </div>

              </div>

              {/* FACILITY HEALTH */}

              <div className="rounded-xl border border-[#1f2937] bg-[#111827] p-6">

                <div className="flex items-center gap-3">

                  <div className="rounded-lg bg-sky-500/10 p-2 text-sky-400">
                    <ShieldCheck size={19} />
                  </div>

                  <div>
                    <p className="text-xs uppercase tracking-wider text-slate-500">
                      Facility Health
                    </p>

                    <h3 className="font-semibold">
                      {healthScore >= 90
                        ? "Excellent"
                        : healthScore >= 75
                        ? "Good"
                        : "Attention Required"}
                    </h3>
                  </div>

                </div>

                {/* HEALTH SCORE */}

                <div className="mt-8 flex items-center justify-center">

                  <div className="relative flex h-44 w-44 items-center justify-center rounded-full border-[12px] border-emerald-500/20">

                    <div
                      className="absolute inset-0 rounded-full border-[12px] border-transparent border-t-emerald-400 border-r-emerald-400"
                      style={{
                        transform: `rotate(${Math.max(
                          0,
                          healthScore * 1.8 - 90
                        )}deg)`,
                      }}
                    />

                    <div className="text-center">

                      <p className="text-4xl font-bold">
                        {healthScore}
                      </p>

                      <p className="text-xs uppercase tracking-widest text-slate-500">
                        Health Score
                      </p>

                    </div>

                  </div>

                </div>

                <div className="mt-8 space-y-4">

                  <HealthRow
                    label="Water Efficiency"
                    value={`${waterEfficiency}%`}
                  />

                  <HealthRow
                    label="Hygiene Compliance"
                    value={`${hygieneCompliance}%`}
                  />

                  <HealthRow
                    label="Fleet Availability"
                    value={
                      fixtures.length
                        ? `${Math.round(
                            ((fixtures.length - leakCount) /
                              fixtures.length) *
                              1000
                          ) / 10}%`
                        : "99.7%"
                    }
                  />

                </div>

              </div>

            </div>

            {/* LIVE SPATIAL FLOOR PLAN */}

            <SpatialFloorPlan />

            {/* LIVE ANOMALY STREAM */}

            <div className="rounded-xl border border-[#1f2937] bg-[#111827]">

              <div className="flex items-center justify-between border-b border-[#1f2937] px-6 py-4">

                <div>
                  <p className="text-xs uppercase tracking-[0.15em] text-slate-500">
                    Monitoring
                  </p>

                  <h3 className="mt-1 font-semibold">
                    Live Anomaly Stream
                  </h3>
                </div>

                <div className="flex items-center gap-3">

                  <span className="flex items-center gap-2 rounded-md border border-[#1f2937] bg-[#0b0f19] px-3 py-1.5 text-xs text-slate-400">
                    <Activity size={13} />
                    Auto-refresh: 5s
                  </span>

                  {backendOnline && (
                    <span className="flex items-center gap-1.5 text-xs text-emerald-400">
                      <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-emerald-400" />
                      Connected
                    </span>
                  )}

                </div>

              </div>

              {activeIssues.length === 0 ? (

                <div className="flex flex-col items-center justify-center py-14">

                  <div className="rounded-full bg-emerald-500/10 p-4 text-emerald-400">
                    <CheckCircle2 size={28} />
                  </div>

                  <p className="mt-4 text-sm font-medium text-slate-300">
                    No active anomalies detected
                  </p>

                  <p className="mt-1 text-xs text-slate-600">
                    All connected fixtures are operating within expected parameters.
                  </p>

                </div>

              ) : (

                <div className="overflow-x-auto">

                  <table className="w-full text-left text-sm">

                    <thead className="border-b border-[#1f2937] text-xs uppercase tracking-wider text-slate-500">

                      <tr>

                        <th className="px-6 py-3">
                          Fixture
                        </th>

                        <th className="px-6 py-3">
                          Type
                        </th>

                        <th className="px-6 py-3">
                          Flow
                        </th>

                        <th className="px-6 py-3">
                          Occupancy
                        </th>

                        <th className="px-6 py-3">
                          Hygiene
                        </th>

                        <th className="px-6 py-3">
                          Status
                        </th>

                      </tr>

                    </thead>

                    <tbody className="divide-y divide-[#1f2937]">

                      {activeIssues.map((fixture) => (

                        <AnomalyRow
                          key={fixture.fixture_id}
                          fixture={fixture.fixture_name}
                          type={fixture.type}
                          flow={`${fixture.water_flow_lpm.toFixed(2)} LPM`}
                          occupancy={String(
                            fixture.occupancy_count_10m
                          )}
                          hygiene={String(
                            Math.round(fixture.hygiene_score)
                          )}
                          status={fixture.status}
                        />

                      ))}

                    </tbody>

                  </table>

                </div>

              )}

            </div>

          </section>
        )}

        {/* ================================================== */}
        {/* TECHNICIAN VIEW */}
        {/* ================================================== */}

        {persona === "technician" && <TechnicianPortal />}

      </div>
    </main>
  );
}

/* ====================================================== */
/* STATUS BLOCK */
/* ====================================================== */

function StatusBlock({
  label,
  value,
  status,
}: {
  label: string;
  value: string;
  status: "normal" | "warning" | "critical";
}) {
  const styles = {
    normal:
      "border-emerald-500/20 bg-emerald-500/5 text-emerald-400",

    warning:
      "border-amber-500/20 bg-amber-500/5 text-amber-400",

    critical:
      "border-red-500/20 bg-red-500/5 text-red-400",
  };

  return (
    <div
      className={`rounded-lg border p-4 ${styles[status]}`}
    >
      <p className="text-xs text-slate-500">
        {label}
      </p>

      <p className="mt-2 text-2xl font-semibold">
        {value}
      </p>
    </div>
  );
}

/* ====================================================== */
/* HEALTH ROW */
/* ====================================================== */

function HealthRow({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <div className="flex items-center justify-between">

      <span className="text-sm text-slate-400">
        {label}
      </span>

      <span className="text-sm font-semibold text-emerald-400">
        {value}
      </span>

    </div>
  );
}

/* ====================================================== */
/* ANOMALY ROW */
/* ====================================================== */

function AnomalyRow({
  fixture,
  type,
  flow,
  occupancy,
  hygiene,
  status,
}: {
  fixture: string;
  type: string;
  flow: string;
  occupancy: string;
  hygiene: string;
  status: FixtureStatus;
}) {
  const statusStyles = {
    NORMAL:
      "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",

    LEAK:
      "bg-red-500/10 text-red-400 border-red-500/20",

    HYGIENE_WARNING:
      "bg-amber-500/10 text-amber-400 border-amber-500/20",
  };

  return (
    <tr className="transition hover:bg-[#0d1421]">

      <td className="px-6 py-4 font-medium text-white">
        {fixture}
      </td>

      <td className="px-6 py-4 text-slate-500">
        {type}
      </td>

      <td className="px-6 py-4 font-mono text-slate-300">
        {flow}
      </td>

      <td className="px-6 py-4 font-mono text-slate-300">
        {occupancy}
      </td>

      <td className="px-6 py-4 font-mono text-slate-300">
        {hygiene}
      </td>

      <td className="px-6 py-4">

        <span
          className={`rounded-md border px-2.5 py-1 text-[10px] font-semibold tracking-wide ${statusStyles[status]}`}
        >
          {status.replace("_", " ")}
        </span>

      </td>

    </tr>
  );
}