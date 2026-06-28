import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { apiDelete, apiGet, apiPost, type Paginated, type Supplier } from "../api";

const CURRENCIES = ["RUB", "USD", "EUR", "CNY"];

export default function SuppliersPage() {
  const qc = useQueryClient();
  const [search, setSearch] = useState("");
  const [form, setForm] = useState({ name: "", inn: "", currency: "RUB" });

  const { data } = useQuery({
    queryKey: ["suppliers", search],
    queryFn: () => apiGet<Paginated<Supplier>>(`/suppliers/?search=${encodeURIComponent(search)}`),
  });

  const create = useMutation({
    mutationFn: () => apiPost<Supplier>("/suppliers/", form),
    onSuccess: () => {
      setForm({ name: "", inn: "", currency: "RUB" });
      qc.invalidateQueries({ queryKey: ["suppliers"] });
    },
  });

  const remove = useMutation({
    mutationFn: (id: number) => apiDelete(`/suppliers/${id}/`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["suppliers"] }),
  });

  return (
    <div>
      <h1>Поставщики</h1>
      <form
        className="inline"
        onSubmit={(e) => {
          e.preventDefault();
          create.mutate();
        }}
      >
        <input
          placeholder="Название"
          value={form.name}
          onChange={(e) => setForm({ ...form, name: e.target.value })}
          required
        />
        <input
          placeholder="ИНН"
          value={form.inn}
          onChange={(e) => setForm({ ...form, inn: e.target.value })}
          required
        />
        <select value={form.currency} onChange={(e) => setForm({ ...form, currency: e.target.value })}>
          {CURRENCIES.map((c) => (
            <option key={c}>{c}</option>
          ))}
        </select>
        <button type="submit">Добавить</button>
      </form>

      <form className="inline" onSubmit={(e) => e.preventDefault()}>
        <input placeholder="Поиск…" value={search} onChange={(e) => setSearch(e.target.value)} />
      </form>

      {create.isError && <p className="muted">Ошибка: {String(create.error)}</p>}

      <table>
        <thead>
          <tr>
            <th>Название</th>
            <th>ИНН</th>
            <th>Валюта</th>
            <th />
          </tr>
        </thead>
        <tbody>
          {data?.results.map((s) => (
            <tr key={s.id}>
              <td>{s.name}</td>
              <td>{s.inn}</td>
              <td>{s.currency}</td>
              <td>
                <button onClick={() => remove.mutate(s.id)}>Удалить</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
