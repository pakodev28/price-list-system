import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
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

const STATUS_LABEL: Record<string, string> = {
  unmatched: "не сопоставлена",
  matched: "сопоставлена",
  no_match: "без соответствия",
};

function rowClass(item: EstimateItem): string {
  if (item.is_confident) return "row-green";
  if (item.match_status === "matched" || item.match_status === "no_match") return "row-red";
  return "row-gray";
}

export default function EstimatePage() {
  const { id } = useParams();
  const estimateId = Number(id);
  const qc = useQueryClient();

  const estimate = useQuery({
    queryKey: ["estimate", estimateId],
    queryFn: () => apiGet<Estimate>(`/estimates/${estimateId}/`),
    refetchInterval: (query) => {
      const data = query.state.data;
      if (!data) return false;
      const matching = data.match_progress > 0 && data.match_progress < 100;
      return data.status === "parsing" || matching ? 1000 : false;
    },
  });

  const items = useQuery({
    queryKey: ["estimate-items", estimateId],
    enabled: estimate.data?.status === "done",
    queryFn: () =>
      apiGet<Paginated<EstimateItem>>(`/estimate-items/?estimate=${estimateId}&page_size=500`),
    refetchInterval: () => {
      const data = estimate.data;
      return data && data.match_progress > 0 && data.match_progress < 100 ? 1500 : false;
    },
  });

  const autoMatch = useMutation({
    mutationFn: () => apiPost(`/estimates/${estimateId}/auto-match/`, {}),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["estimate", estimateId] }),
  });

  if (!estimate.data) return <p>Загрузка…</p>;

  if (estimate.data.status !== "done") {
    if (estimate.data.status === "parsing") return <p>Парсинг… {estimate.data.progress}%</p>;
    return (
      <ImportWizard
        estimate={estimate.data}
        onParsed={() => qc.invalidateQueries({ queryKey: ["estimate", estimateId] })}
      />
    );
  }

  const matching = estimate.data.match_progress > 0 && estimate.data.match_progress < 100;

  return (
    <div>
      <h1>Смета: {estimate.data.source_filename}</h1>
      {estimate.data.row_errors.length > 0 && (
        <p className="muted">
          ⚠ {estimate.data.row_errors.length} строк пропущено из-за ошибок при парсинге
        </p>
      )}
      <p>
        <button disabled={autoMatch.isPending || matching} onClick={() => autoMatch.mutate()}>
          ИИ-сопоставление
        </button>
        {matching && <span>&nbsp;&nbsp;{estimate.data.match_progress}%</span>}
      </p>
      <table>
        <thead>
          <tr>
            <th>#</th>
            <th>Наименование</th>
            <th>Кол-во</th>
            <th>Товар каталога</th>
            <th>Уверенность</th>
            <th>Действия</th>
          </tr>
        </thead>
        <tbody>
          {items.data?.results.map((item) => (
            <ItemRow key={item.id} item={item} onChanged={() => items.refetch()} />
          ))}
        </tbody>
      </table>
    </div>
  );
}

function ItemRow({ item, onChanged }: { item: EstimateItem; onChanged: () => void }) {
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
        <td>{item.row_number}</td>
        <td>{item.name}</td>
        <td>{item.quantity ?? "—"}</td>
        <td>
          {item.catalog_product ? (
            <span>
              {item.catalog_name}
              {item.catalog_article && (
                <span className="muted"> · {item.catalog_article}</span>
              )}
            </span>
          ) : (
            STATUS_LABEL[item.match_status]
          )}
        </td>
        <td>{item.confidence !== null ? `${Math.round(item.confidence * 100)}%` : "—"}</td>
        <td>
          <button onClick={() => setOpen((o) => !o)}>Кандидаты</button>{" "}
          <button onClick={() => noMatch.mutate()}>Без соответствия</button>
        </td>
      </tr>
      {open && (
        <tr>
          <td colSpan={6}>
            {candidates.isLoading && "Загрузка…"}
            {candidates.data?.length === 0 && <span className="muted">Нет кандидатов</span>}
            {candidates.data?.map((c) => (
              <div key={c.id} className="inline">
                <button onClick={() => assign.mutate(c.id)}>Выбрать</button>
                <span>
                  {c.article} — {c.name}
                </span>
                <span className="muted">({Math.round(c.score * 100)}%)</span>
              </div>
            ))}
          </td>
        </tr>
      )}
    </>
  );
}
