import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { motion, AnimatePresence, useScroll, useTransform } from "framer-motion";
import {
  ArrowRight, Menu, X, ScanText, Calculator, GitCompare, ShieldCheck, FileSearch, History, Clock, FileWarning,
  ClipboardCheck, Eye, Lightbulb, GitBranch, Upload, ScanLine, ListChecks, UserCheck, FlaskConical, Pill, BadgeCheck,
  Check, Minus, ChevronDown, User, Type, CalendarClock, FileText, Target, CircleCheckBig, Equal, Archive, FolderSearch,
} from "lucide-react";
import { Dashboard, AuditDemo } from "@/components/landing/Dashboard";
import robotLab from "@/assets/robot-lab.jpg";
import { Reveal, SectionHead, Logo } from "@/components/landing/primitives";

const TITLE = "DocuAudit AI — AI Laboratory Documentation Audit Tool";
const DESC = "Detect laboratory worksheet errors with AI-powered OCR, automated calculation checks, and ALCOA+ data integrity validation. Review-ready records, faster.";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: TITLE },
      { name: "description", content: DESC },
      { property: "og:title", content: TITLE },
      { property: "og:description", content: DESC },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: Index,
});

const nav = [["Home", "home"], ["Features", "features"], ["How It Works", "how"], ["Benefits", "benefits"], ["About", "about"]];

function Header() {
  const [scrolled, setScrolled] = useState(false);
  const [open, setOpen] = useState(false);
  useEffect(() => {
    const f = () => setScrolled(window.scrollY > 20);
    f(); window.addEventListener("scroll", f, { passive: true });
    return () => window.removeEventListener("scroll", f);
  }, []);
  return (
    <header className="fixed inset-x-0 top-0 z-50 px-3 pt-3">
      <div className={`mx-auto flex max-w-6xl items-center justify-between rounded-2xl border px-4 transition-all duration-300 sm:px-5 ${scrolled ? "h-14 border-border bg-card/90 shadow-soft backdrop-blur-md" : "h-16 border-transparent bg-transparent"}`}>
        <Logo />
        <nav className="hidden items-center gap-7 lg:flex" aria-label="Main">
          {nav.map(([l, id]) => <a key={id} href={`#${id}`} className="text-sm font-medium text-muted-foreground transition hover:text-primary">{l}</a>)}
        </nav>
        <div className="hidden items-center gap-4 lg:flex">
          <a href="#cta" className="text-sm font-semibold text-foreground hover:text-primary">Sign In</a>
          <a href="#cta" className="rounded-xl bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground transition hover:bg-primary/90 active:scale-95">Get Started</a>
        </div>
        <button className="rounded-lg p-2 text-primary lg:hidden" aria-label={open ? "Close menu" : "Open menu"} aria-expanded={open} onClick={() => setOpen(!open)}>
          {open ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
        </button>
      </div>
      <AnimatePresence>
        {open && (
          <motion.nav initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }}
            className="mx-auto mt-2 max-w-6xl rounded-2xl border border-border bg-card p-4 shadow-lift lg:hidden">
            {nav.map(([l, id]) => <a key={id} href={`#${id}`} onClick={() => setOpen(false)} className="block rounded-lg px-3 py-2.5 font-medium text-foreground hover:bg-muted">{l}</a>)}
            <a href="#cta" onClick={() => setOpen(false)} className="mt-2 block rounded-xl bg-primary px-4 py-3 text-center font-semibold text-primary-foreground">Get Started</a>
          </motion.nav>
        )}
      </AnimatePresence>
    </header>
  );
}

const words = ["Catch", "Documentation", "Errors", "Before", "They", "Become", "Bigger", "Problems."];

function Hero() {
  const { scrollY } = useScroll();
  const y = useTransform(scrollY, [0, 600], [0, -60]);
  return (
    <section id="home" className="relative overflow-hidden bg-hero pb-20 pt-32 lg:pb-28 lg:pt-40">
      <div className="pointer-events-none absolute inset-0 overflow-hidden" aria-hidden>
        <motion.img src={robotLab} alt="" width={1920} height={1088}
          initial={{ scale: 1.15, opacity: 0 }} animate={{ scale: 1.04, opacity: 1 }} transition={{ duration: 2.4, ease: "easeOut" }}
          className="absolute inset-0 h-full w-full animate-kenburns object-cover object-[70%_center]" />
        <div className="absolute inset-0 bg-hero-veil" />
        <div className="absolute inset-y-0 right-[8%] w-[40%] overflow-hidden">
          <div className="absolute inset-x-0 h-24 animate-beam bg-gradient-to-b from-transparent via-secondary/30 to-transparent" />
        </div>
        <div className="absolute right-[17%] top-[16%] hidden h-28 w-28 lg:block">
          <span className="absolute inset-0 animate-ping-slow rounded-full border border-secondary/60" />
          <span className="absolute inset-3 rounded-full border border-dashed border-primary/40 animate-spin [animation-duration:14s]" />
          <span className="absolute -right-28 top-1/2 rounded-full bg-card/85 px-2.5 py-1 text-[10px] font-bold tracking-widest text-primary backdrop-blur">SAMPLE · ANALYZING</span>
        </div>
        {[12, 28, 46, 63, 78, 90].map((l, i) => (
          <span key={l} className="absolute bottom-0 h-2 w-2 animate-bubble rounded-full bg-secondary/50" style={{ left: `${l}%`, animationDelay: `${i * 1.3}s` }} />
        ))}
        <div className="absolute inset-0 grid-lines opacity-60 [mask-image:radial-gradient(ellipse_at_top_left,black,transparent_60%)]" />
      </div>
      <div className="relative mx-auto grid max-w-6xl items-center gap-14 px-5 lg:grid-cols-[1.05fr_1fr]">
        <div>
          <motion.span initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}
            className="inline-flex items-center gap-2 rounded-full border border-border bg-card px-3 py-1.5 text-[10px] font-bold tracking-[0.14em] text-primary shadow-soft sm:text-[11px]">
            <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-secondary" /> AI-POWERED LABORATORY DOCUMENTATION AUDITING
          </motion.span>
          <h1 className="mt-6 text-[2.6rem] font-extrabold text-primary sm:text-6xl lg:text-[4.1rem]">
            {words.map((w, i) => (
              <motion.span key={i} initial={{ opacity: 0, y: 30, filter: "blur(8px)" }} animate={{ opacity: 1, y: 0, filter: "blur(0px)" }}
                transition={{ delay: 0.15 + i * 0.07, duration: 0.6 }}
                className={`mr-[0.25em] inline-block ${i === 1 || i === 2 ? "text-secondary" : ""}`}>{w}</motion.span>
            ))}
          </h1>
          <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.8 }} className="mt-6 max-w-xl text-lg text-muted-foreground">
            Transform laboratory worksheets into reliable, review-ready records. DocuAudit AI uses intelligent document recognition, automated calculation checks, and ALCOA+ validation to help identify errors, inconsistencies, and missing information before submission.
          </motion.p>
          <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.95 }} className="mt-8 flex flex-wrap gap-3">
            <a href="#cta" className="group inline-flex items-center gap-2 rounded-xl bg-primary px-6 py-3.5 font-semibold text-primary-foreground shadow-lift transition hover:-translate-y-0.5 active:scale-95">
              Start Your First Audit <ArrowRight className="h-4 w-4 transition group-hover:translate-x-1" />
            </a>
            <a href="#how" className="inline-flex items-center rounded-xl border border-border bg-card px-6 py-3.5 font-semibold text-primary transition hover:border-secondary">Explore How It Works</a>
          </motion.div>
          <p className="mt-5 text-sm italic text-muted-foreground">Smarter reviews. Clearer findings. More reliable documentation.</p>
          <div className="mt-6 flex flex-wrap gap-x-6 gap-y-2">
            {["AI-Powered OCR", "Automated Validation", "ALCOA+ Data Integrity Checks"].map((c) => (
              <span key={c} className="flex items-center gap-1.5 text-sm font-semibold text-foreground"><BadgeCheck className="h-4 w-4 text-secondary" />{c}</span>
            ))}
          </div>
        </div>
        <motion.div style={{ y }} className="[perspective:1200px]"><Dashboard /></motion.div>
      </div>
    </section>
  );
}

function Strip() {
  const items = [[ScanText, "Intelligent OCR"], [Calculator, "Calculation Verification"], [GitCompare, "Consistency Checks"], [ShieldCheck, "ALCOA+ Validation"]] as const;
  return (
    <div className="border-y border-border bg-card">
      <div className="mx-auto grid max-w-6xl grid-cols-2 px-5 lg:grid-cols-4">
        {items.map(([I, t], i) => (
          <Reveal key={t} delay={i * 0.08} className={`flex items-center justify-center gap-3 py-6 ${i > 0 ? "lg:border-l" : ""} border-border`}>
            <I className="h-5 w-5 text-secondary" /><span className="text-sm font-bold text-primary">{t}</span>
          </Reveal>
        ))}
      </div>
    </div>
  );
}

function Card({ icon: I, title, desc, i }: { icon: typeof Clock; title: string; desc: string; i: number }) {
  return (
    <Reveal delay={i * 0.08} className="group h-full">
      <div className="h-full rounded-[20px] border border-border bg-card p-7 transition duration-300 hover:-translate-y-1.5 hover:border-secondary/50 hover:shadow-lift">
        <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-muted text-secondary transition group-hover:bg-primary group-hover:text-primary-foreground">
          <I className="h-5 w-5" />
        </div>
        <h3 className="mt-5 text-lg font-bold text-primary">{title}</h3>
        <p className="mt-2 text-sm text-muted-foreground">{desc}</p>
      </div>
    </Reveal>
  );
}

const problems = [
  [Clock, "Manual Review Bottlenecks", "Reviewing worksheets line by line can consume valuable time and make consistent checking difficult."],
  [FileWarning, "Hidden Inconsistencies", "Incorrect calculations, conflicting values, missing dates, and incomplete fields can escape routine checks."],
  [ClipboardCheck, "Documentation Gaps", "Missing signatures, unclear handwritten entries, and incomplete records can complicate quality reviews."],
] as const;
const features = [
  [ScanText, "AI-Powered OCR", "Extract text and numerical values from supported scanned, handwritten, and printed laboratory worksheets. Surface low-confidence fields for human verification."],
  [Calculator, "Automated Calculation Checks", "Verify supported numerical calculations and compare calculated results with recorded values to identify discrepancies."],
  [GitCompare, "Cross-Field Consistency", "Compare related fields and highlight missing information, conflicting entries, and potential inconsistencies."],
  [ShieldCheck, "ALCOA+ Validation", "Support data integrity reviews against Attributable, Legible, Contemporaneous, Original, Accurate, Complete, Consistent, Enduring, and Available principles."],
  [FileSearch, "Actionable Audit Reports", "Organize findings by issue type, severity, location, and review status to help teams investigate discrepancies efficiently."],
  [History, "Traceable Review Workflow", "Support reviewer comments, documented decisions, and clear review states for accountable documentation review."],
] as const;

function Problem() {
  return (
    <section className="py-24 lg:py-32">
      <div className="mx-auto max-w-6xl px-5">
        <SectionHead eyebrow="The Challenge" title="Small Documentation Errors Can Create Significant Risks." desc="Laboratory worksheets contain critical information that must remain accurate, complete, legible, and traceable. Manual reviews can make it difficult to identify every inconsistency across large volumes of records." />
        <div className="mt-14 grid gap-5 md:grid-cols-3">{problems.map(([I, t, d], i) => <Card key={t} icon={I} title={t} desc={d} i={i} />)}</div>
        <Reveal className="mx-auto mt-12 max-w-2xl text-center text-lg font-semibold text-primary">DocuAudit AI helps teams identify potential issues earlier and focus their attention where it matters most.</Reveal>
      </div>
    </section>
  );
}

function Features() {
  return (
    <section id="features" className="bg-muted/50 py-24 lg:py-32">
      <div className="mx-auto max-w-6xl px-5">
        <SectionHead eyebrow="Powerful Features" title="Everything You Need for Smarter Worksheet Auditing." desc="Bring document recognition, validation rules, and actionable review findings together in one streamlined experience." />
        <div className="mt-14 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">{features.map(([I, t, d], i) => <Card key={t} icon={I} title={t} desc={d} i={i % 3} />)}</div>
      </div>
    </section>
  );
}

function Showcase() {
  const rows = [
    [Eye, "See the Issue", "Identify potential documentation gaps without searching every field manually."],
    [Lightbulb, "Understand the Finding", "Review the relevant field, extracted value, and validation rule behind each flagged issue."],
    [GitBranch, "Decide What Happens Next", "Help reviewers confirm, dismiss, annotate, or investigate findings through a clear review workflow."],
  ] as const;
  return (
    <section id="showcase" className="py-24 lg:py-32">
      <div className="mx-auto max-w-6xl px-5">
        <SectionHead eyebrow="See the Difference" title="From Uploaded Worksheet to Actionable Findings." desc="Give reviewers a clearer view of extracted information, detected discrepancies, and the evidence needed to investigate potential issues." />
        <div className="mt-16 grid items-center gap-12 lg:grid-cols-[1.25fr_1fr]">
          <Reveal><AuditDemo /></Reveal>
          <div className="relative space-y-10 pl-2">
            <div className="absolute bottom-6 left-[29px] top-6 w-px bg-border" />
            {rows.map(([I, t, d], i) => (
              <Reveal key={t} delay={i * 0.12} className="relative flex gap-5">
                <div className="relative z-10 flex h-11 w-11 shrink-0 items-center justify-center rounded-full border border-border bg-card text-secondary shadow-soft"><I className="h-5 w-5" /></div>
                <div><h3 className="text-lg font-bold text-primary">{t}</h3><p className="mt-1 text-sm text-muted-foreground">{d}</p></div>
              </Reveal>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}

function How() {
  const steps = [
    [Upload, "Upload", "Upload a supported laboratory worksheet in PDF or image format."],
    [ScanLine, "Extract", "OCR identifies document text, relevant values, and fields for review."],
    [ListChecks, "Validate", "Configured rules check calculations, consistency, completeness, and selected ALCOA+ criteria."],
    [UserCheck, "Review", "Explore flagged findings, examine available evidence, and document reviewer decisions."],
  ] as const;
  return (
    <section id="how" className="bg-card py-24 lg:py-32">
      <div className="mx-auto max-w-6xl px-5">
        <SectionHead eyebrow="A Simple Workflow" title="Four Steps to a More Reliable Review." />
        <div className="relative mt-16 grid gap-10 lg:grid-cols-4 lg:gap-6">
          <motion.div initial={{ scaleX: 0 }} whileInView={{ scaleX: 1 }} viewport={{ once: true }} transition={{ duration: 1.6, ease: "easeInOut" }}
            className="absolute left-0 right-0 top-7 hidden h-px origin-left bg-secondary/50 lg:block" />
          <div className="absolute bottom-0 left-7 top-0 w-px bg-border lg:hidden" />
          {steps.map(([I, t, d], i) => (
            <Reveal key={t} delay={i * 0.18} className="relative flex gap-5 lg:block">
              <div className="relative z-10 flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl bg-primary text-primary-foreground shadow-lift"><I className="h-6 w-6" /></div>
              <div>
                <p className="text-5xl font-extrabold text-muted lg:mt-6">0{i + 1}</p>
                <h3 className="-mt-3 text-xl font-bold text-primary">{t}</h3>
                <p className="mt-2 text-sm text-muted-foreground">{d}</p>
              </div>
            </Reveal>
          ))}
        </div>
        <div className="mt-14 text-center">
          <a href="#showcase" className="group inline-flex items-center gap-2 font-semibold text-primary hover:text-secondary">Explore the Audit Workflow <ArrowRight className="h-4 w-4 transition group-hover:translate-x-1" /></a>
        </div>
      </div>
    </section>
  );
}

function Alcoa() {
  const p = [
    [User, "Attributable", "Identify who performed or documented an activity where supporting records are available."],
    [Type, "Legible", "Highlight potentially unclear or low-confidence entries."],
    [CalendarClock, "Contemporaneous", "Check for required dates and configured timing-related documentation fields."],
    [FileText, "Original", "Support review of original records and their associated documentation."],
    [Target, "Accurate", "Check supported calculations and validation rules."],
    [CircleCheckBig, "Complete", "Identify potentially missing required fields."],
    [Equal, "Consistent", "Detect discrepancies between related fields or records."],
    [Archive, "Enduring", "Support appropriate record-retention and documentation workflows."],
    [FolderSearch, "Available", "Support organized retrieval of records and audit findings."],
  ] as const;
  return (
    <section id="alcoa" className="relative overflow-hidden bg-forest py-24 lg:py-32">
      <div className="pointer-events-none absolute -right-40 -top-40 h-[500px] w-[500px] rounded-full bg-secondary/20 blur-3xl" />
      <div className="relative mx-auto max-w-6xl px-5">
        <SectionHead light eyebrow="Data Integrity Matters" title="Built Around the Principles of Reliable Data." desc="DocuAudit AI supports structured documentation reviews using the ALCOA+ data integrity framework." />
        <div className="mt-14 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {p.map(([I, t, d], i) => (
            <Reveal key={t} delay={(i % 3) * 0.08}>
              <div className="group h-full rounded-[20px] border border-primary-foreground/10 bg-primary-foreground/5 p-6 transition hover:bg-primary-foreground/10">
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-muted text-primary transition group-hover:rotate-6"><I className="h-5 w-5" /></div>
                  <h3 className="text-lg font-bold text-primary-foreground"><span className="text-muted">{t[0]}</span>{t.slice(1)}</h3>
                </div>
                <p className="mt-3 text-sm text-primary-foreground/70">{d}</p>
              </div>
            </Reveal>
          ))}
        </div>
        <p className="mx-auto mt-10 max-w-2xl text-center text-xs text-primary-foreground/60">These are supported review objectives, not a guarantee that all nine principles can be independently verified through automated analysis.</p>
      </div>
    </section>
  );
}

function Benefits() {
  const before = ["Repetitive field-by-field checks.", "Difficult-to-track inconsistencies.", "Separate notes and review records.", "Time-consuming report preparation."];
  const after = ["AI-assisted text extraction.", "Rule-based discrepancy detection.", "Organized findings and reviewer comments.", "Structured audit report preparation."];
  return (
    <section id="benefits" className="py-24 lg:py-32">
      <div className="mx-auto max-w-5xl px-5">
        <SectionHead eyebrow="Benefits" title="Less Time Searching. More Time Reviewing What Matters." />
        <div className="mt-14 grid gap-5 md:grid-cols-2">
          <Reveal className="rounded-[20px] border border-border bg-card p-8">
            <h3 className="text-lg font-bold text-muted-foreground">Traditional Manual Review</h3>
            <ul className="mt-6 space-y-4">{before.map((b) => <li key={b} className="flex items-center gap-3 text-muted-foreground"><span className="flex h-6 w-6 items-center justify-center rounded-full bg-background"><Minus className="h-3.5 w-3.5" /></span>{b}</li>)}</ul>
          </Reveal>
          <Reveal delay={0.12} className="relative rounded-[20px] border-2 border-secondary bg-muted p-8 shadow-lift">
            <span className="absolute -top-3 right-6 rounded-full bg-primary px-3 py-1 text-[11px] font-bold text-primary-foreground">Recommended</span>
            <h3 className="text-lg font-bold text-primary">With DocuAudit AI</h3>
            <ul className="mt-6 space-y-4">{after.map((b, i) => (
              <motion.li key={b} initial={{ opacity: 0, x: -10 }} whileInView={{ opacity: 1, x: 0 }} viewport={{ once: true }} transition={{ delay: 0.3 + i * 0.1 }} className="flex items-center gap-3 font-medium text-foreground">
                <span className="flex h-6 w-6 items-center justify-center rounded-full bg-secondary text-secondary-foreground"><Check className="h-3.5 w-3.5" /></span>{b}
              </motion.li>))}</ul>
          </Reveal>
        </div>
      </div>
    </section>
  );
}

function Audience() {
  const a = [
    [FlaskConical, "Analytical Laboratories", "Support worksheet reviews, numerical verification, and documentation quality checks."],
    [Pill, "Pharmaceutical & Clinical Research Teams", "Help identify potential record inconsistencies and missing documentation before review or submission."],
    [BadgeCheck, "Quality Assurance Professionals", "Organize audit findings and support structured, traceable review workflows."],
  ] as const;
  return (
    <section id="about" className="bg-muted/50 py-24 lg:py-32">
      <div className="mx-auto max-w-6xl px-5">
        <SectionHead eyebrow="Who It's For" title="Designed for Teams That Depend on Reliable Documentation." />
        <div className="mt-14 grid gap-5 md:grid-cols-3">{a.map(([I, t, d], i) => <Card key={t} icon={I} title={t} desc={d} i={i} />)}</div>
      </div>
    </section>
  );
}

const faqs = [
  ["What is DocuAudit AI?", "DocuAudit AI is an intelligent laboratory documentation auditing platform designed to help identify potential worksheet errors, calculation discrepancies, missing information, and data integrity gaps."],
  ["What document formats are supported?", "The planned upload workflow supports PDF, PNG, JPG, and JPEG files. Actual limits and support depend on the implemented document-processing service."],
  ["Can it read handwritten laboratory worksheets?", "OCR can help extract handwritten text, but accuracy depends on handwriting quality, image resolution, and document conditions. Uncertain fields should be reviewed by a person."],
  ["How does calculation verification work?", "The platform can apply configured calculation rules to extracted values and flag discrepancies between expected and recorded results. Validation depends on the available rules and the accuracy of extracted data."],
  ["What is ALCOA+ validation?", "ALCOA+ is a framework for data integrity. DocuAudit AI is designed to support selected documentation checks aligned with these principles; automated checks do not independently certify compliance."],
  ["Does the platform guarantee regulatory compliance?", "No. It supports documentation review and identification of potential issues. Regulatory compliance depends on the complete quality system, applicable requirements, validated processes, and appropriate human oversight."],
  ["Is my laboratory data secure?", "Data protection depends on the deployed application's access controls, storage configuration, encryption, retention policies, and backend security. Do not upload sensitive laboratory records until the applicable security controls have been implemented and reviewed."],
];

function Faq() {
  const [open, setOpen] = useState<number | null>(0);
  return (
    <section id="faq" className="py-24 lg:py-32">
      <div className="mx-auto max-w-3xl px-5">
        <SectionHead eyebrow="FAQ" title="Frequently Asked Questions" />
        <div className="mt-12 space-y-3">
          {faqs.map(([q, a], i) => {
            const isOpen = open === i;
            return (
              <Reveal key={q} delay={i * 0.04} className="overflow-hidden rounded-2xl border border-border bg-card">
                <h3>
                  <button id={`faq-${i}`} aria-expanded={isOpen} aria-controls={`faq-p-${i}`} onClick={() => setOpen(isOpen ? null : i)}
                    className="flex w-full items-center justify-between gap-4 px-6 py-5 text-left font-bold text-primary focus-visible:outline-2 focus-visible:outline-ring">
                    {q}<ChevronDown className={`h-5 w-5 shrink-0 text-secondary transition-transform duration-300 ${isOpen ? "rotate-180" : ""}`} />
                  </button>
                </h3>
                <AnimatePresence initial={false}>
                  {isOpen && (
                    <motion.div id={`faq-p-${i}`} role="region" aria-labelledby={`faq-${i}`} initial={{ height: 0, opacity: 0 }} animate={{ height: "auto", opacity: 1 }} exit={{ height: 0, opacity: 0 }}>
                      <p className="px-6 pb-5 text-sm text-muted-foreground">{a}</p>
                    </motion.div>
                  )}
                </AnimatePresence>
              </Reveal>
            );
          })}
        </div>
      </div>
    </section>
  );
}

function Cta() {
  return (
    <section id="cta" className="px-3 pb-6">
      <Reveal className="relative mx-auto max-w-6xl overflow-hidden rounded-[28px] bg-forest px-6 py-20 text-center sm:py-24">
        <div className="pointer-events-none absolute inset-0 grid-lines opacity-40 [mask-image:radial-gradient(ellipse,black,transparent_70%)]" />
        <motion.div animate={{ rotate: 360 }} transition={{ duration: 60, repeat: Infinity, ease: "linear" }}
          className="pointer-events-none absolute -left-24 -top-24 h-72 w-72 rounded-full border border-dashed border-primary-foreground/15" />
        <div className="relative">
          <h2 className="text-4xl font-extrabold text-primary-foreground sm:text-6xl">Make Every Worksheet <span className="text-muted">Count.</span></h2>
          <p className="mx-auto mt-5 max-w-xl text-primary-foreground/75">Bring greater clarity to laboratory documentation reviews with intelligent extraction, automated checks, and actionable audit findings.</p>
          <div className="mt-9 flex flex-wrap justify-center gap-3">
            <a href="#home" className="group inline-flex items-center gap-2 rounded-xl bg-muted px-6 py-3.5 font-bold text-primary transition hover:-translate-y-0.5">Start Your First Audit <ArrowRight className="h-4 w-4 transition group-hover:translate-x-1" /></a>
            <a href="#features" className="rounded-xl border border-primary-foreground/25 px-6 py-3.5 font-semibold text-primary-foreground transition hover:bg-primary-foreground/10">Explore Features</a>
          </div>
          <p className="mt-6 text-sm text-primary-foreground/60">Built to support more consistent reviews and stronger documentation practices.</p>
        </div>
      </Reveal>
    </section>
  );
}

function Footer() {
  const cols = [
    ["Product", [["Features", "#features"], ["How It Works", "#how"], ["Audit Workflow", "#showcase"]]],
    ["Resources", [["ALCOA+ Principles", "#alcoa"], ["FAQ", "#faq"], ["Documentation (coming soon)", ""]]],
    ["Company", [["About", "#about"], ["Contact (coming soon)", ""], ["Privacy Policy (coming soon)", ""], ["Terms of Use (coming soon)", ""]]],
  ] as const;
  return (
    <footer className="bg-primary text-primary-foreground">
      <div className="mx-auto grid max-w-6xl gap-10 px-5 py-16 sm:grid-cols-2 lg:grid-cols-4">
        <div><Logo light /><p className="mt-4 max-w-xs text-sm text-primary-foreground/70">Intelligent auditing for reliable laboratory data.</p></div>
        {cols.map(([h, links]) => (
          <div key={h}>
            <p className="text-sm font-bold">{h}</p>
            <ul className="mt-4 space-y-2.5">{links.map(([l, href]) => <li key={l}>{href ? <a href={href} className="text-sm text-primary-foreground/70 hover:text-primary-foreground">{l}</a> : <span className="text-sm text-primary-foreground/45">{l}</span>}</li>)}</ul>
          </div>
        ))}
      </div>
      <div className="border-t border-primary-foreground/10">
        <div className="mx-auto flex max-w-6xl flex-col gap-2 px-5 py-6 text-xs text-primary-foreground/55 md:flex-row md:justify-between">
          <p>© 2026 DocuAudit AI. All rights reserved.</p>
          <p className="max-w-xl">DocuAudit AI supports documentation review and does not replace qualified human review or guarantee regulatory compliance.</p>
        </div>
      </div>
    </footer>
  );
}

function Index() {
  return (
    <div className="overflow-x-clip">
      <Header />
      <main>
        <Hero /><Strip /><Problem /><Features /><Showcase /><How /><Alcoa /><Benefits /><Audience /><Faq /><Cta />
      </main>
      <Footer />
    </div>
  );
}
