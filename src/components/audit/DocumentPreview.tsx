interface DocumentPreviewProps {
  src: string;
  filename: string;
  mimeType: string;
}

export function DocumentPreview({ src, filename, mimeType }: DocumentPreviewProps) {
  return (
    <div className="overflow-hidden rounded-lg border border-border bg-muted/30">
      <div className="border-b border-border p-3 text-sm font-medium text-foreground">
        {filename}
      </div>
      <div className="flex min-h-[400px] items-center justify-center p-3">
        {mimeType === "application/pdf" ? (
          <iframe
            src={src}
            title={`Preview of ${filename}`}
            className="h-[70vh] min-h-[500px] w-full rounded-md bg-background"
          />
        ) : mimeType.startsWith("image/") ? (
          <img
            src={src}
            alt={`Preview of ${filename}`}
            className="max-h-[70vh] max-w-full object-contain"
          />
        ) : (
          <p className="text-muted-foreground">Preview is not available for this file type.</p>
        )}
      </div>
    </div>
  );
}
