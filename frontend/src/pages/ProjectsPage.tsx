import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { useNavigate } from "react-router-dom";

import { apiGet, apiPost, apiUpload, type Estimate, type Paginated, type Project } from "../api";

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
    <div>
      <h1>Проекты</h1>
      <form
        className="inline"
        onSubmit={(e) => {
          e.preventDefault();
          createProject.mutate();
        }}
      >
        <input
          placeholder="Название проекта"
          value={name}
          onChange={(e) => setName(e.target.value)}
          required
        />
        <button type="submit">Создать</button>
      </form>

      <table>
        <thead>
          <tr>
            <th>Проект</th>
            <th>Смет</th>
            <th />
          </tr>
        </thead>
        <tbody>
          {projects.data?.results.map((p) => (
            <tr key={p.id}>
              <td>{p.name}</td>
              <td>{p.estimates_count}</td>
              <td>
                <button onClick={() => setSelected(p.id)}>Сметы</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {selected !== null && (
        <Estimates projectId={selected} onOpen={(id) => navigate(`/estimates/${id}`)} />
      )}
    </div>
  );
}

function Estimates({ projectId, onOpen }: { projectId: number; onOpen: (id: number) => void }) {
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
    <div>
      <h2>Сметы проекта</h2>
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
            <th>Статус</th>
            <th>Позиций</th>
            <th />
          </tr>
        </thead>
        <tbody>
          {estimates.data?.results.map((es) => (
            <tr key={es.id}>
              <td>{es.source_filename}</td>
              <td>{es.status}</td>
              <td>{es.items_count}</td>
              <td>
                <button onClick={() => onOpen(es.id)}>Открыть</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
