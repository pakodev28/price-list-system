import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { useNavigate } from "react-router-dom";

import { apiGet, apiUpload, type Paginated, type PriceList, type Supplier } from "../api";

export default function PriceListsPage() {
  const navigate = useNavigate();
  const [selected, setSelected] = useState<number | null>(null);

  const suppliers = useQuery({
    queryKey: ["suppliers", ""],
    queryFn: () => apiGet<Paginated<Supplier>>("/suppliers/"),
  });

  return (
    <div>
      <h1>Прайс-листы</h1>
      <p className="muted">Выберите поставщика, загрузите и распарсите его прайс.</p>
      <table>
        <thead>
          <tr>
            <th>Поставщик</th>
            <th>ИНН</th>
            <th>Валюта</th>
            <th />
          </tr>
        </thead>
        <tbody>
          {suppliers.data?.results.map((s) => (
            <tr key={s.id}>
              <td>{s.name}</td>
              <td>{s.inn}</td>
              <td>{s.currency}</td>
              <td>
                <button onClick={() => setSelected(s.id)}>Прайс-листы</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {selected !== null && (
        <SupplierPriceLists
          supplierId={selected}
          onOpen={(id) => navigate(`/price-lists/${id}`)}
        />
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
    <div>
      <h2>Прайс-листы поставщика</h2>
      <form className="inline" onSubmit={(e) => e.preventDefault()}>
        <input
          type="file"
          accept=".xlsx,.xls"
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) upload.mutate(file);
          }}
        />
      </form>
      <table>
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
          {priceLists.data?.results.map((pl) => (
            <tr key={pl.id}>
              <td>{pl.source_filename}</td>
              <td>{new Date(pl.uploaded_at).toLocaleString("ru-RU")}</td>
              <td>{pl.status}</td>
              <td>{pl.items_count}</td>
              <td>
                <button onClick={() => onOpen(pl.id)}>Открыть</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
