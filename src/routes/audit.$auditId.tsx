import { createFileRoute, Link } from "@tanstack/react-router";
import { useState, useEffect, useCallback } from "react";
import { motion } from "framer-motion";
import { ArrowLeft, FileText, Loader2, AlertTriangle, CheckCircle2, Download } from "lucide-react";
import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";
import { Logo } from "@/components/landing/primitives";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { DocumentPreview } from "@/components/audit/DocumentPreview";
import { getApiError, getApiUrl } from "@/lib/api";

const TITLE = "FixiLab | Document Review";

interface ExtractionResult {
  field_name: string;
  value: string;
  page_number: number;
  confidence?: number;
  source: string;
}

interface AuditFinding {
  id: string;
  severity: string;
  category: string;
  description: string;
  extracted_value: string | null;
  expected_value: string | null;
  page_number: number | null;
  evidence: string | null;
  review_status: string;
  reviewer_comments: string | null;
}

interface AuditDetail {
  filename: string;
  file_size: number;
  status: string;
  created_at: string;
  mime_type: string;
  findings: AuditFinding[];
  extraction_results: ExtractionResult[];
}

export const Route = createFileRoute("/audit/$auditId")({
  head: () => ({
    meta: [{ title: TITLE }, { name: "robots", content: "noindex" }],
  }),
  component: AuditDetail,
});

interface DonutSlice {
  name: string;
  value: number;
  color: string;
}

function DonutChart({
  data,
  centerValue,
  centerLabel,
}: {
  data: DonutSlice[];
  centerValue: number;
  centerLabel: string;
}) {
  return (
    <div className="relative h-40 w-40 shrink-0">
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie
            data={data}
            dataKey="value"
            nameKey="name"
            innerRadius={52}
            outerRadius={72}
            paddingAngle={2}
            startAngle={90}
            endAngle={-270}
            stroke="none"
          >
            {data.map((slice) => (
              <Cell key={slice.name} fill={slice.color} />
            ))}
          </Pie>
          <Tooltip
            contentStyle={{
              borderRadius: 12,
              border: "1px solid var(--border)",
              background: "var(--card)",
              fontSize: 12,
            }}
          />
        </PieChart>
      </ResponsiveContainer>
      <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-2xl font-extrabold text-primary">{centerValue}</span>
        <span className="text-[10px] uppercase tracking-wide text-muted-foreground">
          {centerLabel}
        </span>
      </div>
    </div>
  );
}

function AuditDetail() {
  const { auditId } = Route.useParams();
  const [audit, setAudit] = useState<AuditDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [extracting, setExtracting] = useState(false);
  const [validating, setValidating] = useState(false);
  const [extractionResults, setExtractionResults] = useState<ExtractionResult[]>([]);
  const [findings, setFindings] = useState<AuditFinding[]>([]);
  const [reviewerComments, setReviewerComments] = useState<Record<string, string>>({});
  const [savingFindingId, setSavingFindingId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const fetchAudit = useCallback(async () => {
    try {
      const response = await fetch(getApiUrl(`/api/audits/${auditId}`));
      if (!response.ok) throw new Error(await getApiError(response));
      const data: AuditDetail = await response.json();
      setAudit(data);
      setFindings(data.findings || []);
      setExtractionResults(data.extraction_results || []);
      setReviewerComments(
        Object.fromEntries(
          (data.findings || []).map((finding) => [finding.id, finding.reviewer_comments || ""]),
        ),
      );
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load this audit.");
      console.error("Failed to fetch audit:", err);
    } finally {
      setLoading(false);
    }
  }, [auditId]);

  useEffect(() => {
    void fetchAudit();
    
    // Poll for status updates if the audit is in a processing state
    let intervalId: number | undefined;
    if (audit && ["uploaded", "extracting", "validating"].includes(audit.status)) {
      intervalId = window.setInterval(() => {
        void fetchAudit();
      }, 3000);
    }
    
    return () => {
      if (intervalId) window.clearInterval(intervalId);
    };
  }, [fetchAudit, audit?.status]);

  const handleExtract = async () => {
    setExtracting(true);
    setError(null);
    try {
      const response = await fetch(getApiUrl(`/api/audits/${auditId}/extract`), {
        method: "POST",
      });
      if (!response.ok) throw new Error(await getApiError(response));
      const data: { extraction_results: ExtractionResult[] } = await response.json();
      setExtractionResults(data.extraction_results || []);
      await fetchAudit();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Extraction failed.");
      console.error("Extraction failed:", err);
    } finally {
      setExtracting(false);
    }
  };

  const handleValidate = async () => {
    setValidating(true);
    setError(null);
    try {
      const response = await fetch(getApiUrl(`/api/audits/${auditId}/validate`), {
        method: "POST",
      });
      if (!response.ok) throw new Error(await getApiError(response));
      const data: { extraction_results: ExtractionResult[] } = await response.json();
      setExtractionResults(data.extraction_results || []);
      await fetchAudit();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Validation failed.");
      console.error("Validation failed:", err);
    } finally {
      setValidating(false);
    }
  };

  const handleDownloadReport = async () => {
    try {
      const response = await fetch(getApiUrl(`/api/audits/${auditId}/report`));
      if (!response.ok) throw new Error(await getApiError(response));
      const reportUrl = URL.createObjectURL(await response.blob());
      const link = document.createElement("a");
      link.href = reportUrl;
      link.download = `fixilab-audit-${auditId}.pdf`;
      link.click();
      window.setTimeout(() => URL.revokeObjectURL(reportUrl), 1000);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Report download failed.");
      console.error("Report download failed:", err);
    }
  };

  const handleSaveReview = async (finding: AuditFinding) => {
    setSavingFindingId(finding.id);
    setError(null);
    try {
      const response = await fetch(getApiUrl(`/api/audits/${auditId}/findings/${finding.id}`), {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          reviewer_comments: reviewerComments[finding.id] || "",
          review_status: finding.review_status,
        }),
      });
      if (!response.ok) throw new Error(await getApiError(response));
      const updated: Pick<AuditFinding, "id" | "review_status" | "reviewer_comments"> =
        await response.json();
      setFindings((current) =>
        current.map((item) =>
          item.id === updated.id
            ? {
                ...item,
                review_status: updated.review_status,
                reviewer_comments: updated.reviewer_comments,
              }
            : item,
        ),
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not save this review.");
    } finally {
      setSavingFindingId(null);
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case "critical":
        return "bg-destructive text-destructive-foreground";
      case "major":
        return "bg-warning text-foreground";
      case "minor":
        return "bg-secondary text-secondary-foreground";
      default:
        return "bg-muted text-muted-foreground";
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "open":
        return "bg-destructive/15 text-destructive";
      case "resolved":
        return "bg-secondary/15 text-secondary";
      case "accepted":
        return "bg-secondary/15 text-secondary";
      default:
        return "bg-muted text-muted-foreground";
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  if (!audit) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center px-4">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-foreground">Audit not found</h1>
          <p className="mt-2 text-sm text-destructive">{error}</p>
          <Link to="/audit" className="mt-4 inline-block text-primary hover:text-secondary">
            Start a new audit
          </Link>
        </div>
      </div>
    );
  }

  const criticalCount = findings.filter((f) => f.severity === "critical").length;
  const majorCount = findings.filter((f) => f.severity === "major").length;
  const minorCount = findings.filter((f) => f.severity === "minor").length;
  const reviewCount = findings.filter((f) => f.severity === "review_required").length;

  const severityData: DonutSlice[] = [
    { name: "Critical", value: criticalCount, color: "var(--destructive)" },
    { name: "Major", value: majorCount, color: "var(--warning)" },
    { name: "Minor", value: minorCount, color: "var(--secondary)" },
    { name: "Review required", value: reviewCount, color: "var(--muted-foreground)" },
  ].filter((slice) => slice.value > 0);

  const statusPalette: Record<string, string> = {
    open: "var(--destructive)",
    needs_review: "var(--warning)",
    accepted: "var(--secondary)",
    resolved: "var(--primary)",
  };
  const statusData: DonutSlice[] = Object.entries(
    findings.reduce<Record<string, number>>((acc, finding) => {
      const key = finding.review_status || "open";
      acc[key] = (acc[key] || 0) + 1;
      return acc;
    }, {}),
  ).map(([status, value]) => ({
    name: status.replace(/_/g, " ").replace(/\b\w/g, (char) => char.toUpperCase()),
    value,
    color: statusPalette[status] ?? "var(--muted-foreground)",
  }));

  return (
    <div className="mx-auto max-w-6xl px-5">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-6"
      >
        <Link
          to="/audit"
          className="inline-flex items-center gap-2 text-sm font-semibold text-muted-foreground hover:text-primary"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to Upload
        </Link>
      </motion.div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="mb-8"
      >
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <h1 className="text-3xl font-extrabold text-primary">Document Review</h1>
            <p className="mt-2 text-muted-foreground">{audit.filename}</p>
          </div>
          <Badge
            className={
              audit.status === "completed"
                ? "bg-secondary text-secondary-foreground"
                : "bg-warning text-foreground"
            }
          >
            {audit.status}
          </Badge>
        </div>
      </motion.div>

      {error && (
        <div
          role="alert"
          className="mb-6 rounded-xl border border-destructive/30 bg-destructive/5 p-4 text-sm text-destructive"
        >
          {error}
        </div>
      )}

      {findings.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.15 }}
          className="mb-6 grid gap-4 md:grid-cols-2"
        >
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-base">Severity Mix</CardTitle>
            </CardHeader>
            <CardContent className="flex flex-col items-center gap-5 sm:flex-row">
              <DonutChart
                data={severityData}
                centerValue={findings.length}
                centerLabel="findings"
              />
              <ul className="w-full space-y-2 text-sm text-muted-foreground">
                {severityData.map((slice) => (
                  <li key={slice.name} className="flex items-center justify-between gap-3">
                    <span className="flex items-center gap-2">
                      <span
                        className="h-2.5 w-2.5 rounded-full"
                        style={{ backgroundColor: slice.color }}
                      />
                      {slice.name}
                    </span>
                    <span className="font-semibold text-foreground">{slice.value}</span>
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-base">Review Status</CardTitle>
            </CardHeader>
            <CardContent className="flex flex-col items-center gap-5 sm:flex-row">
              <DonutChart data={statusData} centerValue={findings.length} centerLabel="in review" />
              <ul className="w-full space-y-2 text-sm text-muted-foreground">
                {statusData.map((slice) => (
                  <li key={slice.name} className="flex items-center justify-between gap-3">
                    <span className="flex items-center gap-2">
                      <span
                        className="h-2.5 w-2.5 rounded-full"
                        style={{ backgroundColor: slice.color }}
                      />
                      {slice.name}
                    </span>
                    <span className="font-semibold text-foreground">{slice.value}</span>
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>
        </motion.div>
      )}

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <Tabs defaultValue="findings" className="space-y-6">
            <TabsList className="grid w-full grid-cols-3">
              <TabsTrigger value="findings">Findings</TabsTrigger>
              <TabsTrigger value="extraction">Extraction</TabsTrigger>
              <TabsTrigger value="preview">Preview</TabsTrigger>
            </TabsList>

            <TabsContent value="findings" className="space-y-4">
              <div className="flex flex-wrap gap-3">
                <Button
                  onClick={handleExtract}
                  disabled={extracting || !["uploaded", "failed"].includes(audit.status)}
                  variant="outline"
                >
                  {extracting ? (
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  ) : (
                    <FileText className="mr-2 h-4 w-4" />
                  )}
                  Extract Data
                </Button>
                <Button
                  onClick={handleValidate}
                  disabled={validating || audit.status !== "extracted"}
                  className="bg-primary text-primary-foreground hover:bg-primary/90"
                >
                  {validating ? (
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  ) : (
                    <CheckCircle2 className="mr-2 h-4 w-4" />
                  )}
                  Validate
                </Button>
                <Button
                  onClick={handleDownloadReport}
                  disabled={audit.status !== "completed"}
                  variant="outline"
                >
                  <Download className="mr-2 h-4 w-4" />
                  Download Report
                </Button>
              </div>

              {findings.length === 0 ? (
                <Card>
                  <CardContent className="p-8 text-center">
                    <p className="text-muted-foreground">
                      {audit.status === "completed"
                        ? "No findings generated."
                        : "Run validation to generate findings."}
                      {audit.status === "completed" && (
                        <span className="mt-2 block text-sm">
                          Automated checks only verify readable arithmetic equations and basic
                          documentation fields. Confirm the full worksheet manually.
                        </span>
                      )}
                    </p>
                  </CardContent>
                </Card>
              ) : (
                <div className="space-y-3">
                  {findings.map((finding) => (
                    <Card key={finding.id}>
                      <CardHeader className="pb-3">
                        <div className="flex items-start justify-between gap-4">
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-2">
                              <Badge className={getSeverityColor(finding.severity)}>
                                {finding.severity}
                              </Badge>
                              <Badge variant="outline">{finding.category}</Badge>
                            </div>
                            <CardTitle className="text-base">{finding.description}</CardTitle>
                          </div>
                          <Badge className={getStatusColor(finding.review_status)}>
                            {finding.review_status}
                          </Badge>
                        </div>
                      </CardHeader>
                      <CardContent className="space-y-2 text-sm">
                        {finding.extracted_value && (
                          <div className="flex justify-between">
                            <span className="text-muted-foreground">Extracted:</span>
                            <span className="font-mono">{finding.extracted_value}</span>
                          </div>
                        )}
                        {finding.expected_value && (
                          <div className="flex justify-between">
                            <span className="text-muted-foreground">Expected:</span>
                            <span className="font-mono">{finding.expected_value}</span>
                          </div>
                        )}
                        {finding.page_number && (
                          <div className="flex justify-between">
                            <span className="text-muted-foreground">Page:</span>
                            <span>{finding.page_number}</span>
                          </div>
                        )}
                        {finding.evidence && (
                          <div className="mt-3 pt-3 border-t border-border">
                            <p className="text-muted-foreground">{finding.evidence}</p>
                          </div>
                        )}
                        <div className="mt-4 space-y-3 border-t border-border pt-4">
                          <label className="block text-sm font-medium">
                            Review status
                            <select
                              value={finding.review_status}
                              onChange={(event) =>
                                setFindings((current) =>
                                  current.map((item) =>
                                    item.id === finding.id
                                      ? { ...item, review_status: event.target.value }
                                      : item,
                                  ),
                                )
                              }
                              className="mt-1 block w-full rounded-md border border-input bg-background px-3 py-2"
                            >
                              <option value="open">Open</option>
                              <option value="accepted">Accepted</option>
                              <option value="resolved">Resolved</option>
                              <option value="needs_review">Needs review</option>
                            </select>
                          </label>
                          <label className="block text-sm font-medium">
                            Reviewer comments
                            <textarea
                              rows={3}
                              value={reviewerComments[finding.id] ?? ""}
                              onChange={(event) =>
                                setReviewerComments((current) => ({
                                  ...current,
                                  [finding.id]: event.target.value,
                                }))
                              }
                              className="mt-1 block w-full rounded-md border border-input bg-background px-3 py-2 font-normal"
                              placeholder="Add review notes"
                            />
                          </label>
                          <Button
                            onClick={() => handleSaveReview(finding)}
                            disabled={savingFindingId === finding.id}
                            variant="outline"
                            size="sm"
                          >
                            {savingFindingId === finding.id ? "Saving..." : "Save review"}
                          </Button>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              )}
            </TabsContent>

            <TabsContent value="extraction">
              <Card>
                <CardHeader>
                  <CardTitle>Extracted Data</CardTitle>
                </CardHeader>
                <CardContent>
                  {extractionResults.length === 0 ? (
                    <p className="text-muted-foreground text-center py-8">
                      Click "Extract Data" to begin extraction.
                    </p>
                  ) : (
                    <div className="space-y-2 max-h-96 overflow-y-auto">
                      {extractionResults.map((result, index) => (
                        <div
                          key={index}
                          className="flex items-center justify-between p-3 rounded-lg bg-muted/50"
                        >
                          <div>
                            <p className="font-medium text-foreground">{result.field_name}</p>
                            <p className="text-sm text-muted-foreground">{result.value}</p>
                          </div>
                          <div className="text-right">
                            <p className="text-xs text-muted-foreground">
                              Page {result.page_number}
                            </p>
                            {result.confidence !== undefined && (
                              <p className="text-xs text-muted-foreground">
                                {Math.round(result.confidence * 100)}% confidence
                              </p>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="preview">
              <Card>
                <CardHeader>
                  <CardTitle>Document Preview</CardTitle>
                </CardHeader>
                <CardContent>
                  <DocumentPreview
                    src={getApiUrl(`/api/audits/${auditId}/file`)}
                    filename={audit.filename}
                    mimeType={audit.mime_type}
                  />
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        </div>

        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Audit Summary</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Total Findings</span>
                <span className="text-2xl font-bold text-primary">{findings.length}</span>
              </div>
              <div className="space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span className="flex items-center gap-2">
                    <span className="h-2 w-2 rounded-full bg-destructive" />
                    Critical
                  </span>
                  <span className="font-semibold">{criticalCount}</span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="flex items-center gap-2">
                    <span className="h-2 w-2 rounded-full bg-warning" />
                    Major
                  </span>
                  <span className="font-semibold">{majorCount}</span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="flex items-center gap-2">
                    <span className="h-2 w-2 rounded-full bg-secondary" />
                    Minor
                  </span>
                  <span className="font-semibold">{minorCount}</span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="flex items-center gap-2">
                    <span className="h-2 w-2 rounded-full bg-muted-foreground" />
                    Review Required
                  </span>
                  <span className="font-semibold">{reviewCount}</span>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Audit Information</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 text-sm">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Status</span>
                <span className="font-medium">{audit.status}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">File Size</span>
                <span className="font-medium">
                  {(audit.file_size / 1024 / 1024).toFixed(2)} MB
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Created</span>
                <span className="font-medium">
                  {new Date(audit.created_at).toLocaleString()}
                </span>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
