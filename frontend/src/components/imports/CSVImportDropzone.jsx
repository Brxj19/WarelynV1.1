export function CSVImportDropzone({ file, onFileChange }) {
  return (
    <label className="flex cursor-pointer flex-col items-center justify-center rounded-2xl border border-dashed border-warelyn-border bg-slate-50 px-6 py-8 text-center transition hover:border-warelyn-primary hover:bg-blue-50/40">
      <span className="text-sm font-semibold text-warelyn-text">Upload product CSV or XLSX</span>
      <span className="mt-2 text-xs text-warelyn-muted">Choose a .csv or .xlsx file with product master data. Stock quantities are not imported.</span>
      <input
        accept=".csv,text/csv,.xlsx,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        className="sr-only"
        type="file"
        onChange={(event) => onFileChange(event.target.files?.[0] ?? null)}
      />
      {file ? <span className="mt-4 rounded-full bg-white px-3 py-1 text-xs font-semibold text-warelyn-primary ring-1 ring-blue-200">{file.name}</span> : null}
    </label>
  );
}
