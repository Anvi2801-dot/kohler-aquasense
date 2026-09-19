"use client";

import { useEffect, useState } from "react";
import {
  Activity,
  Droplets,
  IndianRupee,
  Gauge,
  Wifi,
  WifiOff,
} from "lucide-react";

const API_URL = "http://localhost:8000";

type KPIData = {
  total_water_saved_liters: number;
  cost_saved_inr: number;
  active_leaks_count: number;
  system_uptime_percent: number;
};

function MetricCard({
  icon,
  label,
  value,
  subtitle,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
  subtitle: string;
}) {
  return (
    <div className="rounded-xl border border-[#1f2937] bg-[#111827] p-5 shadow-lg shadow-black/10 transition hover:border-sky-500/30">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs font-medium uppercase tracking-[0.16em] text-slate-500">
            {label}
          </p>

          <div className="mt-3 text-2xl font-semibold tracking-tight text-white">
            {value}
          </div>

          <p className="mt-1 text-xs text-slate-500">
            {subtitle}
          </p>
        </div>

        <div className="rounded-lg border border-[#1f2937] bg-[#0b0f19] p-2.5 text-sky-400">
          {icon}
        </div>
      </div>
    </div>
  );
}

export default function Header() {
  const [kpis, setKpis] = useState<KPIData | null>(null);
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    let mounted = true;

    const fetchKPIs = async () => {
      try {
        const response = await fetch(
          `${API_URL}/api/kpis`,
          {
            cache: "no-store",
          }
        );

        if (!response.ok) {
          throw new Error("Failed to fetch KPIs");
        }

        const data: KPIData = await response.json();

        if (mounted) {
          setKpis(data);
          setConnected(true);
        }
      } catch (error) {
        console.error("KPI API error:", error);

        if (mounted) {
          setConnected(false);
        }
      }
    };

    fetchKPIs();

    const interval = setInterval(fetchKPIs, 5000);

    return () => {
      mounted = false;
      clearInterval(interval);
    };
  }, []);

  const waterSaved = kpis?.total_water_saved_liters ?? 1248;
  const costSaved = kpis?.cost_saved_inr ?? 137.28;
  const uptime = kpis?.system_uptime_percent ?? 99.7;

  return (
    <header className="w-full border-b border-[#1f2937] bg-[#0b0f19]">
      {/* Top Navigation */}
      <div className="mx-auto max-w-[1600px] px-6 lg:px-8">
        <div className="flex min-h-[76px] items-center justify-between gap-6">

          {/* Brand */}
          <div className="flex items-center gap-4">
            {/* Kohler-style wordmark block */}
            <div className="flex h-10 w-24 items-center justify-center border border-slate-600 bg-[#111827]">
              <span className="text-sm font-bold tracking-[0.22em] text-white">
                KOHLER
              </span>
            </div>

            <div className="hidden border-l border-[#1f2937] pl-4 sm:block">
              <h1 className="text-sm font-semibold tracking-wide text-white">
                AquaSense OS
              </h1>

              <p className="mt-0.5 text-[11px] uppercase tracking-[0.14em] text-slate-500">
                PNQ NITB — Departure Zone 3
              </p>
            </div>
          </div>

          {/* System Status */}
          <div className="flex items-center gap-4">
            <div className="hidden items-center gap-2 text-xs text-slate-500 md:flex">
              <Activity size={14} />
              <span>LIVE TELEMETRY</span>
            </div>

            <div
              className={`flex items-center gap-2 rounded-full border px-3 py-1.5 text-xs font-medium ${
                connected
                  ? "border-emerald-500/20 bg-emerald-500/10 text-emerald-400"
                  : "border-red-500/20 bg-red-500/10 text-red-400"
              }`}
            >
              {connected ? (
                <Wifi size={13} />
              ) : (
                <WifiOff size={13} />
              )}

              <span>
                {connected ? "System Online" : "Backend Offline"}
              </span>

              <span
                className={`h-1.5 w-1.5 rounded-full ${
                  connected
                    ? "animate-pulse bg-emerald-400"
                    : "bg-red-400"
                }`}
              />
            </div>
          </div>
        </div>
      </div>

      {/* KPI Strip */}
      <div className="border-t border-[#1f2937] bg-[#0d1421]">
        <div className="mx-auto grid max-w-[1600px] grid-cols-1 gap-3 px-6 py-4 md:grid-cols-3 lg:px-8">

          <MetricCard
            icon={<Droplets size={19} />}
            label="Water Saved"
            value={`${waterSaved.toLocaleString()} L`}
            subtitle="+12.4% vs baseline"
          />

          <MetricCard
            icon={<IndianRupee size={19} />}
            label="Utility Cost Saved"
            value={`₹${costSaved.toFixed(2)}`}
            subtitle="Est. PMC bulk utility savings"
          />

          <MetricCard
            icon={<Gauge size={19} />}
            label="Active Fleet Uptime"
            value={`${uptime.toFixed(1)}%`}
            subtitle="9 Connected Fixtures"
          />
        </div>
      </div>
    </header>
  );
}