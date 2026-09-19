"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import {
  AlertTriangle,
  CheckCircle2,
  ChevronRight,
  Droplets,
  Gauge,
  MapPin,
  Plane,
  RotateCcw,
  Sparkles,
  Bath,
  Users,
  Waves,
  X,
} from "lucide-react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";


// ============================================================
// TYPES
// ============================================================

type FixtureStatus =
  | "NORMAL"
  | "LEAK"
  | "HYGIENE_WARNING";

type FixtureType =
  | "Sink"
  | "Urinal"
  | "Stall";

interface Fixture {
  fixture_id: string;
  fixture_name: string;
  type: FixtureType;

  water_flow_lpm: number;
  occupancy_count_10m: number;
  flush_count_10m?: number;
  pressure_psi: number;

  status: FixtureStatus;

  hygiene_score: number;
  timestamp?: string;

  last_cleaned?: string;
}


// ============================================================
// DEMO FALLBACK DATA
// ============================================================

const INITIAL_FIXTURES: Fixture[] = [
  {
    fixture_id: "KOHLER_FAUCET_101",
    fixture_name: "Sink 1",
    type: "Sink",
    water_flow_lpm: 0.72,
    occupancy_count_10m: 8,
    pressure_psi: 51.2,
    status: "NORMAL",
    hygiene_score: 89,
    last_cleaned: "12 min ago",
  },
  {
    fixture_id: "KOHLER_FAUCET_102",
    fixture_name: "Sink 2",
    type: "Sink",
    water_flow_lpm: 0.64,
    occupancy_count_10m: 6,
    pressure_psi: 50.8,
    status: "NORMAL",
    hygiene_score: 91,
    last_cleaned: "15 min ago",
  },
  {
    fixture_id: "KOHLER_FAUCET_103",
    fixture_name: "Sink 3",
    type: "Sink",
    water_flow_lpm: 0.91,
    occupancy_count_10m: 13,
    pressure_psi: 49.7,
    status: "HYGIENE_WARNING",
    hygiene_score: 27,
    last_cleaned: "38 min ago",
  },
  {
    fixture_id: "KOHLER_FAUCET_104",
    fixture_name: "Sink 4",
    type: "Sink",
    water_flow_lpm: 0.58,
    occupancy_count_10m: 5,
    pressure_psi: 52.1,
    status: "NORMAL",
    hygiene_score: 94,
    last_cleaned: "8 min ago",
  },
  {
    fixture_id: "KOHLER_URINAL_201",
    fixture_name: "Urinal 1",
    type: "Urinal",
    water_flow_lpm: 0.84,
    occupancy_count_10m: 11,
    pressure_psi: 48.9,
    status: "NORMAL",
    hygiene_score: 85,
    last_cleaned: "18 min ago",
  },
  {
    fixture_id: "KOHLER_URINAL_202",
    fixture_name: "Urinal 2",
    type: "Urinal",
    water_flow_lpm: 0.77,
    occupancy_count_10m: 9,
    pressure_psi: 49.5,
    status: "NORMAL",
    hygiene_score: 87,
    last_cleaned: "21 min ago",
  },
  {
    fixture_id: "KOHLER_URINAL_203",
    fixture_name: "Urinal 3",
    type: "Urinal",
    water_flow_lpm: 0.71,
    occupancy_count_10m: 7,
    pressure_psi: 50.1,
    status: "NORMAL",
    hygiene_score: 90,
    last_cleaned: "14 min ago",
  },
  {
    fixture_id: "KOHLER_STALL_301",
    fixture_name: "Stall 1",
    type: "Stall",
    water_flow_lpm: 0.18,
    occupancy_count_10m: 4,
    pressure_psi: 47.6,
    status: "NORMAL",
    hygiene_score: 92,
    last_cleaned: "11 min ago",
  },
  {
    fixture_id: "KOHLER_STALL_302",
    fixture_name: "Stall 2",
    type: "Stall",
    water_flow_lpm: 0.16,
    occupancy_count_10m: 3,
    pressure_psi: 47.9,
    status: "NORMAL",
    hygiene_score: 95,
    last_cleaned: "9 min ago",
  },
];


// ============================================================
// FIXTURE ICON
// ============================================================

function FixtureIcon({
  type,
  size = 18,
}: {
  type: FixtureType;
  size?: number;
}) {
  if (type === "Sink") {
    return <Waves size={size} />;
  }

  if (type === "Urinal") {
    return <Droplets size={size} />;
  }

  return <Bath size={size} />;
}


// ============================================================
// STATUS CONFIGURATION
// ============================================================

const STATUS_CONFIG = {
  NORMAL: {
    label: "Normal Operation",

    border: "border-[#22c55e]",
    text: "text-[#22c55e]",
    bg: "bg-[#22c55e]/10",
    glow: "shadow-[0_0_18px_rgba(34,197,94,0.16)]",

    dot: "bg-[#22c55e]",
  },

  HYGIENE_WARNING: {
    label: "Cleaning Needed",

    border: "border-[#f59e0b]",
    text: "text-[#f59e0b]",
    bg: "bg-[#f59e0b]/10",
    glow: "shadow-[0_0_18px_rgba(245,158,11,0.18)]",

    dot: "bg-[#f59e0b]",
  },

  LEAK: {
    label: "Active Micro-Leak",

    border: "border-[#ef4444]",
    text: "text-[#ef4444]",
    bg: "bg-[#ef4444]/10",
    glow: "shadow-[0_0_22px_rgba(239,68,68,0.30)]",

    dot: "bg-[#ef4444]",
  },
};


// ============================================================
// MAIN COMPONENT
// ============================================================

export default function SpatialFloorPlan() {
  const [fixtures, setFixtures] =
    useState<Fixture[]>(INITIAL_FIXTURES);

  const [selectedFixture, setSelectedFixture] =
    useState<Fixture | null>(null);

  const [actionLoading, setActionLoading] =
    useState<string | null>(null);

  const [backendOnline, setBackendOnline] =
    useState(false);


  // ==========================================================
  // FETCH TELEMETRY (Cached by default, Live on forced update)
  // ==========================================================

  const fetchTelemetry = useCallback(async (isLive = false) => {
    try {
      const endpoint = isLive ? "/api/telemetry" : "/api/telemetry/cached";
      const response = await fetch(
        `${API_URL}${endpoint}`,
        {
          cache: "no-store",
        }
      );

      if (!response.ok) {
        throw new Error(
          "Telemetry request failed"
        );
      }

      const data = await response.json();

      if (Array.isArray(data.fixtures)) {
        setFixtures(data.fixtures);
      }

      setBackendOnline(true);
    } catch (error) {
      console.error(
        "Telemetry API error:",
        error
      );

      setBackendOnline(false);
    }
  }, []);


  // ==========================================================
  // LIVE TELEMETRY POLLING
  // ==========================================================

  useEffect(() => {
    fetchTelemetry(false);

    const interval = setInterval(() => {
      fetchTelemetry(false);
    }, 5000);

    return () => clearInterval(interval);
  }, [fetchTelemetry]);


  // ==========================================================
  // SIMULATION ACTION
  // ==========================================================

  const runSimulation = async (
    action:
      | "INJECT_LEAK"
      | "FLIGHT_RUSH"
      | "RESET"
  ) => {
    try {
      setActionLoading(action);

      const response = await fetch(
        `${API_URL}/api/simulate`,
        {
          method: "POST",

          headers: {
            "Content-Type":
              "application/json",
          },

          body: JSON.stringify({
            action,
          }),
        }
      );

      if (!response.ok) {
        throw new Error(
          "Simulation request failed"
        );
      }

      await new Promise((resolve) =>
        setTimeout(resolve, 350)
      );

      // Force live update after simulation action
      await fetchTelemetry(true);

      if (action === "RESET") {
        setSelectedFixture(null);
      }
    } catch (error) {
      console.error(
        "Simulation API error:",
        error
      );
    } finally {
      setActionLoading(null);
    }
  };


  // ==========================================================
  // UPDATE SELECTED FIXTURE
  // ==========================================================

  useEffect(() => {
    if (!selectedFixture) return;

    const updatedFixture =
      fixtures.find(
        (fixture) =>
          fixture.fixture_id ===
          selectedFixture.fixture_id
      );

    if (updatedFixture) {
      setSelectedFixture(updatedFixture);
    }
  }, [fixtures, selectedFixture]);


  // ==========================================================
  // FIXTURE GROUPS
  // ==========================================================

  const sinks = useMemo(
    () =>
      fixtures.filter(
        (fixture) =>
          fixture.type === "Sink"
      ),
    [fixtures]
  );

  const urinals = useMemo(
    () =>
      fixtures.filter(
        (fixture) =>
          fixture.type === "Urinal"
      ),
    [fixtures]
  );

  const stalls = useMemo(
    () =>
      fixtures.filter(
        (fixture) =>
          fixture.type === "Stall"
      ),
    [fixtures]
  );


  // ==========================================================
  // COUNTERS
  // ==========================================================

  const normalCount = fixtures.filter(
    (fixture) =>
      fixture.status === "NORMAL"
  ).length;

  const warningCount = fixtures.filter(
    (fixture) =>
      fixture.status ===
      "HYGIENE_WARNING"
  ).length;

  const leakCount = fixtures.filter(
    (fixture) =>
      fixture.status === "LEAK"
  ).length;


  return (
    <section className="w-full rounded-2xl border border-[#1f2937] bg-[#111827] shadow-2xl shadow-black/20">

      {/* ================================================== */}
      {/* MAP HEADER */}
      {/* ================================================== */}

      <div className="flex flex-col gap-4 border-b border-[#1f2937] px-6 py-5 md:flex-row md:items-center md:justify-between">

        <div>
          <div className="flex items-center gap-2">

            <MapPin
              size={16}
              className="text-[#38bdf8]"
            />

            <span className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[#38bdf8]">
              Spatial Intelligence
            </span>

          </div>

          <h2 className="mt-1 text-lg font-semibold text-white">
            Restroom Floor Map
          </h2>

          <p className="mt-1 text-xs text-slate-500">
            PNQ NITB · 9 Connected Fixtures
          </p>
        </div>


        {/* Map summary */}

        <div className="flex items-center gap-2">

          <StatusCounter
            color="green"
            label="Normal"
            value={normalCount}
          />

          <StatusCounter
            color="amber"
            label="Warning"
            value={warningCount}
          />

          <StatusCounter
            color="red"
            label="Leak"
            value={leakCount}
          />

        </div>

      </div>


      {/* ================================================== */}
      {/* FLOOR PLAN */}
      {/* ================================================== */}

      <div className="p-4 md:p-6">

        <div className="relative overflow-hidden rounded-xl border border-[#1f2937] bg-[#0b0f19]">

          {/* Grid background */}

          <div
            className="absolute inset-0 opacity-[0.055]"
            style={{
              backgroundImage:
                `
                linear-gradient(to right, #94a3b8 1px, transparent 1px),
                linear-gradient(to bottom, #94a3b8 1px, transparent 1px)
                `,
              backgroundSize:
                "40px 40px",
            }}
          />


          <div className="relative p-5 md:p-8">

            {/* Entry */}

            <div className="mb-5 flex justify-center">

              <div className="flex items-center gap-2 rounded-full border border-[#1f2937] bg-[#111827] px-4 py-1.5 text-[10px] font-medium uppercase tracking-[0.16em] text-slate-500">

                <ChevronRight
                  size={12}
                />

                Terminal Corridor / Entry

              </div>

            </div>


            {/* ============================== */}
            {/* TOP ZONE — SINKS */}
            {/* ============================== */}

            <FloorZone
              label="TOP ZONE"
              title="Hand-Wash Area"
              subtitle="Sinks 01 — 04"
              icon={
                <Waves size={16} />
              }
            >

              <div className="grid grid-cols-2 gap-3 md:grid-cols-4">

                {sinks.map(
                  (fixture) => (
                    <FixtureBox
                      key={
                        fixture.fixture_id
                      }
                      fixture={
                        fixture
                      }
                      onClick={() =>
                        setSelectedFixture(
                          fixture
                        )
                      }
                    />
                  )
                )}

              </div>

            </FloorZone>


            {/* Corridor */}

            <div className="my-5 flex items-center gap-3">

              <div className="h-px flex-1 bg-[#1f2937]" />

              <span className="text-[9px] uppercase tracking-[0.2em] text-slate-700">
                Main circulation
              </span>

              <div className="h-px flex-1 bg-[#1f2937]" />

            </div>


            {/* ============================== */}
            {/* MIDDLE ZONE — URINALS */}
            {/* ============================== */}

            <FloorZone
              label="MIDDLE ZONE"
              title="Urinal Bay"
              subtitle="Urinals 01 — 03"
              icon={
                <Droplets
                  size={16}
                />
              }
            >

              <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">

                {urinals.map(
                  (fixture) => (
                    <FixtureBox
                      key={
                        fixture.fixture_id
                      }
                      fixture={
                        fixture
                      }
                      onClick={() =>
                        setSelectedFixture(
                          fixture
                        )
                      }
                    />
                  )
                )}

              </div>

            </FloorZone>


            {/* Corridor */}

            <div className="my-5 flex items-center gap-3">

              <div className="h-px flex-1 bg-[#1f2937]" />

              <span className="text-[9px] uppercase tracking-[0.2em] text-slate-700">
                Privacy corridor
              </span>

              <div className="h-px flex-1 bg-[#1f2937]" />

            </div>


            {/* ============================== */}
            {/* BOTTOM ZONE — STALLS */}
            {/* ============================== */}

            <FloorZone
              label="BOTTOM ZONE"
              title="Private Stalls"
              subtitle="Stalls 01 — 02"
              icon={
                <Bath size={16} />
              }
            >

              <div className="mx-auto grid max-w-2xl grid-cols-2 gap-3">

                {stalls.map(
                  (fixture) => (
                    <FixtureBox
                      key={
                        fixture.fixture_id
                      }
                      fixture={
                        fixture
                      }
                      onClick={() =>
                        setSelectedFixture(
                          fixture
                        )
                      }
                    />
                  )
                )}

              </div>

            </FloorZone>


            {/* Exit */}

            <div className="mt-5 flex justify-center">

              <div className="flex items-center gap-2 rounded-full border border-[#1f2937] bg-[#111827] px-4 py-1.5 text-[10px] font-medium uppercase tracking-[0.16em] text-slate-500">

                Exit / Terminal Concourse

                <ChevronRight
                  size={12}
                />

              </div>

            </div>

          </div>
        </div>


        {/* ================================================== */}
        {/* LEGEND */}
        {/* ================================================== */}

        <div className="mt-4 flex flex-wrap items-center gap-x-6 gap-y-2 px-1">

          <Legend
            color="#22c55e"
            label="Normal Operation"
          />

          <Legend
            color="#f59e0b"
            label="High Traffic / Cleaning Needed"
          />

          <Legend
            color="#ef4444"
            label="Active Micro-Leak"
            pulse
          />

          <div className="ml-auto flex items-center gap-2 text-[10px] text-slate-600">

            <span
              className={`h-1.5 w-1.5 rounded-full ${
                backendOnline
                  ? "bg-emerald-400"
                  : "bg-slate-600"
              }`}
            />

            {backendOnline
              ? "LIVE TELEMETRY"
              : "DEMO TELEMETRY"}

          </div>

        </div>

      </div>


      {/* ================================================== */}
      {/* SIMULATION CONTROL BAR */}
      {/* ================================================== */}

      <div className="border-t border-[#1f2937] bg-[#0d1421] px-5 py-4">

        <div className="mb-3 flex items-center gap-2">

          <Sparkles
            size={14}
            className="text-[#38bdf8]"
          />

          <span className="text-[10px] font-semibold uppercase tracking-[0.18em] text-slate-500">
            Simulation Controls
          </span>

        </div>


        <div className="grid grid-cols-1 gap-2 sm:grid-cols-3">

          <SimulationButton
            icon={
              <AlertTriangle
                size={16}
              />
            }
            label="Inject Solenoid Leak"
            loading={
              actionLoading ===
              "INJECT_LEAK"
            }
            variant="danger"
            onClick={() =>
              runSimulation(
                "INJECT_LEAK"
              )
            }
          />

          <SimulationButton
            icon={
              <Plane size={16} />
            }
            label="Simulate Flight Landing Rush"
            loading={
              actionLoading ===
              "FLIGHT_RUSH"
            }
            variant="warning"
            onClick={() =>
              runSimulation(
                "FLIGHT_RUSH"
              )
            }
          />

          <SimulationButton
            icon={
              <RotateCcw
                size={16}
              />
            }
            label="Reset All Sensors"
            loading={
              actionLoading === "RESET"
            }
            variant="default"
            onClick={() =>
              runSimulation("RESET")
            }
          />

        </div>

      </div>

      {selectedFixture && (
        <FixtureModal
          fixture={selectedFixture}
          onClose={() => setSelectedFixture(null)}
        />
      )}

    </section>
  );
}


// ============================================================
// FLOOR ZONE
// ============================================================

function FloorZone({
  label,
  title,
  subtitle,
  icon,
  children,
}: {
  label: string;
  title: string;
  subtitle: string;
  icon: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <div className="rounded-xl border border-[#1f2937] bg-[#111827]/70 p-4">

      <div className="mb-4 flex items-center justify-between">

        <div className="flex items-center gap-3">

          <div className="rounded-lg border border-[#1f2937] bg-[#0b0f19] p-2 text-[#38bdf8]">
            {icon}
          </div>

          <div>
            <div className="flex items-center gap-2">

              <span className="text-[9px] font-semibold uppercase tracking-[0.18em] text-slate-600">
                {label}
              </span>

              <span className="h-1 w-1 rounded-full bg-slate-700" />

              <span className="text-[9px] uppercase tracking-[0.12em] text-slate-600">
                {subtitle}
              </span>

            </div>

            <h3 className="mt-0.5 text-sm font-semibold text-slate-200">
              {title}
            </h3>
          </div>

        </div>

      </div>

      {children}

    </div>
  );
}


// ============================================================
// FIXTURE BOX
// ============================================================

function FixtureBox({
  fixture,
  onClick,
}: {
  fixture: Fixture;
  onClick: () => void;
}) {
  const config =
    STATUS_CONFIG[
      fixture.status
    ];

  return (
    <button
      onClick={onClick}
      className={`
        group relative
        min-h-[112px]
        rounded-xl
        border
        ${config.border}
        ${config.glow}
        ${config.bg}
        p-4
        text-left
        transition-all
        duration-200
        hover:-translate-y-0.5
        hover:brightness-110
        focus:outline-none
        focus:ring-2
        focus:ring-[#38bdf8]/50
        ${
          fixture.status === "LEAK"
            ? "animate-[pulse_2s_ease-in-out_infinite]"
            : ""
        }
      `}
    >

      {/* Status indicator */}

      <div className="absolute right-3 top-3">

        <span
          className={`
            block h-2 w-2 rounded-full
            ${config.dot}
            ${
              fixture.status ===
              "LEAK"
                ? "animate-pulse"
                : ""
            }
          `}
        />

      </div>


      {/* Icon */}

      <div
        className={`
          mb-3 flex h-8 w-8
          items-center justify-center
          rounded-lg
          bg-[#0b0f19]
          ${config.text}
        `}
      >
        <FixtureIcon
          type={fixture.type}
          size={16}
        />
      </div>


      {/* Name */}

      <p className="text-sm font-semibold text-white">
        {fixture.fixture_name}
      </p>

      <p className="mt-0.5 font-mono text-[9px] text-slate-600">
        {fixture.fixture_id}
      </p>


      {/* Telemetry */}

      <div className="mt-3 flex items-center justify-between">

        <div>
          <p className="font-mono text-sm font-semibold text-slate-200">
            {fixture.water_flow_lpm.toFixed(2)}
            <span className="ml-1 text-[9px] font-normal text-slate-600">
              LPM
            </span>
          </p>
        </div>

        <div
          className={`text-[9px] font-semibold uppercase tracking-wider ${config.text}`}
        >
          {fixture.status ===
          "LEAK"
            ? "LEAK"
            : fixture.status ===
              "HYGIENE_WARNING"
            ? "CLEAN"
            : "OK"}
        </div>

      </div>


      {/* Hover indicator */}

      <div className="absolute bottom-3 right-3 opacity-0 transition group-hover:opacity-100">

        <ChevronRight
          size={13}
          className="text-slate-500"
        />

      </div>

    </button>
  );
}


// ============================================================
// FIXTURE DETAIL MODAL
// ============================================================

function FixtureModal({
  fixture,
  onClose,
}: {
  fixture: Fixture;
  onClose: () => void;
}) {
  const config =
    STATUS_CONFIG[
      fixture.status
    ];

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4 backdrop-blur-sm"
      onClick={onClose}
    >

      <div
        className="w-full max-w-lg overflow-hidden rounded-2xl border border-[#1f2937] bg-[#111827] shadow-2xl shadow-black/50"
        onClick={(event) =>
          event.stopPropagation()
        }
      >

        {/* Modal header */}

        <div className="flex items-start justify-between border-b border-[#1f2937] p-5">

          <div className="flex items-center gap-3">

            <div
              className={`
                rounded-lg
                border
                ${config.border}
                ${config.bg}
                p-2.5
                ${config.text}
              `}
            >
              <FixtureIcon
                type={fixture.type}
                size={20}
              />
            </div>

            <div>

              <p className="text-xs uppercase tracking-[0.16em] text-slate-500">
                Live Fixture Telemetry
              </p>

              <h2 className="mt-1 text-lg font-semibold text-white">
                {fixture.fixture_name}
              </h2>

              <p className="font-mono text-[10px] text-slate-600">
                {fixture.fixture_id}
              </p>

            </div>

          </div>


          <button
            onClick={onClose}
            className="rounded-lg p-2 text-slate-500 transition hover:bg-[#1f2937] hover:text-white"
            aria-label="Close"
          >
            <X size={18} />
          </button>

        </div>


        {/* Status */}

        <div className="p-5">

          <div
            className={`
              flex items-center justify-between
              rounded-xl
              border
              ${config.border}
              ${config.bg}
              px-4 py-3
            `}
          >

            <div className="flex items-center gap-2">

              <span
                className={`
                  h-2 w-2 rounded-full
                  ${config.dot}
                  ${
                    fixture.status ===
                    "LEAK"
                      ? "animate-pulse"
                      : ""
                  }
                `}
              />

              <span
                className={`text-xs font-semibold ${config.text}`}
              >
                {config.label}
              </span>

            </div>

            <span className="text-[10px] uppercase tracking-wider text-slate-600">
              {fixture.type}
            </span>

          </div>


          {/* Telemetry grid */}

          <div className="mt-4 grid grid-cols-2 gap-3">

            <TelemetryCard
              icon={
                <Droplets
                  size={16}
                />
              }
              label="Water Flow"
              value={`${fixture.water_flow_lpm.toFixed(
                2
              )} LPM`}
            />

            <TelemetryCard
              icon={
                <Users size={16} />
              }
              label="Occupancy"
              value={`${fixture.occupancy_count_10m}`}
              suffix="10m"
            />

            <TelemetryCard
              icon={
                <Gauge size={16} />
              }
              label="Pressure"
              value={`${fixture.pressure_psi.toFixed(
                1
              )} PSI`}
            />

            <TelemetryCard
              icon={
                <ShieldCheckIcon />
              }
              label="Hygiene Score"
              value={`${fixture.hygiene_score.toFixed(
                0
              )}/100`}
            />

          </div>


          {/* Last cleaned */}

          <div className="mt-3 flex items-center justify-between rounded-xl border border-[#1f2937] bg-[#0b0f19] px-4 py-3">

            <span className="text-xs text-slate-500">
              Last Cleaned
            </span>

            <span className="text-xs font-medium text-slate-300">
              {fixture.last_cleaned ??
                "Recently"}
            </span>

          </div>


          {/* Timestamp */}

          {fixture.timestamp && (
            <p className="mt-4 text-center font-mono text-[9px] text-slate-700">
              Telemetry received{" "}
              {new Date(
                fixture.timestamp
              ).toLocaleTimeString()}
            </p>
          )}

        </div>

      </div>

    </div>
  );
}


// ============================================================
// TELEMETRY CARD
// ============================================================

function TelemetryCard({
  icon,
  label,
  value,
  suffix,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
  suffix?: string;
}) {
  return (
    <div className="rounded-xl border border-[#1f2937] bg-[#0b0f19] p-4">

      <div className="flex items-center gap-2 text-[#38bdf8]">
        {icon}

        <span className="text-[10px] uppercase tracking-wider text-slate-600">
          {label}
        </span>
      </div>

      <div className="mt-3">

        <span className="font-mono text-lg font-semibold text-white">
          {value}
        </span>

        {suffix && (
          <span className="ml-1 text-[9px] text-slate-600">
            {suffix}
          </span>
        )}

      </div>

    </div>
  );
}


// ============================================================
// STATUS COUNTER
// ============================================================

function StatusCounter({
  color,
  label,
  value,
}: {
  color: "green" | "amber" | "red";
  label: string;
  value: number;
}) {
  const styles = {
    green:
      "text-[#22c55e] bg-[#22c55e]/5 border-[#22c55e]/20",
    amber:
      "text-[#f59e0b] bg-[#f59e0b]/5 border-[#f59e0b]/20",
    red:
      "text-[#ef4444] bg-[#ef4444]/5 border-[#ef4444]/20",
  };

  const dots = {
    green: "bg-[#22c55e]",
    amber: "bg-[#f59e0b]",
    red: "bg-[#ef4444]",
  };

  return (
    <div
      className={`flex items-center gap-2 rounded-lg border px-2.5 py-1.5 ${styles[color]}`}
    >

      <span
        className={`h-1.5 w-1.5 rounded-full ${dots[color]}`}
      />

      <span className="text-[10px] font-medium">
        {value}
      </span>

      <span className="hidden text-[9px] text-slate-600 sm:inline">
        {label}
      </span>

    </div>
  );
}


// ============================================================
// LEGEND
// ============================================================

function Legend({
  color,
  label,
  pulse = false,
}: {
  color: string;
  label: string;
  pulse?: boolean;
}) {
  return (
    <div className="flex items-center gap-2">

      <span
        className={`h-2 w-2 rounded-full ${
          pulse ? "animate-pulse" : ""
        }`}
        style={{
          backgroundColor: color,
          boxShadow: `0 0 8px ${color}`,
        }}
      />

      <span className="text-[10px] text-slate-500">
        {label}
      </span>

    </div>
  );
}


// ============================================================
// SIMULATION BUTTON
// ============================================================

function SimulationButton({
  icon,
  label,
  loading,
  variant,
  onClick,
}: {
  icon: React.ReactNode;
  label: string;
  loading: boolean;
  variant:
    | "danger"
    | "warning"
    | "default";
  onClick: () => void;
}) {
  const styles = {
    danger:
      "border-red-500/20 bg-red-500/5 text-red-400 hover:border-red-500/40 hover:bg-red-500/10",

    warning:
      "border-amber-500/20 bg-amber-500/5 text-amber-400 hover:border-amber-500/40 hover:bg-amber-500/10",

    default:
      "border-[#1f2937] bg-[#111827] text-slate-300 hover:border-sky-500/30 hover:bg-[#1f2937]",
  };

  return (
    <button
      onClick={onClick}
      disabled={loading}
      className={`
        flex items-center justify-center gap-2
        rounded-lg
        border
        px-4 py-3
        text-xs font-semibold
        transition
        disabled:cursor-not-allowed
        disabled:opacity-50
        ${styles[variant]}
      `}
    >

      {loading ? (
        <span className="h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent" />
      ) : (
        icon
      )}

      {label}

    </button>
  );
}


// ============================================================
// SMALL SHIELD ICON
// ============================================================

function ShieldCheckIcon() {
  return (
    <CheckCircle2 size={16} />
  );
}