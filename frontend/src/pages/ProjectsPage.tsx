import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { useNavigate } from "react-router-dom";

import { apiGet, apiPost, apiUpload, type Estimate, type Paginated, type Project } from "../api";
import { EmptyRow, Loading, StatusBadge } from "../components/ui";

export default function ProjectsPage() {
  const qc = useQueryClient();
  const navigate = useNavigate();
  const [name, setName] = useState("");
  const [selected, setSelected] = useState<number | null>(null);

  const projects = useQuery({
    queryKey: ["projects"],
    queryFn: () => apiGet<Paginated<Project>>("/projects/"),
  });

  const createProject = useMutation({
    mutationFn: () => apiPost<Project>("/projects/", { name }),
    onSuccess: () => {
      setName("");
      qc.invalidateQueries({ queryKey: ["projects"] });
    },
  });

  return (
    <div className="stack">
      <div className="page-header">
        <h1>Проекты</h1>
        <div className="sub">Проекты содержат сметы. Выберите проект, чтобы открыть его сметы.</div>
      </div>

      <div className="card card-pad">
        <form
          className="toolbar"
          onSubmit={(e) => {
            e.preventDefault();
            createProject.mutate();
          }}
        >
          <input
            className="input grow"
            placeholder="Название проекта"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
          />
          <button className="btn btn-primary" type="submit">
            Создать проект
          </button>
        </form>
      </div>

      <div className="card">
        <div className="card-header">Проекты</div>
        <div className="table-wrap">
          <table className="tbl">
            <thead>
              <tr>
                <th>Проект</th>
                <th>Смет</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {!projects.data ? (
                <Loading cols={3} />
              ) : projects.data.results.length === 0 ? (
                <EmptyRow cols={3} text="Проектов пока нет." />
              ) : (
                projects.data.results.map((p) => (
                  <tr
                    key={p.id}
                    className={`selectable${selected === p.id ? " selected" : ""}`}
                    onClick={() => setSelected(p.id)}
                  >
                    <td className="cell-strong">{p.name}</td>
                    <td className="cell-num">{p.estimates_count}</td>
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
        <ProjectEstimates projectId={selected} onOpen={(id) => navigate(`/estimates/${id}`)} />
      )}
    </div>
  );
}

function ProjectEstimates({
  projectId,
  onOpen,
}: {
  projectId: number;
  onOpen: (id: number) => void;
}) {
  const qc = useQueryClient();
  const estimates = useQuery({
    queryKey: ["estimates", projectId],
    queryFn: () => apiGet<Paginated<Estimate>>(`/estimates/?project=${projectId}`),
  });

  const upload = useMutation({
    mutationFn: (file: File) => {
      const form = new FormData();
      form.append("project", String(projectId));
      form.append("file", file);
      return apiUpload<Estimate>("/estimates/", form);
    },
    onSuccess: (created) => {
      qc.invalidateQueries({ queryKey: ["estimates", projectId] });
      onOpen(created.id);
    },
  });

  return (
    <div className="card">
      <div className="card-header">
        <span>Сметы проекта</span>
        <label className="btn btn-primary btn-sm">
          Загрузить смету (.xlsx)
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
            {!estimates.data ? (
              <Loading cols={5} />
            ) : estimates.data.results.length === 0 ? (
              <EmptyRow cols={5} text="Загрузите первую смету этого проекта." />
            ) : (
              estimates.data.results.map((es) => (
                <tr key={es.id}>
                  <td className="cell-strong">{es.source_filename}</td>
                  <td className="muted">{new Date(es.uploaded_at).toLocaleString("ru-RU")}</td>
                  <td>
                    <StatusBadge status={es.status} />
                  </td>
                  <td className="cell-num">{es.items_count}</td>
                  <td>
                    <div className="actions">
                      <button className="btn btn-sm" onClick={() => onOpen(es.id)}>
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
