import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { useNavigate } from "react-router-dom";

import { apiGet, apiUpload, type Paginated, type PriceList, type Supplier } from "../api";
import { EmptyRow, Loading, Pagination, StatusBadge } from "../components/ui";

export default function PriceListsPage() {
  const navigate = useNavigate();
  const [page, setPage] = useState(1);
  const [expanded, setExpanded] = useState<number | null>(null);

  const suppliers = useQuery({
    queryKey: ["suppliers-pl", page],
    queryFn: () => apiGet<Paginated<Supplier>>(`/suppliers/?page=${page}`),
  });

  return (
    <div className="stack">
      <div className="page-header">
        <h1>Прайс-листы</h1>
        <div className="sub">Нажмите на поставщика, чтобы раскрыть и загрузить его прайсы.</div>
      </div>

      <div className="card">
        <div className="card-header">Поставщики</div>
        <div className="table-wrap">
          <table className="tbl">
            <thead>
              <tr>
                <th>Поставщик</th>
                <th>ИНН</th>
                <th>Валюта</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {!suppliers.data ? (
                <Loading cols={4} />
              ) : suppliers.data.results.length === 0 ? (
                <EmptyRow cols={4} text="Сначала добавьте поставщиков на вкладке «Поставщики»." />
              ) : (
                suppliers.data.results.map((s) => (
                  <SupplierRow
                    key={s.id}
                    supplier={s}
                    expanded={expanded === s.id}
                    onToggle={() => setExpanded(expanded === s.id ? null : s.id)}
                    onOpen={(id) => navigate(`/price-lists/${id}`)}
                  />
                ))
              )}
            </tbody>
          </table>
        </div>
        <Pagination count={suppliers.data?.count ?? 0} page={page} onChange={setPage} />
      </div>
    </div>
  );
}

function SupplierRow({
  supplier,
  expanded,
  onToggle,
  onOpen,
}: {
  supplier: Supplier;
  expanded: boolean;
  onToggle: () => void;
  onOpen: (id: number) => void;
}) {
  return (
    <>
      <tr className={`selectable${expanded ? " selected" : ""}`} onClick={onToggle}>
        <td className="cell-strong">{supplier.name}</td>
        <td className="cell-num">{supplier.inn}</td>
        <td>
          <span className="badge gray">{supplier.currency}</span>
        </td>
        <td style={{ textAlign: "right" }}>
          <span className="chev">{expanded ? "˅" : "›"}</span>
        </td>
      </tr>
      {expanded && (
        <tr className="subrow">
          <td colSpan={4}>
            <SupplierPriceLists supplierId={supplier.id} onOpen={onOpen} />
          </td>
        </tr>
      )}
    </>
  );
}

function SupplierPriceLists({
  supplierId,
  onOpen,
}: {
  supplierId: number;
  onOpen: (id: number) => void;
}) {
  const qc = useQueryClient();
  const priceLists = useQuery({
    queryKey: ["price-lists", supplierId],
    queryFn: () => apiGet<Paginated<PriceList>>(`/price-lists/?supplier=${supplierId}&page_size=100`),
  });

  const upload = useMutation({
    mutationFn: (file: File) => {
      const form = new FormData();
      form.append("supplier", String(supplierId));
      form.append("file", file);
      return apiUpload<PriceList>("/price-lists/", form);
    },
    onSuccess: (created) => {
      qc.invalidateQueries({ queryKey: ["price-lists", supplierId] });
      onOpen(created.id);
    },
  });

  return (
    <div>
      <div className="row-flex" style={{ marginBottom: 10 }}>
        <b>Прайс-листы поставщика</b>
        <span className="spacer" />
        <label className="btn btn-primary btn-sm">
          Загрузить прайс (.xlsx)
          <input
            type="file"
            accept=".xlsx,.xls"
            style={{ display: "none" }}
            onChange={(e) => {
              const file = e.target.files?.[0];
              if (file) upload.mutate(file);
            }}
          />
        </label>
      </div>
      {!priceLists.data ? (
        <span className="muted">Загрузка…</span>
      ) : priceLists.data.results.length === 0 ? (
        <span className="muted">Загрузите первый прайс этого поставщика.</span>
      ) : (
        <table className="tbl">
          <thead>
            <tr>
              <th>Файл</th>
              <th>Загружен</th>
              <th>Статус</th>
              <th>Позиций</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {priceLists.data.results.map((pl) => (
              <tr key={pl.id}>
                <td className="cell-strong">{pl.source_filename}</td>
                <td className="muted">{new Date(pl.uploaded_at).toLocaleString("ru-RU")}</td>
                <td>
                  <StatusBadge status={pl.status} />
                </td>
                <td className="cell-num">{pl.items_count}</td>
                <td>
                  <div className="actions">
                    <button className="btn btn-sm" onClick={() => onOpen(pl.id)}>
                      Открыть
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
