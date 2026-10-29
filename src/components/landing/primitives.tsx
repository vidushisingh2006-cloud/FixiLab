import { motion, type HTMLMotionProps } from "framer-motion";
import type { ReactNode } from "react";

export function Reveal({ children, delay = 0, className, ...rest }: { children: ReactNode; delay?: number; className?: string } & HTMLMotionProps<"div">) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 28 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-60px" }}
      transition={{ duration: 0.7, delay, ease: [0.22, 1, 0.36, 1] }}
      className={className}
      {...rest}
    >
      {children}
    </motion.div>
  );
}

export function SectionHead({ eyebrow, title, desc, light = false }: { eyebrow?: string; title: ReactNode; desc?: string; light?: boolean }) {
  return (
    <Reveal className="mx-auto max-w-2xl text-center">
      {eyebrow && <p className={light ? "eyebrow text-muted" : "eyebrow"}>{eyebrow}</p>}
      <h2 className={`mt-4 text-3xl font-extrabold sm:text-4xl lg:text-5xl ${light ? "text-primary-foreground" : "text-primary"}`}>{title}</h2>
      {desc && <p className={`mt-5 text-base sm:text-lg ${light ? "text-primary-foreground/75" : "text-muted-foreground"}`}>{desc}</p>}
    </Reveal>
  );
}

export function Logo({ light = false }: { light?: boolean }) {
  return (
    <a href="#home" className="flex items-center gap-2.5" aria-label="DocuAudit AI home">
      <svg width="34" height="34" viewBox="0 0 34 34" aria-hidden>
        <rect width="34" height="34" rx="10" className={light ? "fill-primary-foreground" : "fill-primary"} />
        <path d="M11 8h8l5 5v13a1 1 0 0 1-1 1H11a1 1 0 0 1-1-1V9a1 1 0 0 1 1-1Z" className={light ? "fill-primary" : "fill-primary-foreground"} opacity=".95" />
        <path d="m13.5 19 2.5 2.5 5-5" fill="none" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" className="stroke-secondary" />
      </svg>
      <span className={`text-lg font-extrabold tracking-tight ${light ? "text-primary-foreground" : "text-primary"}`}>
        DocuAudit<span className="text-secondary"> AI</span>
      </span>
    </a>
  );
}
