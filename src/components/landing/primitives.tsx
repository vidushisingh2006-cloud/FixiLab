import { motion, type HTMLMotionProps } from "framer-motion";
import type { ReactNode } from "react";
import logoAsset from "@/assets/fixilab-logo.png.asset.json";

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
    <a href="#home" aria-label="FixiLab home" className={`group inline-flex items-center ${light ? "rounded-xl bg-card px-3 py-1.5 shadow-soft" : ""}`}>
      <img src={logoAsset.url} alt="FixiLab" width={190} height={80} className="h-11 w-auto rounded-md mix-blend-multiply transition-transform duration-300 group-hover:-rotate-2 group-hover:scale-105" />
    </a>
  );
}
