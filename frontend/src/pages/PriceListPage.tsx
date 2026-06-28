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

  if (!priceList.data) return <p>Загрузка…</p>;

  if (priceList.data.status !== "done") {
    if (priceList.data.status === "parsing") return <p>Парсинг… {priceList.data.progress}%</p>;
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
    <div>
      <h1>Прайс-лист: {priceList.data.source_filename}</h1>
      {priceList.data.row_errors.length > 0 && (
        <p className="muted">
          ⚠ {priceList.data.row_errors.length} строк пропущено из-за ошибок при парсинге
        </p>
      )}
      <p>
        <button disabled={autoMatch.isPending || matching} onClick={() => autoMatch.mutate()}>
          ИИ-привязка к каталогу
        </button>
        {matching && <span>&nbsp;&nbsp;{priceList.data.match_progress}%</span>}
      </p>
      <table>
        <thead>
          <tr>
            <th>#</th>
            <th>Артикул</th>
            <th>Наименование</th>
            <th>Цена</th>
            <th>Товар каталога</th>
            <th>Действия</th>
          </tr>
        </thead>
        <tbody>
          {items.data?.results.map((it) => (
            <PriceItemRow key={it.id} item={it} onChanged={() => items.refetch()} />
          ))}
        </tbody>
      </table>
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
      <tr className={item.catalog_product ? "row-green" : "row-gray"}>
        <td>{item.row_number}</td>
        <td>{item.article}</td>
        <td>{item.name}</td>
        <td>{item.price ?? "—"}</td>
        <td>
          {item.catalog_product ? (
            <span>
              {item.catalog_name}
              {item.catalog_article && <span className="muted"> · {item.catalog_article}</span>}
            </span>
          ) : (
            "—"
          )}
        </td>
        <td>
          <button onClick={() => setOpen((o) => !o)}>Кандидаты</button>{" "}
          {item.catalog_product ? (
            <button onClick={() => unlink.mutate()}>Отвязать</button>
          ) : (
            <button onClick={() => createProduct.mutate()}>Создать в каталоге</button>
          )}
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
