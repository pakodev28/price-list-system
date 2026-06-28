import type { ReactNode } from "react";

const STEPS: { title: string; body: ReactNode }[] = [
  {
    title: "Поставщики",
    body: (
      <>
        Заведите перевозчиков и таможенных брокеров: <b>название, ИНН, валюта</b>. Список ищется и
        редактируется прямо в строке. У каждого поставщика — свои прайс-листы.
      </>
    ),
  },
  {
    title: "Прайс-листы",
    body: (
      <>
        Откройте поставщика → <b>«Загрузить прайс (.xlsx)»</b>. Укажите, какие колонки файла
        соответствуют артикулу, наименованию, цене и единице, посмотрите превью и запустите парсинг
        (идёт в фоне с прогрессом). Затем привяжите позиции к каталогу: <b>«Кандидаты»</b> (выбрать
        вручную), <b>«Создать в каталоге»</b> или <b>«ИИ-привязка»</b>.
      </>
    ),
  },
  {
    title: "Каталог",
    body: (
      <>
        Эталонный справочник услуг и товаров (с кодами ТН ВЭД) — к нему привязываются и прайсы, и
        сметы. Можно вести вручную (с группами) или наполнять из прайсов кнопкой «Создать в
        каталоге».
      </>
    ),
  },
  {
    title: "Проекты и сметы",
    body: (
      <>
        Создайте сделку (проект) → загрузите смету из Excel, настройте колонки (наименование,
        артикул, ед., количество, цена) и распарсите. Позиции попадут в таблицу.
      </>
    ),
  },
  {
    title: "Сопоставление с каталогом",
    body: (
      <>
        В смете нажмите <b>«ИИ-сопоставление»</b> — система подберёт товар каталога для каждой
        позиции и покажет уверенность. Можно сопоставлять <b>только выбранные</b> строки (отметьте
        галочками). Правьте вручную: <b>«Кандидаты»</b> или <b>«Без соответствия»</b>.
      </>
    ),
  },
];

export default function HelpPage() {
  return (
    <div className="stack">
      <div className="page-header">
        <h1>Справка</h1>
        <div className="sub">
          Сервис для учёта прайс-листов перевозчиков и брокеров, каталога услуг/товаров и смет по
          импортным сделкам Китай → РФ с сопоставлением через ИИ.
        </div>
      </div>

      <div className="card">
        <div className="card-header">Как пользоваться — по шагам</div>
        <div className="help-section">
          {STEPS.map((step, index) => (
            <div className="help-step" key={step.title}>
              <div className="num">{index + 1}</div>
              <div className="body">
                <b>{step.title}.</b> {step.body}
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="card">
        <div className="card-header">Подсказки</div>
        <div className="help-section" style={{ display: "flex", flexDirection: "column", gap: 10 }}>
          <div className="row-flex">
            <span className="badge green">95%</span>
            <span className="muted">зелёный — модель уверена в сопоставлении</span>
          </div>
          <div className="row-flex">
            <span className="badge red">40%</span>
            <span className="muted">красный — низкая уверенность, проверьте вручную</span>
          </div>
          <div className="row-flex">
            <span className="badge gray">без соответствия</span>
            <span className="muted">в каталоге нет подходящего товара</span>
          </div>
          <div className="muted">
            ИИ можно запускать по всей смете или по выбранным позициям. Большие списки и таблицы
            разбиты на страницы; в каталоге и поставщиках работает поиск.
          </div>
        </div>
      </div>
    </div>
  );
}
