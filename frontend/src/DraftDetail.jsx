import { useEffect, useState } from "react";
import { editDraft, getDraft, reviewDraft } from "./api";

function Info({ label, children }) {
  return (
    <div>
      <dt className="text-xs font-medium uppercase tracking-wide text-slate-500">{label}</dt>
      <dd className="mt-0.5 text-sm text-slate-800">{children || "-"}</dd>
    </div>
  );
}

export default function DraftDetail({ draftId, onClose, onChanged }) {
  const [detail, setDetail] = useState(null);
  const [subject, setSubject] = useState("");
  const [body, setBody] = useState("");
  const [loadError, setLoadError] = useState("");
  const [actionError, setActionError] = useState("");
  const [busy, setBusy] = useState(false);
  const [confirming, setConfirming] = useState(null);

  useEffect(() => {
    let active = true;
    getDraft(draftId)
      .then((d) => {
        if (!active) return;
        setDetail(d);
        setSubject(d.subject);
        setBody(d.body);
      })
      .catch((err) => {
        if (active) setLoadError(err.message);
      });
    return () => {
      active = false;
    };
  }, [draftId]);

  useEffect(() => {
    const onKey = (event) => {
      if (event.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  const pending = detail?.status === "pending";
  const dirty = detail !== null && (subject !== detail.subject || body !== detail.body);
  const invalid = subject.trim() === "" || body.trim() === "";

  async function save() {
    setBusy(true);
    setActionError("");
    try {
      const updated = await editDraft(draftId, subject, body);
      setDetail(updated);
      setSubject(updated.subject);
      setBody(updated.body);
    } catch (err) {
      setActionError(err.message);
    } finally {
      setBusy(false);
    }
  }

  async function review(decision) {
    setBusy(true);
    setActionError("");
    try {
      // Unsaved edits are saved first, so the approved email matches the screen.
      if (dirty) await editDraft(draftId, subject, body);
      await reviewDraft(draftId, decision);
      onChanged(
        decision === "approved"
          ? `Approved. The email to ${detail.lead_email} will be sent shortly.`
          : "Draft rejected. No email will be sent."
      );
      onClose();
    } catch (err) {
      setActionError(err.message);
      setConfirming(null);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div
      className="fixed inset-0 z-10 flex items-start justify-center overflow-y-auto bg-slate-900/40 p-4"
      onMouseDown={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-label="Draft details"
        className="my-8 w-full max-w-2xl rounded-xl bg-white p-6 shadow-xl"
      >
        <div className="flex items-start justify-between">
          <h3 className="text-lg font-semibold text-slate-800">Review draft</h3>
          <button
            onClick={onClose}
            className="rounded-lg px-2 py-1 text-slate-500 hover:bg-slate-100"
            aria-label="Close"
          >
            X
          </button>
        </div>

        {loadError && (
          <p role="alert" className="mt-4 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">
            {loadError}
          </p>
        )}
        {!detail && !loadError && <p className="mt-4 text-slate-500">Loading...</p>}

        {detail && (
          <>
            <dl className="mt-4 grid grid-cols-2 gap-4 rounded-lg bg-slate-50 p-4">
              <Info label="Lead">{detail.lead_name}</Info>
              <Info label="Email">{detail.lead_email}</Info>
              <Info label="Company">{detail.company}</Info>
              <Info label="Service interest">{detail.service_interest}</Info>
              <div className="col-span-2">
                <Info label="Their message">
                  <span className="whitespace-pre-wrap">{detail.lead_message}</span>
                </Info>
              </div>
            </dl>

            <h4 className="mt-6 text-sm font-semibold text-slate-700">AI analysis</h4>
            <p className="text-xs text-slate-500">A recommendation, not a verified fact.</p>
            <dl className="mt-2 grid grid-cols-2 gap-4 rounded-lg bg-indigo-50 p-4">
              <Info label="Category">{detail.category}</Info>
              <Info label="Priority">{detail.priority}</Info>
              <div className="col-span-2">
                <Info label="Intent">{detail.intent}</Info>
              </div>
              <div className="col-span-2">
                <Info label="Summary">{detail.summary}</Info>
              </div>
              <div className="col-span-2">
                <Info label="Recommended action">{detail.recommended_action}</Info>
              </div>
            </dl>

            <h4 className="mt-6 text-sm font-semibold text-slate-700">
              Email draft{" "}
              <span className="font-normal text-slate-500">({detail.status})</span>
            </h4>
            <label className="mt-2 block text-sm font-medium text-slate-700">
              Subject
              <input
                value={subject}
                maxLength={200}
                disabled={!pending || busy}
                onChange={(e) => setSubject(e.target.value)}
                className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-slate-900 disabled:bg-slate-100"
              />
            </label>
            <label className="mt-3 block text-sm font-medium text-slate-700">
              Message
              <textarea
                value={body}
                rows={9}
                maxLength={5000}
                disabled={!pending || busy}
                onChange={(e) => setBody(e.target.value)}
                className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-slate-900 disabled:bg-slate-100"
              />
            </label>

            {actionError && (
              <p role="alert" className="mt-4 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">
                {actionError}
              </p>
            )}

            {!pending && (
              <p className="mt-4 text-sm text-slate-500">
                This draft is {detail.status} and can no longer be changed.
              </p>
            )}

            {pending && !confirming && (
              <div className="mt-5 flex flex-wrap items-center gap-3">
                <button
                  onClick={save}
                  disabled={!dirty || invalid || busy}
                  className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-100 disabled:opacity-50"
                >
                  {busy ? "Working..." : "Save changes"}
                </button>
                <div className="flex-1" />
                <button
                  onClick={() => setConfirming("rejected")}
                  disabled={busy}
                  className="rounded-lg border border-red-300 px-4 py-2 text-sm font-medium text-red-700 hover:bg-red-50 disabled:opacity-50"
                >
                  Reject
                </button>
                <button
                  onClick={() => setConfirming("approved")}
                  disabled={invalid || busy}
                  className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-700 disabled:opacity-50"
                >
                  Approve
                </button>
              </div>
            )}

            {pending && confirming && (
              <div className="mt-5 rounded-lg border border-amber-300 bg-amber-50 p-4">
                <p className="text-sm text-slate-800">
                  {confirming === "approved"
                    ? `Approve this draft? The email will be sent to ${detail.lead_email}.`
                    : "Reject this draft? No email will be sent."}
                </p>
                <div className="mt-3 flex gap-3">
                  <button
                    onClick={() => review(confirming)}
                    disabled={busy}
                    className={`rounded-lg px-4 py-2 text-sm font-medium text-white disabled:opacity-60 ${
                      confirming === "approved"
                        ? "bg-emerald-600 hover:bg-emerald-700"
                        : "bg-red-600 hover:bg-red-700"
                    }`}
                  >
                    {busy ? "Working..." : confirming === "approved" ? "Yes, approve" : "Yes, reject"}
                  </button>
                  <button
                    onClick={() => setConfirming(null)}
                    disabled={busy}
                    className="rounded-lg border border-slate-300 px-4 py-2 text-sm text-slate-700 hover:bg-white"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
