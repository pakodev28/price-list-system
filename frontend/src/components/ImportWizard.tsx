import { useMutation, useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { apiGet, apiPost, type Estimate, type Preview } from "../api";

const FIELDS: { key: string; label: string }[] = [
  { key: "name", label: "Наименование" },
  { key: "article", label: "Артикул" },
  { key: "unit", label: "Ед. изм." },
  { key: "quantity", label: "Количество" },
  { key: "material_price", label: "Цена материалов" },
  { key: "installation_price", label: "Цена монтажа" },
];

export default function ImportWizard({
  estimate,
  onParsed,
}: {
  estimate: Estimate;
  onParsed: () => void;
}) {
  // null = let the backend auto-detect the header row.
  const [headerRow, setHeaderRow] = useState<number | null>(null);
  const [mapping, setMapping] = useState<Record<string, number>>({});

  const preview = useQuery({
    queryKey: ["preview", estimate.id, headerRow],
    queryFn: () =>
      apiGet<Preview>(
        `/estimates/${estimate.id}/preview/${
          headerRow === null ? "" : `?header_row=${headerRow}`
        }`,
      ),
  });

  const effectiveHeaderRow = headerRow ?? preview.data?.header_row ?? 0;

  const parse = useMutation({
    mutationFn: () =>
      apiPost(`/estimates/${estimate.id}/parse/`, {
        header_row: effectiveHeaderRow,
        sheet: "",
        mapping,
      }),
    onSuccess: onParsed,
  });

  const columns = preview.data?.columns ?? [];

  return (
    <div>
      <h2>Импорт сметы: {estimate.source_filename}</h2>
      {preview.isError && (
        <p className="muted">Не удалось прочитать файл: {String(preview.error)}</p>
      )}

      <form className="inline" onSubmit={(e) => e.preventDefault()}>
        <label>
          Строка заголовка:&nbsp;
          <input
            type="number"
            min={0}
            value={effectiveHeaderRow}
            onChange={(e) => setHeaderRow(Number(e.target.value))}
            style={{ width: 60 }}
          />
          {headerRow === null && <span className="muted"> (определена автоматически)</span>}
        </label>
      </form>

      <h3>Сопоставление колонок</h3>
      {FIELDS.map((f) => (
        <div key={f.key} className="inline">
          <label style={{ width: 160 }}>{f.label}</label>
          <select
            value={mapping[f.key] ?? ""}
            onChange={(e) => {
              const value = e.target.value;
              setMapping((m) => {
                const next = { ...m };
                if (value === "") delete next[f.key];
                else next[f.key] = Number(value);
                return next;
              });
            }}
          >
            <option value="">— нет —</option>
            {columns.map((c, i) => (
              <option key={i} value={i}>
                {i}: {c}
              </option>
            ))}
          </select>
        </div>
      ))}

      <h3>Превью</h3>
      <table>
        <thead>
          <tr>
            {columns.map((c, i) => (
              <th key={i}>
                {i}: {c}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {preview.data?.rows.slice(0, 10).map((row, ri) => (
            <tr key={ri}>
              {row.map((cell, ci) => (
                <td key={ci}>{cell}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>

      <p>
        <button
          disabled={mapping.name === undefined || parse.isPending}
          onClick={() => parse.mutate()}
        >
          Распарсить
        </button>
        {mapping.name === undefined && (
          <span className="muted"> — укажите колонку «Наименование»</span>
        )}
      </p>
    </div>
  );
}
