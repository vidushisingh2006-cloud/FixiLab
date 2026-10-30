import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import type { ReactNode } from "react";
import { Audit } from "@/routes/audit";

vi.mock("@tanstack/react-router", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@tanstack/react-router")>();
  return {
    ...actual,
    Link: ({ children }: { children: ReactNode }) => <a>{children}</a>,
  };
});

describe("Audit Route", () => {
  it("renders upload interface", () => {
    render(<Audit />);
    expect(screen.getByText("Start Your First Audit")).toBeInTheDocument();
  });

  it("shows file upload instructions", () => {
    render(<Audit />);
    expect(screen.getByText(/drag and drop/i)).toBeInTheDocument();
  });

  it("displays supported file formats", () => {
    render(<Audit />);
    expect(screen.getByText(/PDF, PNG, JPG, JPEG/i)).toBeInTheDocument();
  });
});
