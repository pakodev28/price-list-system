import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
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
import { EmptyRow, Loading, Progress } from "../components/ui";

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

  const priceList = useQuery({
    queryKey: ["price-list", priceListId],
    queryFn: () => apiGet<PriceList>(`/price-lists/${priceListId}/`),
    refetchInterval: (query) => {
      const data = query.state.data;
      if (!data) return false;
      const matching = data.match_progress > 0 && data.match_progress < 100;
      return data.status === "parsing" || matching ? 1000 : false;
    },
  });

  const items = useQuery({
    queryKey: ["price-list-items", priceListId],
    enabled: priceList.data?.status === "done",
    queryFn: () =>
      apiGet<Paginated<PriceListItem>>(
        `/price-list-items/?price_list=${priceListId}&page_size=500`,
      ),
    refetchInterval: () => {
      const data = priceList.data;
      return data && data.match_progress > 0 && data.match_progress < 100 ? 1500 : false;
    },
  });

  const autoMatch = useMutation({
    mutationFn: () => apiPost(`/price-lists/${priceListId}/auto-match/`, {}),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["price-list", priceListId] }),
  });

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

  const matching = priceList.data.match_progress > 0 && priceList.data.match_progress < 100;

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
        {matching ? (
          <Progress value={priceList.data.match_progress} />
        ) : (
          <button
            className="btn btn-primary"
            disabled={autoMatch.isPending}
            onClick={() => autoMatch.mutate()}
          >
            ✨ ИИ-привязка к каталогу
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
                <Loading cols={6} />
              ) : items.data.results.length === 0 ? (
                <EmptyRow cols={6} text="Нет позиций." />
              ) : (
                items.data.results.map((it) => (
                  <PriceItemRow key={it.id} item={it} onChanged={() => items.refetch()} />
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

function PriceItemRow({ item, onChanged }: { item: PriceListItem; onChanged: () => void }) {
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
          <td colSpan={6}>
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
