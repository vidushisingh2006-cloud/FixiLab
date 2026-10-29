import { motion } from "framer-motion";
import { AlertTriangle, CheckCircle2, Clock, FileText, ScanText, XCircle, Sparkles, Link2 } from "lucide-react";

const metrics = [
  { label: "Checks Passed", value: 42, icon: CheckCircle2, tone: "text-secondary" },
  { label: "Issues Detected", value: 3, icon: XCircle, tone: "text-destructive" },
  { label: "Pending Review", value: 5, icon: Clock, tone: "text-warning" },
];
const findings = [
  { t: "Calculation discrepancy", s: "Row 14 · Assay %", tone: "bg-destructive", tag: "Critical" },
  { t: "Missing reviewer signature", s: "Page 2 · Sign-off", tone: "bg-warning", tag: "Review" },
  { t: "Low-confidence OCR field", s: "Page 1 · Batch No.", tone: "bg-warning", tag: "Review" },
];

function Ring() {
  const r = 38, c = 2 * Math.PI * r;
  const segs = [
    { p: 0.84, cls: "stroke-secondary", off: 0 },
    { p: 0.1, cls: "stroke-warning", off: 0.84 },
    { p: 0.06, cls: "stroke-destructive", off: 0.94 },
  ];
  return (
    <svg viewBox="0 0 100 100" className="h-28 w-28 -rotate-90">
      <circle cx="50" cy="50" r={r} className="fill-none stroke-muted" strokeWidth="10" />
      {segs.map((s, i) => (
        <motion.circle
          key={i} cx="50" cy="50" r={r} className={`fill-none ${s.cls}`} strokeWidth="10" strokeLinecap="butt"
          strokeDasharray={`${s.p * c} ${c}`}
          initial={{ strokeDashoffset: s.p * c - s.off * c + s.p * c }}
          animate={{ strokeDashoffset: -s.off * c }}
          transition={{ duration: 1.4, delay: 0.6 + i * 0.25, ease: "easeOut" }}
        />
      ))}
    </svg>
  );
}

export function Dashboard() {
  return (
    <div className="relative">
      <motion.div
        initial={{ opacity: 0, y: 40, rotateX: 8 }}
        animate={{ opacity: 1, y: 0, rotateX: 0 }}
        transition={{ duration: 1, delay: 0.2, ease: [0.22, 1, 0.36, 1] }}
        className="relative rounded-3xl border border-border bg-card p-5 shadow-lift sm:p-6"
      >
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="text-sm font-bold text-primary">Worksheet Audit Overview</p>
            <p className="mt-0.5 flex items-center gap-1.5 text-xs text-muted-foreground"><FileText className="h-3.5 w-3.5" /> Analytical_Worksheet_001.pdf</p>
          </div>
          <span className="inline-flex items-center gap-1.5 rounded-full bg-warning/15 px-3 py-1 text-xs font-semibold text-foreground">
            <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-warning" /> Review Required
          </span>
        </div>

        <div className="mt-5 grid grid-cols-3 gap-2.5">
          {metrics.map((m, i) => (
            <motion.div key={m.label} initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.5 + i * 0.12 }}
              className="rounded-2xl border border-border bg-background p-3">
              <m.icon className={`h-4 w-4 ${m.tone}`} />
              <p className="mt-2 text-2xl font-extrabold text-primary">{m.value}</p>
              <p className="text-[11px] leading-tight text-muted-foreground">{m.label}</p>
            </motion.div>
          ))}
        </div>

        <div className="mt-4 grid gap-4 sm:grid-cols-[auto_1fr]">
          <div className="flex items-center gap-4 rounded-2xl bg-muted/60 p-4 sm:flex-col sm:justify-center">
            <div className="relative">
              <Ring />
              <div className="absolute inset-0 flex flex-col items-center justify-center">
                <span className="text-xl font-extrabold text-primary">84%</span>
                <span className="text-[10px] text-muted-foreground">validated</span>
              </div>
            </div>
            <div className="space-y-1 text-[11px] text-muted-foreground">
              <p className="flex items-center gap-1.5"><span className="h-2 w-2 rounded-full bg-secondary" />Passed</p>
              <p className="flex items-center gap-1.5"><span className="h-2 w-2 rounded-full bg-warning" />Review</p>
              <p className="flex items-center gap-1.5"><span className="h-2 w-2 rounded-full bg-destructive" />Critical</p>
            </div>
          </div>
          <ul className="space-y-2">
            {findings.map((f, i) => (
              <motion.li key={f.t} initial={{ opacity: 0, x: 16 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.9 + i * 0.15 }}
                className="flex items-center gap-3 rounded-xl border border-border p-3">
                <span className={`h-8 w-1 rounded-full ${f.tone}`} />
                <div className="min-w-0 flex-1">
                  <p className="truncate text-xs font-semibold text-foreground">{f.t}</p>
                  <p className="text-[11px] text-muted-foreground">{f.s}</p>
                </div>
                <span className="text-[10px] font-semibold text-muted-foreground">{f.tag}</span>
              </motion.li>
            ))}
            <button className="mt-1 w-full rounded-xl bg-primary py-2.5 text-xs font-semibold text-primary-foreground transition hover:bg-primary/90">View Audit Report</button>
          </ul>
        </div>
        <p className="mt-3 text-center text-[10px] text-muted-foreground">Illustrative sample data</p>
      </motion.div>

      <motion.div initial={{ opacity: 0, scale: 0.8 }} animate={{ opacity: 1, scale: 1 }} transition={{ delay: 1.3 }}
        className="absolute -left-4 top-24 hidden animate-floaty items-center gap-2 rounded-full border border-border bg-card px-4 py-2 text-xs font-semibold text-primary shadow-soft md:flex">
        <Sparkles className="h-3.5 w-3.5 text-secondary" /> AI-Assisted Review
      </motion.div>
      <motion.div initial={{ opacity: 0, scale: 0.8 }} animate={{ opacity: 1, scale: 1 }} transition={{ delay: 1.5 }}
        className="absolute -right-3 bottom-16 hidden animate-floaty items-center gap-2 rounded-full bg-primary px-4 py-2 text-xs font-semibold text-primary-foreground shadow-lift md:flex [animation-delay:1.5s]">
        <Link2 className="h-3.5 w-3.5" /> Traceable Findings
      </motion.div>
    </div>
  );
}

export function AuditDemo() {
  return (
    <div className="rounded-3xl border border-border bg-card p-4 shadow-lift sm:p-5">
      <div className="mb-4 flex items-center justify-between">
        <div className="flex gap-1.5"><span className="h-2.5 w-2.5 rounded-full bg-destructive/60" /><span className="h-2.5 w-2.5 rounded-full bg-warning/70" /><span className="h-2.5 w-2.5 rounded-full bg-secondary/70" /></div>
        <span className="rounded-full bg-muted px-3 py-1 text-[10px] font-semibold text-primary">Interactive demo · mock data</span>
      </div>
      <div className="grid gap-4 md:grid-cols-2">
        <div className="relative overflow-hidden rounded-2xl border border-border bg-background p-4 grid-lines">
          <p className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground">Document preview</p>
          <div className="mt-3 space-y-2 font-mono text-[11px] text-foreground">
            {[["Sample wt (mg)", "50.12"], ["Std. area", "10234"], ["Sample area", "10051"], ["Std. purity %", "99.8"]].map(([k, v]) => (
              <div key={k} className="flex justify-between rounded-md bg-card/80 px-2 py-1.5"><span className="text-muted-foreground">{k}</span><span>{v}</span></div>
            ))}
            <motion.div initial={{ backgroundColor: "transparent" }} whileInView={{ backgroundColor: "oklch(0.65 0.13 22 / 0.14)" }} transition={{ delay: 0.8, duration: 0.6 }}
              className="flex justify-between rounded-md px-2 py-1.5 ring-1 ring-destructive/50">
              <span className="text-muted-foreground">Result %</span><span className="font-bold text-destructive">99.12</span>
            </motion.div>
          </div>
          <div className="pointer-events-none absolute inset-x-0 h-10 animate-scan bg-gradient-to-b from-transparent via-secondary/25 to-transparent" />
        </div>
        <div className="space-y-3">
          <div className="rounded-2xl border border-border p-3">
            <p className="flex items-center gap-1.5 text-[10px] font-bold uppercase tracking-widest text-muted-foreground"><ScanText className="h-3 w-3" /> Extracted text</p>
            <p className="mt-2 font-mono text-[11px] text-foreground">Batch No: <span className="rounded bg-warning/20 px-1">LB-2O26-14</span></p>
            <div className="mt-2 flex items-center gap-2 text-[10px] text-muted-foreground">
              Confidence
              <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-muted">
                <motion.div initial={{ width: 0 }} whileInView={{ width: "62%" }} transition={{ duration: 1.2, delay: 0.4 }} className="h-full rounded-full bg-warning" />
              </div>
              62%
            </div>
          </div>
          <div className="rounded-2xl border border-destructive/30 bg-destructive/5 p-3">
            <p className="flex items-center gap-1.5 text-xs font-bold text-destructive"><AlertTriangle className="h-3.5 w-3.5" /> Issue summary</p>
            <p className="mt-1.5 text-xs text-foreground">Recorded result does not match the calculated value.</p>
            <p className="mt-1 font-mono text-[10px] text-muted-foreground">Expected 98.04 · Recorded 99.12</p>
            <div className="mt-3 flex items-center justify-between">
              <span className="rounded-full bg-warning/20 px-2 py-0.5 text-[10px] font-semibold text-foreground">Status: Open</span>
              <button className="rounded-lg bg-primary px-3 py-1.5 text-[11px] font-semibold text-primary-foreground transition hover:bg-primary/90">View Finding</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
