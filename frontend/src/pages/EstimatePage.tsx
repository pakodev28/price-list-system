import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";

import {
  apiGet,
  apiPost,
  type CandidateOption,
  type Estimate,
  type EstimateItem,
  type Paginated,
} from "../api";
import ImportWizard from "../components/ImportWizard";
import { EmptyRow, Loading, Pagination, Progress } from "../components/ui";

const STATUS_LABEL: Record<string, string> = {
  unmatched: "не сопоставлена",
  matched: "сопоставлена",
  no_match: "без соответствия",
};

const ESTIMATE_FIELDS = [
  { key: "name", label: "Наименование" },
  { key: "article", label: "Артикул" },
  { key: "unit", label: "Ед. изм." },
  { key: "quantity", label: "Количество" },
  { key: "material_price", label: "Цена материалов" },
  { key: "installation_price", label: "Цена монтажа" },
];

function rowClass(item: EstimateItem): string {
  if (item.is_confident) return "row-green";
  if (item.match_status === "matched" || item.match_status === "no_match") return "row-red";
  return "";
}

export default function EstimatePage() {
  const { id } = useParams();
  const estimateId = Number(id);
  const qc = useQueryClient();
  const [matchRunning, setMatchRunning] = useState(false);
  const [page, setPage] = useState(1);
  const [selected, setSelected] = useState<Set<number>>(new Set());

  const estimate = useQuery({
    queryKey: ["estimate", estimateId],
    queryFn: () => apiGet<Estimate>(`/estimates/${estimateId}/`),
    refetchInterval: (query) => {
      const data = query.state.data;
      if (!data) return false;
      return data.status === "parsing" || matchRunning ? 1000 : false;
    },
  });

  const items = useQuery({
    queryKey: ["estimate-items", estimateId, page],
    enabled: estimate.data?.status === "done",
    queryFn: () =>
      apiGet<Paginated<EstimateItem>>(`/estimate-items/?estimate=${estimateId}&page=${page}`),
    refetchInterval: () => (matchRunning ? 1500 : false),
  });

  const autoMatch = useMutation({
    mutationFn: (itemIds: number[] | undefined) =>
      apiPost(`/estimates/${estimateId}/auto-match/`, itemIds ? { item_ids: itemIds } : {}),
    onSuccess: () => {
      setMatchRunning(true);
      setSelected(new Set());
      qc.invalidateQueries({ queryKey: ["estimate", estimateId] });
    },
  });

  useEffect(() => {
    if (matchRunning && (estimate.data?.match_progress ?? 0) >= 100) {
      setMatchRunning(false);
      qc.invalidateQueries({ queryKey: ["estimate-items", estimateId] });
    }
  }, [matchRunning, estimate.data?.match_progress, qc, estimateId]);

  if (!estimate.data) {
    return (
      <div className="loading">
        <span className="spinner" />
        Загрузка…
      </div>
    );
  }

  if (estimate.data.status !== "done") {
    if (estimate.data.status === "parsing") {
      return (
        <div className="stack">
          <div className="page-header">
            <h1>Смета</h1>
            <div className="sub">{estimate.data.source_filename}</div>
          </div>
          <div className="card card-pad">
            <div className="row-flex">
              <span className="badge amber">
                <span className="dot" />
                парсинг
              </span>
              <Progress value={estimate.data.progress} />
            </div>
          </div>
        </div>
      );
    }
    return (
      <ImportWizard
        resourceUrl={`/estimates/${estimateId}`}
        sourceFilename={estimate.data.source_filename}
        fields={ESTIMATE_FIELDS}
        onParsed={() => qc.invalidateQueries({ queryKey: ["estimate", estimateId] })}
      />
    );
  }

  const pageItems = items.data?.results ?? [];
  const pageIds = pageItems.map((it) => it.id);
  const allOnPageSelected = pageIds.length > 0 && pageIds.every((id) => selected.has(id));

  const toggle = (itemId: number) =>
    setSelected((prev) => {
      const next = new Set(prev);
      next.has(itemId) ? next.delete(itemId) : next.add(itemId);
      return next;
    });

  const toggleAll = () =>
    setSelected((prev) => {
      const next = new Set(prev);
      pageIds.forEach((id) => (allOnPageSelected ? next.delete(id) : next.add(id)));
      return next;
    });

  const runMatch = () => autoMatch.mutate(selected.size ? [...selected] : undefined);

  return (
    <div className="stack">
      <div className="page-header row-flex">
        <div>
          <h1>Смета</h1>
          <div className="sub">
            {estimate.data.source_filename} · {estimate.data.items_count} позиций
          </div>
        </div>
        <div className="spacer" />
        {matchRunning ? (
          <span className="row-flex">
            <span className="spinner" />
            <span className="muted">Сопоставление…</span>
          </span>
        ) : (
          <button className="btn btn-primary" disabled={autoMatch.isPending} onClick={runMatch}>
            {selected.size ? `✨ Сопоставить выбранные (${selected.size})` : "✨ ИИ-сопоставление"}
          </button>
        )}
      </div>

      {estimate.data.row_errors.length > 0 && (
        <div className="alert warn">
          ⚠ {estimate.data.row_errors.length} строк пропущено из-за ошибок при парсинге.
        </div>
      )}

      <div className="card">
        <div className="table-wrap">
          <table className="tbl">
            <thead>
              <tr>
                <th style={{ width: 36 }}>
                  <input
                    type="checkbox"
                    className="check"
                    checked={allOnPageSelected}
                    onChange={toggleAll}
                  />
                </th>
                <th>#</th>
                <th>Наименование</th>
                <th>Кол-во</th>
                <th>Товар каталога</th>
                <th>Уверенность</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {!items.data ? (
                <Loading cols={7} />
              ) : pageItems.length === 0 ? (
                <EmptyRow cols={7} text="Нет позиций." />
              ) : (
                pageItems.map((item) => (
                  <ItemRow
                    key={item.id}
                    item={item}
                    checked={selected.has(item.id)}
                    onToggle={() => toggle(item.id)}
                    onChanged={() => items.refetch()}
                  />
                ))
              )}
            </tbody>
          </table>
        </div>
        <Pagination count={items.data?.count ?? 0} page={page} onChange={setPage} />
      </div>
    </div>
  );
}

function ItemRow({
  item,
  checked,
  onToggle,
  onChanged,
}: {
  item: EstimateItem;
  checked: boolean;
  onToggle: () => void;
  onChanged: () => void;
}) {
  const [open, setOpen] = useState(false);

  const candidates = useQuery({
    queryKey: ["candidates", item.id],
    enabled: open,
    queryFn: () => apiGet<CandidateOption[]>(`/estimate-items/${item.id}/candidates/`),
  });

  const assign = useMutation({
    mutationFn: (productId: number) =>
      apiPost(`/estimate-items/${item.id}/assign/`, { catalog_product: productId }),
    onSuccess: () => {
      setOpen(false);
      onChanged();
    },
  });
  const noMatch = useMutation({
    mutationFn: () => apiPost(`/estimate-items/${item.id}/no-match/`, {}),
    onSuccess: onChanged,
  });

  return (
    <>
      <tr className={rowClass(item)}>
        <td>
          <input type="checkbox" className="check" checked={checked} onChange={onToggle} />
        </td>
        <td className="cell-num">{item.row_number}</td>
        <td className="cell-strong">{item.name}</td>
        <td>{item.quantity ?? "—"}</td>
        <td>
          {item.catalog_product ? (
            <span>
              {item.catalog_name}
              {item.catalog_article && <span className="muted"> · {item.catalog_article}</span>}
            </span>
          ) : (
            <span className="badge gray">{STATUS_LABEL[item.match_status]}</span>
          )}
        </td>
        <td>
          {item.confidence !== null ? (
            <span className={`badge ${item.is_confident ? "green" : "red"}`}>
              {Math.round(item.confidence * 100)}%
            </span>
          ) : (
            <span className="muted">—</span>
          )}
        </td>
        <td>
          <div className="actions">
            <button className="btn btn-sm btn-ghost" onClick={() => setOpen((o) => !o)}>
              Кандидаты
            </button>
            <button className="btn btn-sm btn-ghost" onClick={() => noMatch.mutate()}>
              Без соответствия
            </button>
          </div>
        </td>
      </tr>
      {open && (
        <tr className="subrow">
          <td colSpan={7}>
            {candidates.isLoading && <span className="muted">Загрузка…</span>}
            {candidates.data?.length === 0 && <span className="muted">Нет кандидатов</span>}
            {candidates.data?.map((c) => (
              <div key={c.id} className="candidate">
                <button className="btn btn-sm btn-primary" onClick={() => assign.mutate(c.id)}>
                  Выбрать
                </button>
                <span className="cell-strong">{c.name}</span>
                <span className="muted">{c.article}</span>
                <span className="spacer" />
                <span className="badge gray">{Math.round(c.score * 100)}%</span>
              </div>
            ))}
          </td>
        </tr>
      )}
    </>
  );
}
