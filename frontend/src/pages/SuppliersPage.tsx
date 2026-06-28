import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { apiDelete, apiGet, apiPatch, apiPost, type Paginated, type Supplier } from "../api";
import { EmptyRow, Loading, Pagination } from "../components/ui";

const CURRENCIES = ["RUB", "USD", "EUR", "CNY"];
const EMPTY = { name: "", inn: "", currency: "RUB" };

export default function SuppliersPage() {
  const qc = useQueryClient();
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [form, setForm] = useState(EMPTY);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editForm, setEditForm] = useState(EMPTY);

  const { data } = useQuery({
    queryKey: ["suppliers", search, page],
    queryFn: () =>
      apiGet<Paginated<Supplier>>(
        `/suppliers/?search=${encodeURIComponent(search)}&page=${page}`,
      ),
  });

  const invalidate = () => qc.invalidateQueries({ queryKey: ["suppliers"] });
  const create = useMutation({
    mutationFn: () => apiPost<Supplier>("/suppliers/", form),
    onSuccess: () => {
      setForm(EMPTY);
      invalidate();
    },
  });
  const update = useMutation({
    mutationFn: () => apiPatch<Supplier>(`/suppliers/${editingId}/`, editForm),
    onSuccess: () => {
      setEditingId(null);
      invalidate();
    },
  });
  const remove = useMutation({
    mutationFn: (id: number) => apiDelete(`/suppliers/${id}/`),
    onSuccess: invalidate,
  });

  const startEdit = (s: Supplier) => {
    setEditingId(s.id);
    setEditForm({ name: s.name, inn: s.inn, currency: s.currency });
  };

  return (
    <div className="stack">
      <div className="page-header">
        <h1>Поставщики</h1>
        <div className="sub">Перевозчики и таможенные брокеры: название, ИНН, валюта.</div>
      </div>

      <div className="card card-pad">
        <form
          className="toolbar"
          onSubmit={(e) => {
            e.preventDefault();
            create.mutate();
          }}
        >
          <input
            className="input grow"
            placeholder="Название"
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
            required
          />
          <input
            className="input"
            placeholder="ИНН"
            value={form.inn}
            onChange={(e) => setForm({ ...form, inn: e.target.value })}
            required
          />
          <select
            className="select"
            value={form.currency}
            onChange={(e) => setForm({ ...form, currency: e.target.value })}
          >
            {CURRENCIES.map((c) => (
              <option key={c}>{c}</option>
            ))}
          </select>
          <button className="btn btn-primary" type="submit">
            Добавить
          </button>
        </form>
        {(create.isError || update.isError) && (
          <div className="alert error" style={{ marginTop: 12 }}>
            Ошибка: {String(create.error ?? update.error)}
          </div>
        )}
      </div>

      <div className="card">
        <div className="card-header">
          <span>Все поставщики</span>
          <input
            className="input sm"
            style={{ width: 240 }}
            placeholder="Поиск по названию или ИНН…"
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setPage(1);
            }}
          />
        </div>
        <div className="table-wrap">
          <table className="tbl">
            <thead>
              <tr>
                <th>Название</th>
                <th>ИНН</th>
                <th>Валюта</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {!data ? (
                <Loading cols={4} />
              ) : data.results.length === 0 ? (
                <EmptyRow cols={4} text="Поставщиков не найдено." />
              ) : (
                data.results.map((s) =>
                  editingId === s.id ? (
                    <tr key={s.id}>
                      <td>
                        <input
                          className="input sm"
                          value={editForm.name}
                          onChange={(e) => setEditForm({ ...editForm, name: e.target.value })}
                        />
                      </td>
                      <td>
                        <input
                          className="input sm"
                          value={editForm.inn}
                          onChange={(e) => setEditForm({ ...editForm, inn: e.target.value })}
                        />
                      </td>
                      <td>
                        <select
                          className="select sm"
                          value={editForm.currency}
                          onChange={(e) => setEditForm({ ...editForm, currency: e.target.value })}
                        >
                          {CURRENCIES.map((c) => (
                            <option key={c}>{c}</option>
                          ))}
                        </select>
                      </td>
                      <td>
                        <div className="actions">
                          <button className="btn btn-sm btn-primary" onClick={() => update.mutate()}>
                            Сохранить
                          </button>
                          <button className="btn btn-sm btn-ghost" onClick={() => setEditingId(null)}>
                            Отмена
                          </button>
                        </div>
                      </td>
                    </tr>
                  ) : (
                    <tr key={s.id}>
                      <td className="cell-strong">{s.name}</td>
                      <td className="cell-num">{s.inn}</td>
                      <td>
                        <span className="badge gray">{s.currency}</span>
                      </td>
                      <td>
                        <div className="actions">
                          <button className="btn btn-sm btn-ghost" onClick={() => startEdit(s)}>
                            Изменить
                          </button>
                          <button className="btn btn-sm btn-danger" onClick={() => remove.mutate(s.id)}>
                            Удалить
                          </button>
                        </div>
                      </td>
                    </tr>
                  ),
                )
              )}
            </tbody>
          </table>
        </div>
        <Pagination count={data?.count ?? 0} page={page} onChange={setPage} />
      </div>
    </div>
  );
}
