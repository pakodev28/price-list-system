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
