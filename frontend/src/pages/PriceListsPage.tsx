import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { useNavigate } from "react-router-dom";

import { apiGet, apiUpload, type Paginated, type PriceList, type Supplier } from "../api";
import { EmptyRow, Loading, StatusBadge } from "../components/ui";

export default function PriceListsPage() {
  const navigate = useNavigate();
  const [selected, setSelected] = useState<number | null>(null);

  const suppliers = useQuery({
    queryKey: ["suppliers", ""],
    queryFn: () => apiGet<Paginated<Supplier>>("/suppliers/"),
  });

  return (
    <div className="stack">
      <div className="page-header">
        <h1>Прайс-листы</h1>
        <div className="sub">Выберите поставщика, чтобы загрузить и распарсить его прайс.</div>
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
                  <tr
                    key={s.id}
                    className={`selectable${selected === s.id ? " selected" : ""}`}
                    onClick={() => setSelected(s.id)}
                  >
                    <td className="cell-strong">{s.name}</td>
                    <td className="cell-num">{s.inn}</td>
                    <td>
                      <span className="badge gray">{s.currency}</span>
                    </td>
                    <td style={{ textAlign: "right" }}>
                      <span className="chev">›</span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {selected !== null && (
        <SupplierPriceLists supplierId={selected} onOpen={(id) => navigate(`/price-lists/${id}`)} />
      )}
    </div>
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
    queryFn: () => apiGet<Paginated<PriceList>>(`/price-lists/?supplier=${supplierId}`),
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
    <div className="card">
      <div className="card-header">
        <span>Прайс-листы поставщика</span>
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
      <div className="table-wrap">
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
            {!priceLists.data ? (
              <Loading cols={5} />
            ) : priceLists.data.results.length === 0 ? (
              <EmptyRow cols={5} text="Загрузите первый прайс этого поставщика." />
            ) : (
              priceLists.data.results.map((pl) => (
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
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
