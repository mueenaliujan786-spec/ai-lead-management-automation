import { useEffect, useState } from "react";
import { listDrafts } from "./api";
import DraftDetail from "./DraftDetail";

const TABS = [
  { key: "pending", label: "Pending" },
  { key: "approved", label: "Approved" },
  { key: "sent", label: "Sent" },
  { key: "rejected", label: "Rejected" },
  { key: "", label: "All" },
];

const PRIORITY_STYLES = {
  High: "bg-red-100 text-red-700",
  Medium: "bg-amber-100 text-amber-700",
  Low: "bg-slate-100 text-slate-600",
};

const STATUS_STYLES = {
  pending: "bg-indigo-100 text-indigo-700",
  approved: "bg-emerald-100 text-emerald-700",
  sent: "bg-sky-100 text-sky-700",
  rejected: "bg-slate-200 text-slate-600",
};

function Badge({ text, styles }) {
  if (!text) return <span className="text-slate-400">-</span>;
  const style = styles[text] || "bg-slate-100 text-slate-600";
  return (
    <span className={`inline-block rounded-full px-2.5 py-0.5 text-xs font-medium ${style}`}>
      {text}
    </span>
  );
}

export default function DraftList() {
  const [tab, setTab] = useState("pending");
  const [reloadKey, setReloadKey] = useState(0);
  const [selectedId, setSelectedId] = useState(null);
  const [notice, setNotice] = useState("");
  const [state, setState] = useState({ loading: true, error: "", drafts: [] });

  useEffect(() => {
    let active = true;
    listDrafts(tab)
      .then((drafts) => {
        if (active) setState({ loading: false, error: "", drafts });
      })
      .catch((err) => {
        if (active) setState({ loading: false, error: err.message, drafts: [] });
      });
    return () => {
      active = false;
    };
  }, [tab, reloadKey]);

  function selectTab(key) {
    setNotice("");
    setState({ loading: true, error: "", drafts: [] });
    setTab(key);
  }

  function handleChanged(message) {
    setNotice(message);
    setState({ loading: true, error: "", drafts: [] });
    setReloadKey((k) => k + 1);
  }

  const { loading, error, drafts } = state;

  return (
    <section>
      <div className="flex flex-wrap gap-2">
        {TABS.map((t) => (
          <button
            key={t.label}
            onClick={() => selectTab(t.key)}
            className={`rounded-full px-4 py-1.5 text-sm font-medium ${
              tab === t.key
                ? "bg-indigo-600 text-white"
                : "bg-white text-slate-600 shadow-sm hover:bg-slate-100"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {notice && (
        <p role="status" className="mt-4 rounded-lg bg-emerald-50 px-4 py-2 text-sm text-emerald-800">
          {notice}
        </p>
      )}

      <div className="mt-4 overflow-x-auto rounded-xl bg-white shadow-sm">
        {loading && <p className="p-6 text-slate-500">Loading drafts...</p>}
        {error && (
          <p role="alert" className="p-6 text-red-700">
            {error}
          </p>
        )}
        {!loading && !error && drafts.length === 0 && (
          <p className="p-6 text-slate-500">No drafts in this view.</p>
        )}
        {!loading && !error && drafts.length > 0 && (
          <table className="min-w-full text-left text-sm">
            <thead className="border-b border-slate-200 text-slate-500">
              <tr>
                <th className="px-4 py-3 font-medium">Lead</th>
                <th className="px-4 py-3 font-medium">Subject</th>
                <th className="px-4 py-3 font-medium">Category</th>
                <th className="px-4 py-3 font-medium">Priority</th>
                <th className="px-4 py-3 font-medium">Status</th>
                <th className="px-4 py-3 font-medium">Created</th>
              </tr>
            </thead>
            <tbody>
              {drafts.map((d) => (
                <tr
                  key={d.draft_id}
                  tabIndex={0}
                  onClick={() => setSelectedId(d.draft_id)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") setSelectedId(d.draft_id);
                  }}
                  className="cursor-pointer border-b border-slate-100 last:border-0 hover:bg-slate-50 focus:bg-slate-50 focus:outline-none"
                >
                  <td className="px-4 py-3">
                    <div className="font-medium text-slate-800">{d.lead_name}</div>
                    <div className="text-slate-500">{d.company || d.lead_email}</div>
                  </td>
                  <td className="px-4 py-3 text-slate-700">{d.subject}</td>
                  <td className="px-4 py-3 text-slate-700">{d.category || "-"}</td>
                  <td className="px-4 py-3">
                    <Badge text={d.priority} styles={PRIORITY_STYLES} />
                  </td>
                  <td className="px-4 py-3">
                    <Badge text={d.status} styles={STATUS_STYLES} />
                  </td>
                  <td className="px-4 py-3 text-slate-500">
                    {new Date(d.created_at).toLocaleString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {selectedId && (
        <DraftDetail
          key={selectedId}
          draftId={selectedId}
          onClose={() => setSelectedId(null)}
          onChanged={handleChanged}
        />
      )}
    </section>
  );
}
