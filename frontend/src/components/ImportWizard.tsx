import { useMutation, useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { apiGet, apiPost, type Preview } from "../api";

export interface ImportFieldDef {
  key: string;
  label: string;
}

/** Generic Excel import wizard: preview → column mapping → background parse.
 *  Reused for both estimates and price lists via `resourceUrl` + `fields`.
 *  `headerRow` defaults to null, letting the backend auto-detect it. */
export default function ImportWizard({
  resourceUrl,
  sourceFilename,
  fields,
  onParsed,
}: {
  resourceUrl: string;
  sourceFilename: string;
  fields: ImportFieldDef[];
  onParsed: () => void;
}) {
  const [headerRow, setHeaderRow] = useState<number | null>(null);
  const [mapping, setMapping] = useState<Record<string, number>>({});

  const preview = useQuery({
    queryKey: ["preview", resourceUrl, headerRow],
    queryFn: () =>
      apiGet<Preview>(
        `${resourceUrl}/preview/${headerRow === null ? "" : `?header_row=${headerRow}`}`,
      ),
  });

  const effectiveHeaderRow = headerRow ?? preview.data?.header_row ?? 0;

  const parse = useMutation({
    mutationFn: () =>
      apiPost(`${resourceUrl}/parse/`, {
        header_row: effectiveHeaderRow,
        sheet: "",
        mapping,
      }),
    onSuccess: onParsed,
  });

  const columns = preview.data?.columns ?? [];

  return (
    <div className="stack">
      <div className="page-header">
        <h1>Импорт файла</h1>
        <div className="sub">{sourceFilename}</div>
      </div>

      <div className="card card-pad">
        <div className="row-flex">
          <span className="muted">Строка заголовка</span>
          <input
            className="input sm"
            type="number"
            min={0}
            style={{ width: 80 }}
            value={effectiveHeaderRow}
            onChange={(e) => setHeaderRow(Number(e.target.value))}
          />
          {headerRow === null && <span className="badge blue">определена автоматически</span>}
        </div>
        {preview.isError && (
          <div className="alert error" style={{ marginTop: 12 }}>
            Не удалось прочитать файл: {String(preview.error)}
          </div>
        )}
      </div>

      <div className="card">
        <div className="card-header">Сопоставление колонок</div>
        <div className="card-pad stack" style={{ gap: 10 }}>
          {fields.map((f) => (
            <div key={f.key} className="row-flex">
              <span className="field-label">{f.label}</span>
              <select
                className="select sm"
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
        </div>
      </div>

      <div className="card">
        <div className="card-header">Превью</div>
        <div className="table-wrap">
          <table className="tbl">
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
        </div>
      </div>

      <div className="row-flex">
        <button
          className="btn btn-primary"
          disabled={mapping.name === undefined || parse.isPending}
          onClick={() => parse.mutate()}
        >
          Распарсить
        </button>
        {mapping.name === undefined && (
          <span className="muted">Укажите колонку «Наименование»</span>
        )}
      </div>
    </div>
  );
}
