import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { apiGet, apiPost, type CatalogProduct, type Paginated } from "../api";

export default function CatalogPage() {
  const qc = useQueryClient();
  const [search, setSearch] = useState("");
  const [form, setForm] = useState({ article: "", name: "", unit: "" });

  const { data } = useQuery({
    queryKey: ["catalog", search],
    queryFn: () => apiGet<Paginated<CatalogProduct>>(`/products/?search=${encodeURIComponent(search)}`),
  });

  const create = useMutation({
    mutationFn: () => apiPost<CatalogProduct>("/products/", form),
    onSuccess: () => {
      setForm({ article: "", name: "", unit: "" });
      qc.invalidateQueries({ queryKey: ["catalog"] });
    },
  });

  return (
    <div>
      <h1>Каталог товаров</h1>
      <form
        className="inline"
        onSubmit={(e) => {
          e.preventDefault();
          create.mutate();
        }}
      >
        <input
          placeholder="Артикул"
          value={form.article}
          onChange={(e) => setForm({ ...form, article: e.target.value })}
          required
        />
        <input
          placeholder="Наименование"
          value={form.name}
          onChange={(e) => setForm({ ...form, name: e.target.value })}
          required
        />
        <input
          placeholder="Ед. изм."
          value={form.unit}
          onChange={(e) => setForm({ ...form, unit: e.target.value })}
        />
        <button type="submit">Добавить</button>
      </form>

      <form className="inline" onSubmit={(e) => e.preventDefault()}>
        <input placeholder="Поиск…" value={search} onChange={(e) => setSearch(e.target.value)} />
      </form>

      <table>
        <thead>
          <tr>
            <th>Артикул</th>
            <th>Наименование</th>
            <th>Ед. изм.</th>
            <th>Группа</th>
          </tr>
        </thead>
        <tbody>
          {data?.results.map((p) => (
            <tr key={p.id}>
              <td>{p.article}</td>
              <td>{p.name}</td>
              <td>{p.unit}</td>
              <td>{p.group_name ?? "—"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
