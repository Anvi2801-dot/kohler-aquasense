"use client";

import { useCallback, useEffect, useState } from "react";
import {
  AlertTriangle,
  CheckCircle2,
  Clock3,
  Loader2,
  MapPin,
  Package,
  ShieldCheck,
  Sparkles,
  Wrench,
  XCircle,
} from "lucide-react";

const API_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

type Priority = "CRITICAL" | "HIGH" | "ROUTINE";

interface WorkOrder {
  ticket_id: string;
  fixture_id: string;
  fixture_location?: string;
  fixture_name?: string;
  priority: Priority;
  root_cause: string;
  recommended_action: string;
  kohler_part_number: string;
  kohler_part_name?: string;
  water_saved_lpm?: number;
  status?: string;
  created_at?: string;
}

interface DispatchResponse {
  work_orders?: WorkOrder[];
  tickets?: WorkOrder[];
}

const priorityStyles: Record<
  Priority,
  {
    badge: string;
    icon: string;
  }
> = {
  CRITICAL: {
    badge: "border-red-500/30 bg-red-500/10 text-red-400",
    icon: "text-red-400",
  },
  HIGH: {
    badge: "border-amber-500/30 bg-amber-500/10 text-amber-400",
    icon: "text-amber-400",
  },
  ROUTINE: {
    badge: "border-blue-500/30 bg-blue-500/10 text-blue-400",
    icon: "text-blue-400",
  },
};

function normalizeWorkOrders(data: DispatchResponse | WorkOrder[]): WorkOrder[] {
  if (Array.isArray(data)) {
    return data;
  }

  return data.work_orders || data.tickets || [];
}

function formatFixtureName(order: WorkOrder) {
  if (order.fixture_location && order.fixture_name) {
    return `${order.fixture_location} - ${order.fixture_name}`;
  }

  if (order.fixture_location) {
    return order.fixture_location;
  }

  return order.fixture_id;
}

export default function TechnicianPortal() {
  const [workOrders, setWorkOrders] = useState<WorkOrder[]>([]);
  const [loading, setLoading] = useState(true);
  const [completingTicket, setCompletingTicket] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const fetchWorkOrders = useCallback(async () => {
    try {
      setError(null);

      const response = await fetch(`${API_URL}/api/dispatch`, {
        method: "GET",
        cache: "no-store",
      });

      if (!response.ok) {
        throw new Error(`Dispatch API returned ${response.status}`);
      }

      const data: DispatchResponse | WorkOrder[] = await response.json();
      setWorkOrders(normalizeWorkOrders(data));
    } catch (err) {
      console.error("Failed to fetch work orders:", err);
      setError("Unable to connect to the dispatch system.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchWorkOrders();

    // Keep the technician queue synchronized with the backend
    const interval = setInterval(fetchWorkOrders, 5000);

    return () => clearInterval(interval);
  }, [fetchWorkOrders]);

  const completeWorkOrder = async (order: WorkOrder) => {
    try {
      setCompletingTicket(order.ticket_id);
      setError(null);

      const response = await fetch(`${API_URL}/api/dispatch/complete`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          ticket_id: order.ticket_id,
          fixture_id: order.fixture_id,
        }),
      });

      if (!response.ok) {
        throw new Error(`Completion API returned ${response.status}`);
      }

      // Remove the ticket immediately from the active queue
      setWorkOrders((current) =>
        current.filter((item) => item.ticket_id !== order.ticket_id)
      );
    } catch (err) {
      console.error("Failed to complete work order:", err);
      setError(`Could not complete ${order.ticket_id}. Please try again.`);
    } finally {
      setCompletingTicket(null);
    }
  };

  return (
    <section className="space-y-6">
      {/* Portal Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div className="flex items-center gap-2">
            <Wrench className="h-5 w-5 text-orange-400" />

            <span className="text-xs font-semibold uppercase tracking-[0.18em] text-orange-400">
              Field Technician Portal
            </span>
          </div>

          <h2 className="mt-2 text-2xl font-semibold tracking-tight text-white">
            Marcus
          </h2>

          <p className="mt-1 text-sm text-slate-400">
            Active maintenance queue for Airport Terminal Restroom
          </p>
        </div>

        <div className="flex items-center gap-2 rounded-xl border border-slate-800 bg-slate-900/70 px-4 py-2.5">
          <div
            className={`h-2 w-2 rounded-full ${
              error ? "bg-red-400" : "bg-emerald-400"
            }`}
          />

          <span className="text-xs font-medium text-slate-300">
            {error ? "Dispatch Offline" : "Dispatch System Online"}
          </span>
        </div>
      </div>

      {/* Error Banner */}
      {error && (
        <div className="flex items-center gap-3 rounded-xl border border-red-500/20 bg-red-500/5 px-4 py-3 text-sm text-red-300">
          <XCircle className="h-4 w-4 shrink-0" />
          <span>{error}</span>

          <button
            onClick={fetchWorkOrders}
            className="ml-auto rounded-lg border border-red-500/20 px-3 py-1.5 text-xs font-medium transition hover:bg-red-500/10"
          >
            Retry
          </button>
        </div>
      )}

      {/* Loading State */}
      {loading ? (
        <div className="flex min-h-[320px] items-center justify-center rounded-2xl border border-slate-800 bg-slate-950/60">
          <div className="flex flex-col items-center gap-3">
            <Loader2 className="h-7 w-7 animate-spin text-orange-400" />

            <p className="text-sm text-slate-400">
              Loading active work orders...
            </p>
          </div>
        </div>
      ) : workOrders.length === 0 ? (
        /* Empty Queue State */
        <div className="flex min-h-[360px] flex-col items-center justify-center rounded-2xl border border-emerald-500/20 bg-emerald-500/[0.03] px-6 text-center">
          <div className="mb-5 flex h-16 w-16 items-center justify-center rounded-full border border-emerald-500/20 bg-emerald-500/10">
            <CheckCircle2 className="h-8 w-8 text-emerald-400" />
          </div>

          <h3 className="text-lg font-semibold text-white">
            All fixtures operating within normal parameters
          </h3>

          <p className="mt-2 max-w-md text-sm leading-6 text-slate-500">
            No active maintenance tickets require technician attention.
            AquaSense OS is continuously monitoring the facility.
          </p>

          <div className="mt-6 flex items-center gap-2 rounded-lg border border-slate-800 bg-slate-900/60 px-4 py-2.5 text-xs text-slate-400">
            <ShieldCheck className="h-4 w-4 text-emerald-400" />
            System monitoring active
          </div>
        </div>
      ) : (
        /* Active Work Orders */
        <div className="space-y-4">
          {workOrders.map((order) => {
            const priority =
              priorityStyles[order.priority] || priorityStyles.ROUTINE;

            const isCompleting = completingTicket === order.ticket_id;

            return (
              <article
                key={order.ticket_id}
                className="group overflow-hidden rounded-2xl border border-slate-800 bg-slate-950/70 transition hover:border-slate-700"
              >
                {/* Header Section */}
                <div className="flex flex-col gap-4 border-b border-slate-800/80 p-5 sm:flex-row sm:items-start sm:justify-between">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="rounded-md border border-slate-700 bg-slate-900 px-2.5 py-1 text-xs font-mono font-semibold text-slate-300">
                      #{order.ticket_id.replace("#", "")}
                    </span>

                    <span
                      className={`inline-flex items-center gap-1.5 rounded-md border px-2.5 py-1 text-[10px] font-bold tracking-wider ${priority.badge}`}
                    >
                      <AlertTriangle
                        className={`h-3 w-3 ${priority.icon}`}
                      />
                      {order.priority}
                    </span>
                  </div>

                  {order.created_at && (
                    <div className="flex items-center gap-1.5 text-xs text-slate-500">
                      <Clock3 className="h-3.5 w-3.5" />
                      {new Date(order.created_at).toLocaleTimeString([], {
                        hour: "2-digit",
                        minute: "2-digit",
                      })}
                    </div>
                  )}
                </div>

                {/* Content Section */}
                <div className="grid gap-6 p-5 lg:grid-cols-[1fr_1fr]">
                  {/* Fixture & Parts */}
                  <div>
                    <div className="mb-4 flex items-center gap-2">
                      <MapPin className="h-4 w-4 text-orange-400" />

                      <span className="text-[10px] font-semibold uppercase tracking-[0.16em] text-slate-500">
                        Fixture Location
                      </span>
                    </div>

                    <h3 className="text-base font-semibold text-white">
                      {formatFixtureName(order)}
                    </h3>

                    <p className="mt-1 font-mono text-xs text-slate-500">
                      {order.fixture_id}
                    </p>

                    <div className="mt-5 rounded-xl border border-orange-500/20 bg-orange-500/[0.04] p-4">
                      <div className="flex items-center gap-2 text-[10px] font-semibold uppercase tracking-[0.15em] text-orange-400">
                        <Package className="h-3.5 w-3.5" />
                        Kohler Replacement Part
                      </div>

                      <p className="mt-2 text-sm font-bold text-white">
                        {order.kohler_part_name ||
                          "Replacement Component"}{" "}
                        <span className="font-mono text-orange-300">
                          #{order.kohler_part_number}
                        </span>
                      </p>
                    </div>
                  </div>

                  {/* AI Root Cause & Recommendation */}
                  <div className="space-y-4">
                    <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-4">
                      <div className="mb-2 flex items-center gap-2">
                        <Sparkles className="h-4 w-4 text-purple-400" />

                        <span className="text-[10px] font-semibold uppercase tracking-[0.15em] text-purple-400">
                          LLM Root Cause Analysis
                        </span>
                      </div>

                      <p className="text-sm leading-6 text-slate-300">
                        {order.root_cause ||
                          "AI diagnostic analysis is unavailable."}
                      </p>
                    </div>

                    <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-4">
                      <div className="mb-2 flex items-center gap-2">
                        <Wrench className="h-4 w-4 text-blue-400" />

                        <span className="text-[10px] font-semibold uppercase tracking-[0.15em] text-blue-400">
                          Recommended Repair Action
                        </span>
                      </div>

                      <p className="text-sm leading-6 text-slate-300">
                        {order.recommended_action ||
                          "Follow standard Kohler maintenance procedure."}
                      </p>
                    </div>
                  </div>
                </div>

                {/* Footer Controls */}
                <div className="flex flex-col gap-4 border-t border-slate-800/80 bg-slate-900/30 p-5 sm:flex-row sm:items-center sm:justify-between">
                  <div className="flex items-center gap-4">
                    {typeof order.water_saved_lpm === "number" && (
                      <div>
                        <p className="text-[9px] uppercase tracking-wider text-slate-500">
                          Est. Water Recovery
                        </p>

                        <p className="mt-1 text-sm font-semibold text-emerald-400">
                          {order.water_saved_lpm.toFixed(1)} L/hr
                        </p>
                      </div>
                    )}

                    <div className="h-7 w-px bg-slate-800" />

                    <div>
                      <p className="text-[9px] uppercase tracking-wider text-slate-500">
                        Assigned Technician
                      </p>

                      <p className="mt-1 text-sm font-medium text-slate-300">
                        Marcus
                      </p>
                    </div>
                  </div>

                  <button
                    onClick={() => completeWorkOrder(order)}
                    disabled={isCompleting}
                    className="inline-flex items-center justify-center gap-2 rounded-xl bg-orange-500 px-5 py-2.5 text-sm font-semibold text-white shadow-lg shadow-orange-500/10 transition hover:bg-orange-400 disabled:cursor-not-allowed disabled:opacity-60"
                  >
                    {isCompleting ? (
                      <>
                        <Loader2 className="h-4 w-4 animate-spin" />
                        Completing...
                      </>
                    ) : (
                      <>
                        <CheckCircle2 className="h-4 w-4" />
                        Acknowledge &amp; Complete
                      </>
                    )}
                  </button>
                </div>
              </article>
            );
          })}
        </div>
      )}
    </section>
  );
}