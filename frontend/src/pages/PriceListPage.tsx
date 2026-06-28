import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";

import {
  apiGet,
  apiPost,
  type CandidateOption,
  type Paginated,
  type PriceList,
  type PriceListItem,
} from "../api";
import ImportWizard from "../components/ImportWizard";
import { EmptyRow, Loading, Pagination, Progress } from "../components/ui";

const PRICE_LIST_FIELDS = [
  { key: "article", label: "Артикул" },
  { key: "name", label: "Наименование" },
  { key: "unit", label: "Ед. изм." },
  { key: "price", label: "Цена" },
];

export default function PriceListPage() {
  const { id } = useParams();
  const priceListId = Number(id);
  const qc = useQueryClient();
  const [matchRunning, setMatchRunning] = useState(false);
  const [page, setPage] = useState(1);
  const [selected, setSelected] = useState<Set<number>>(new Set());

  const priceList = useQuery({
    queryKey: ["price-list", priceListId],
    queryFn: () => apiGet<PriceList>(`/price-lists/${priceListId}/`),
    refetchInterval: (query) => {
      const data = query.state.data;
      if (!data) return false;
      return data.status === "parsing" || matchRunning ? 1000 : false;
    },
  });

  const items = useQuery({
    queryKey: ["price-list-items", priceListId, page],
    enabled: priceList.data?.status === "done",
    queryFn: () =>
      apiGet<Paginated<PriceListItem>>(`/price-list-items/?price_list=${priceListId}&page=${page}`),
    refetchInterval: () => (matchRunning ? 1500 : false),
  });

  const autoMatch = useMutation({
    mutationFn: (itemIds: number[] | undefined) =>
      apiPost(`/price-lists/${priceListId}/auto-match/`, itemIds ? { item_ids: itemIds } : {}),
    onSuccess: () => {
      setMatchRunning(true);
      setSelected(new Set());
      qc.invalidateQueries({ queryKey: ["price-list", priceListId] });
    },
  });

  useEffect(() => {
    if (matchRunning && (priceList.data?.match_progress ?? 0) >= 100) {
      setMatchRunning(false);
      qc.invalidateQueries({ queryKey: ["price-list-items", priceListId] });
    }
  }, [matchRunning, priceList.data?.match_progress, qc, priceListId]);

  if (!priceList.data) {
    return (
      <div className="loading">
        <span className="spinner" />
        Загрузка…
      </div>
    );
  }

  if (priceList.data.status !== "done") {
    if (priceList.data.status === "parsing") {
      return (
        <div className="stack">
          <div className="page-header">
            <h1>Прайс-лист</h1>
            <div className="sub">{priceList.data.source_filename}</div>
          </div>
          <div className="card card-pad">
            <div className="row-flex">
              <span className="badge amber">
                <span className="dot" />
                парсинг
              </span>
              <Progress value={priceList.data.progress} />
            </div>
          </div>
        </div>
      );
    }
    return (
      <ImportWizard
        resourceUrl={`/price-lists/${priceListId}`}
        sourceFilename={priceList.data.source_filename}
        fields={PRICE_LIST_FIELDS}
        onParsed={() => qc.invalidateQueries({ queryKey: ["price-list", priceListId] })}
      />
    );
  }

  const pageItems = items.data?.results ?? [];
  const pageIds = pageItems.map((it) => it.id);
  const allOnPageSelected = pageIds.length > 0 && pageIds.every((id) => selected.has(id));

  const toggle = (itemId: number) =>
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(itemId)) next.delete(itemId);
      else next.add(itemId);
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
          <h1>Прайс-лист</h1>
          <div className="sub">
            {priceList.data.source_filename} · {priceList.data.items_count} позиций
          </div>
        </div>
        <div className="spacer" />
        {matchRunning ? (
          <span className="row-flex">
            <span className="spinner" />
            <span className="muted">Привязка…</span>
          </span>
        ) : (
          <button className="btn btn-primary" disabled={autoMatch.isPending} onClick={runMatch}>
            {selected.size ? `✨ Привязать выбранные (${selected.size})` : "✨ ИИ-привязка к каталогу"}
          </button>
        )}
      </div>

      {priceList.data.row_errors.length > 0 && (
        <div className="alert warn">
          ⚠ {priceList.data.row_errors.length} строк пропущено из-за ошибок при парсинге.
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
                <th>Артикул</th>
                <th>Наименование</th>
                <th>Цена</th>
                <th>Товар каталога</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {!items.data ? (
                <Loading cols={7} />
              ) : pageItems.length === 0 ? (
                <EmptyRow cols={7} text="Нет позиций." />
              ) : (
                pageItems.map((it) => (
                  <PriceItemRow
                    key={it.id}
                    item={it}
                    checked={selected.has(it.id)}
                    onToggle={() => toggle(it.id)}
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

function PriceItemRow({
  item,
  checked,
  onToggle,
  onChanged,
}: {
  item: PriceListItem;
  checked: boolean;
  onToggle: () => void;
  onChanged: () => void;
}) {
  const [open, setOpen] = useState(false);

  const candidates = useQuery({
    queryKey: ["pl-candidates", item.id],
    enabled: open,
    queryFn: () => apiGet<CandidateOption[]>(`/price-list-items/${item.id}/candidates/`),
  });

  const assign = useMutation({
    mutationFn: (productId: number) =>
      apiPost(`/price-list-items/${item.id}/assign/`, { catalog_product: productId }),
    onSuccess: () => {
      setOpen(false);
      onChanged();
    },
  });
  const createProduct = useMutation({
    mutationFn: () => apiPost(`/price-list-items/${item.id}/create-product/`, {}),
    onSuccess: onChanged,
  });
  const unlink = useMutation({
    mutationFn: () => apiPost(`/price-list-items/${item.id}/unlink/`, {}),
    onSuccess: onChanged,
  });

  return (
    <>
      <tr className={item.catalog_product ? "row-green" : ""}>
        <td>
          <input type="checkbox" className="check" checked={checked} onChange={onToggle} />
        </td>
        <td className="cell-num">{item.row_number}</td>
        <td className="cell-num">{item.article || "—"}</td>
        <td className="cell-strong">{item.name}</td>
        <td>{item.price ?? "—"}</td>
        <td>
          {item.catalog_product ? (
            <span>
              {item.catalog_name}
              {item.catalog_article && <span className="muted"> · {item.catalog_article}</span>}
            </span>
          ) : (
            <span className="badge gray">не привязано</span>
          )}
        </td>
        <td>
          <div className="actions">
            <button className="btn btn-sm btn-ghost" onClick={() => setOpen((o) => !o)}>
              Кандидаты
            </button>
            {item.catalog_product ? (
              <button className="btn btn-sm btn-ghost" onClick={() => unlink.mutate()}>
                Отвязать
              </button>
            ) : (
              <button className="btn btn-sm btn-ghost" onClick={() => createProduct.mutate()}>
                Создать в каталоге
              </button>
            )}
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
