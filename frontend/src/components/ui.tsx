// Small shared presentational helpers.

const STATUS: Record<string, { cls: string; label: string }> = {
  pending: { cls: "gray", label: "ожидает" },
  parsing: { cls: "amber", label: "парсинг" },
  done: { cls: "green", label: "готово" },
  failed: { cls: "red", label: "ошибка" },
};

export function StatusBadge({ status }: { status: string }) {
  const s = STATUS[status] ?? { cls: "gray", label: status };
  return (
    <span className={`badge ${s.cls}`}>
      <span className="dot" />
      {s.label}
    </span>
  );
}

export function Progress({ value }: { value: number }) {
  return (
    <div className="progress-row">
      <div className="progress">
        <span style={{ width: `${value}%` }} />
      </div>
      <span className="muted">{value}%</span>
    </div>
  );
}

export function Loading({ cols }: { cols: number }) {
  return (
    <tr>
      <td colSpan={cols}>
        <div className="loading">
          <span className="spinner" />
          Загрузка…
        </div>
      </td>
    </tr>
  );
}

export function EmptyRow({ cols, text }: { cols: number; text: string }) {
  return (
    <tr>
      <td colSpan={cols}>
        <div className="empty">{text}</div>
      </td>
    </tr>
  );
}

export const PAGE_SIZE = 25;

export function Pagination({
  count,
  page,
  onChange,
}: {
  count: number;
  page: number;
  onChange: (page: number) => void;
}) {
  if (count <= PAGE_SIZE) return null;
  const pages = Math.ceil(count / PAGE_SIZE);
  const from = (page - 1) * PAGE_SIZE + 1;
  const to = Math.min(count, page * PAGE_SIZE);
  return (
    <div className="pager">
      <span className="muted">
        {from}–{to} из {count}
      </span>
      <span className="spacer" />
      <button className="btn btn-sm" disabled={page <= 1} onClick={() => onChange(page - 1)}>
        ‹ Назад
      </button>
      <span className="muted">
        {page} / {pages}
      </span>
      <button className="btn btn-sm" disabled={page >= pages} onClick={() => onChange(page + 1)}>
        Вперёд ›
      </button>
    </div>
  );
}
