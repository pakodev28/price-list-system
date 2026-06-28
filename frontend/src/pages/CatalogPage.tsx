import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import {
  apiDelete,
  apiGet,
  apiPatch,
  apiPost,
  type CatalogProduct,
  type Paginated,
  type ProductGroup,
} from "../api";
import { EmptyRow, Loading, Pagination } from "../components/ui";

interface ProductForm {
  article: string;
  name: string;
  unit: string;
  group: number | "";
}

const EMPTY: ProductForm = { article: "", name: "", unit: "", group: "" };

function GroupSelect({
  value,
  groups,
  onChange,
}: {
  value: number | "";
  groups: ProductGroup[];
  onChange: (v: number | "") => void;
}) {
  return (
    <select
      className="select sm"
      value={value}
      onChange={(e) => onChange(e.target.value === "" ? "" : Number(e.target.value))}
    >
      <option value="">— без группы —</option>
      {groups.map((g) => (
        <option key={g.id} value={g.id}>
          {g.name}
        </option>
      ))}
    </select>
  );
}

export default function CatalogPage() {
  const qc = useQueryClient();
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [form, setForm] = useState<ProductForm>(EMPTY);
  const [groupName, setGroupName] = useState("");
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editForm, setEditForm] = useState<ProductForm>(EMPTY);

  const products = useQuery({
    queryKey: ["catalog", search, page],
    queryFn: () =>
      apiGet<Paginated<CatalogProduct>>(
        `/products/?search=${encodeURIComponent(search)}&page=${page}`,
      ),
  });
  const groups = useQuery({
    queryKey: ["product-groups"],
    queryFn: () => apiGet<Paginated<ProductGroup>>("/product-groups/?page_size=500"),
  });
  const groupOptions = groups.data?.results ?? [];

  const invalidate = () => qc.invalidateQueries({ queryKey: ["catalog"] });
  const toPayload = (f: ProductForm) => ({ ...f, group: f.group === "" ? null : f.group });

  const create = useMutation({
    mutationFn: () => apiPost<CatalogProduct>("/products/", toPayload(form)),
    onSuccess: () => {
      setForm(EMPTY);
      invalidate();
    },
  });
  const update = useMutation({
    mutationFn: () => apiPatch<CatalogProduct>(`/products/${editingId}/`, toPayload(editForm)),
    onSuccess: () => {
      setEditingId(null);
      invalidate();
    },
  });
  const remove = useMutation({
    mutationFn: (id: number) => apiDelete(`/products/${id}/`),
    onSuccess: invalidate,
  });
  const createGroup = useMutation({
    mutationFn: () => apiPost<ProductGroup>("/product-groups/", { name: groupName }),
    onSuccess: () => {
      setGroupName("");
      qc.invalidateQueries({ queryKey: ["product-groups"] });
    },
  });

  const startEdit = (p: CatalogProduct) => {
    setEditingId(p.id);
    setEditForm({ article: p.article, name: p.name, unit: p.unit, group: p.group ?? "" });
  };

  return (
    <div className="stack">
      <div className="page-header">
        <h1>Каталог</h1>
        <div className="sub">
          Эталонный справочник услуг и товаров (ТН ВЭД) — к нему привязываются прайсы и сметы.
        </div>
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
            className="input"
            placeholder="Артикул / код"
            value={form.article}
            onChange={(e) => setForm({ ...form, article: e.target.value })}
            required
          />
          <input
            className="input grow"
            placeholder="Наименование"
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
            required
          />
          <input
            className="input"
            style={{ width: 110 }}
            placeholder="Ед."
            value={form.unit}
            onChange={(e) => setForm({ ...form, unit: e.target.value })}
          />
          <GroupSelect
            value={form.group}
            groups={groupOptions}
            onChange={(v) => setForm({ ...form, group: v })}
          />
          <button className="btn btn-primary" type="submit">
            Добавить
          </button>
        </form>
        <form
          className="toolbar"
          style={{ marginTop: 12 }}
          onSubmit={(e) => {
            e.preventDefault();
            createGroup.mutate();
          }}
        >
          <input
            className="input"
            placeholder="Новая группа"
            value={groupName}
            onChange={(e) => setGroupName(e.target.value)}
            required
          />
          <button className="btn" type="submit">
            Добавить группу
          </button>
        </form>
      </div>

      <div className="card">
        <div className="card-header">
          <span>Товары и услуги</span>
          <input
            className="input sm"
            style={{ width: 240 }}
            placeholder="Поиск по артикулу или названию…"
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
                <th>Артикул</th>
                <th>Наименование</th>
                <th>Ед.</th>
                <th>Группа</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {!products.data ? (
                <Loading cols={5} />
              ) : products.data.results.length === 0 ? (
                <EmptyRow cols={5} text="Ничего не найдено." />
              ) : (
                products.data.results.map((p) =>
                  editingId === p.id ? (
                    <tr key={p.id}>
                      <td>
                        <input
                          className="input sm"
                          value={editForm.article}
                          onChange={(e) => setEditForm({ ...editForm, article: e.target.value })}
                        />
                      </td>
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
                          style={{ width: 80 }}
                          value={editForm.unit}
                          onChange={(e) => setEditForm({ ...editForm, unit: e.target.value })}
                        />
                      </td>
                      <td>
                        <GroupSelect
                          value={editForm.group}
                          groups={groupOptions}
                          onChange={(v) => setEditForm({ ...editForm, group: v })}
                        />
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
                    <tr key={p.id}>
                      <td className="cell-num">{p.article}</td>
                      <td className="cell-strong">{p.name}</td>
                      <td>{p.unit || "—"}</td>
                      <td>
                        {p.group_name ? (
                          <span className="badge blue">{p.group_name}</span>
                        ) : (
                          <span className="muted">—</span>
                        )}
                      </td>
                      <td>
                        <div className="actions">
                          <button className="btn btn-sm btn-ghost" onClick={() => startEdit(p)}>
                            Изменить
                          </button>
                          <button className="btn btn-sm btn-danger" onClick={() => remove.mutate(p.id)}>
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
        <Pagination count={products.data?.count ?? 0} page={page} onChange={setPage} />
      </div>
    </div>
  );
}
