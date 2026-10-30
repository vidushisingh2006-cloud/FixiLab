import { createFileRoute, Link } from "@tanstack/react-router";
import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Upload, X, FileText, ArrowRight, AlertCircle, CheckCircle2, Loader2 } from "lucide-react";
import { Logo } from "@/components/landing/primitives";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { getApiError, getApiUrl } from "@/lib/api";

const TITLE = "FixiLab | Start Your First Audit";
const DESC =
  "Upload your analytical worksheet to identify calculation discrepancies, documentation gaps and potential inconsistencies.";

export const Route = createFileRoute("/audit/")({
  head: () => ({
    meta: [
      { title: TITLE },
      { name: "description", content: DESC },
      { name: "robots", content: "noindex" },
    ],
  }),
  component: Audit,
});

const MAX_FILE_SIZE = 15 * 1024 * 1024; // 15 MB
const ACCEPTED_TYPES = ["application/pdf", "image/png", "image/jpeg", "image/jpg"];
const ACCEPTED_EXTENSIONS = [".pdf", ".png", ".jpg", ".jpeg"];

export function Audit() {
  const [file, setFile] = useState<File | null>(null);
  const [dragActive, setDragActive] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [auditId, setAuditId] = useState<string | null>(null);

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      validateAndSetFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      validateAndSetFile(e.target.files[0]);
    }
  };

  const validateAndSetFile = (selectedFile: File) => {
    setError(null);

    const extension = selectedFile.name.slice(selectedFile.name.lastIndexOf(".")).toLowerCase();
    if (
      !ACCEPTED_TYPES.includes(selectedFile.type) &&
      !(selectedFile.type === "" && ACCEPTED_EXTENSIONS.includes(extension))
    ) {
      setError("Invalid file type. Please upload a PDF, PNG, JPG, or JPEG file.");
      return;
    }

    if (selectedFile.size > MAX_FILE_SIZE) {
      setError("File size exceeds 15 MB limit. Please upload a smaller file.");
      return;
    }

    setFile(selectedFile);
  };

  const handleRemoveFile = () => {
    setFile(null);
    setError(null);
    setAuditId(null);
    setUploadProgress(0);
  };

  const handleUpload = async () => {
    if (!file) return;

    setUploading(true);
    setError(null);

    const formData = new FormData();
    formData.append("file", file);
    formData.append("filename", file.name);
    formData.append("file_size", file.size.toString());
    formData.append("mime_type", file.type);

    try {
      const response = await fetch(getApiUrl("/api/audits"), {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error(await getApiError(response));
      }

      const data = await response.json();
      setAuditId(data.id);
      setUploadProgress(100);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to upload file.");
      console.error(err);
    } finally {
      setUploading(false);
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return "0 Bytes";
    const k = 1024;
    const sizes = ["Bytes", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + " " + sizes[i];
  };

  return (
    <div className="mx-auto max-w-4xl px-5">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="text-center"
      >
        <h1 className="text-4xl font-extrabold text-primary sm:text-5xl">
          Start Your First Audit
        </h1>
        <p className="mt-4 text-lg text-muted-foreground">
          Upload your analytical worksheet to identify calculation discrepancies, documentation
          gaps and potential inconsistencies.
        </p>
      </motion.div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.1 }}
        className="mt-10"
      >
        {!file ? (
          <div
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
            className={`relative rounded-3xl border-2 border-dashed p-12 text-center transition-all ${
              dragActive
                ? "border-secondary bg-secondary/5"
                : "border-border bg-card hover:border-secondary/50"
            }`}
          >
            <input
              type="file"
              id="file-upload"
              className="hidden"
              accept=".pdf,.png,.jpg,.jpeg"
              onChange={handleFileSelect}
            />
            <label htmlFor="file-upload" className="flex cursor-pointer flex-col items-center">
              <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-muted">
                <Upload className="h-8 w-8 text-primary" />
              </div>
              <p className="text-lg font-semibold text-foreground">
                Drag and drop your worksheet here
              </p>
              <p className="mt-2 text-sm text-muted-foreground">or click to browse files</p>
              <p className="mt-4 text-xs text-muted-foreground">
                Supported formats: PDF, PNG, JPG, JPEG (max 15 MB)
              </p>
            </label>
          </div>
        ) : (
          <div className="rounded-3xl border border-border bg-card p-6 shadow-soft">
            <div className="flex items-start justify-between">
              <div className="flex items-center gap-4">
                <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-muted">
                  <FileText className="h-6 w-6 text-primary" />
                </div>
                <div>
                  <p className="font-semibold text-foreground">{file.name}</p>
                  <p className="text-sm text-muted-foreground">
                    {formatFileSize(file.size)} · {file.type}
                  </p>
                </div>
              </div>
              <button
                onClick={handleRemoveFile}
                className="rounded-lg p-2 text-muted-foreground transition hover:bg-muted hover:text-destructive"
                aria-label="Remove file"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            {uploading && (
              <div className="mt-6">
                <div className="mb-2 flex items-center justify-between text-sm">
                  <span className="text-muted-foreground">Uploading...</span>
                  <span className="font-semibold text-foreground">{uploadProgress}%</span>
                </div>
                <Progress value={uploadProgress} className="h-2" />
              </div>
            )}

            {!uploading && (
              <div className="mt-6 flex gap-3">
                <Button
                  onClick={handleUpload}
                  className="flex-1 bg-primary text-primary-foreground hover:bg-primary/90"
                >
                  Upload and Start Audit
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Button>
              </div>
            )}
          </div>
        )}

        {error && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="mt-4 flex items-center gap-2 rounded-xl border border-destructive/30 bg-destructive/5 p-4 text-sm text-destructive"
          >
            <AlertCircle className="h-5 w-5 shrink-0" />
            {error}
          </motion.div>
        )}

        {auditId && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="mt-4 flex items-center gap-2 rounded-xl border border-secondary/30 bg-secondary/5 p-4 text-sm text-foreground"
          >
            <CheckCircle2 className="h-5 w-5 shrink-0 text-secondary" />
            <span className="font-semibold">Upload successful!</span>
            <Link
              to="/audit/$auditId"
              params={{ auditId }}
              className="ml-auto font-semibold text-primary hover:text-secondary"
            >
              Continue to Document Review
              <ArrowRight className="ml-1 inline h-4 w-4" />
            </Link>
          </motion.div>
        )}
      </motion.div>

      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.5, delay: 0.2 }}
        className="mt-12 rounded-2xl border border-border bg-muted/30 p-6"
      >
        <h3 className="text-sm font-bold text-primary">What happens next?</h3>
        <div className="mt-4 space-y-3 text-sm text-muted-foreground">
          <div className="flex items-start gap-3">
            <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-primary text-[10px] font-bold text-primary-foreground">
              1
            </div>
            <p>Document preview and data extraction</p>
          </div>
          <div className="flex items-start gap-3">
            <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-primary text-[10px] font-bold text-primary-foreground">
              2
            </div>
            <p>Intelligent validation and calculation checks</p>
          </div>
          <div className="flex items-start gap-3">
            <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-primary text-[10px] font-bold text-primary-foreground">
              3
            </div>
            <p>Review findings and generate audit report</p>
          </div>
        </div>
      </motion.div>

      <motion.p
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.5, delay: 0.3 }}
        className="mt-8 text-center text-xs text-muted-foreground"
      >
        Your documents are processed securely. Uploaded files are stored temporarily and are not
        shared with third parties.
      </motion.p>
    </div>
  );
}
