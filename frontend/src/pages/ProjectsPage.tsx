import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { useNavigate } from "react-router-dom";

import { apiGet, apiPost, apiUpload, type Estimate, type Paginated, type Project } from "../api";
import { EmptyRow, Loading, Pagination, StatusBadge } from "../components/ui";

export default function ProjectsPage() {
  const qc = useQueryClient();
  const navigate = useNavigate();
  const [name, setName] = useState("");
  const [page, setPage] = useState(1);
  const [expanded, setExpanded] = useState<number | null>(null);

  const projects = useQuery({
    queryKey: ["projects", page],
    queryFn: () => apiGet<Paginated<Project>>(`/projects/?page=${page}`),
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
        <div className="sub">Сделки содержат сметы. Нажмите на проект, чтобы раскрыть его сметы.</div>
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
            placeholder="Название сделки / проекта"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
          />
          <button className="btn btn-primary" type="submit">
            Создать
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
                  <ProjectRow
                    key={p.id}
                    project={p}
                    expanded={expanded === p.id}
                    onToggle={() => setExpanded(expanded === p.id ? null : p.id)}
                    onOpen={(id) => navigate(`/estimates/${id}`)}
                  />
                ))
              )}
            </tbody>
          </table>
        </div>
        <Pagination count={projects.data?.count ?? 0} page={page} onChange={setPage} />
      </div>
    </div>
  );
}

function ProjectRow({
  project,
  expanded,
  onToggle,
  onOpen,
}: {
  project: Project;
  expanded: boolean;
  onToggle: () => void;
  onOpen: (id: number) => void;
}) {
  return (
    <>
      <tr className={`selectable${expanded ? " selected" : ""}`} onClick={onToggle}>
        <td className="cell-strong">{project.name}</td>
        <td className="cell-num">{project.estimates_count}</td>
        <td style={{ textAlign: "right" }}>
          <span className="chev">{expanded ? "˅" : "›"}</span>
        </td>
      </tr>
      {expanded && (
        <tr className="subrow">
          <td colSpan={3}>
            <ProjectEstimates projectId={project.id} onOpen={onOpen} />
          </td>
        </tr>
      )}
    </>
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
    queryFn: () => apiGet<Paginated<Estimate>>(`/estimates/?project=${projectId}&page_size=100`),
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
    <div>
      <div className="row-flex" style={{ marginBottom: 10 }}>
        <b>Сметы проекта</b>
        <span className="spacer" />
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
      {!estimates.data ? (
        <span className="muted">Загрузка…</span>
      ) : estimates.data.results.length === 0 ? (
        <span className="muted">Загрузите первую смету этой сделки.</span>
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
            {estimates.data.results.map((es) => (
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
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
