import { useState } from "react";

const CATEGORIES = [
  {
    id: "produtos",
    label: "Produtos",
    icon: "📦",
    color: "#C07D2F",
    bg: "#FFF8F0",
    border: "#F0C080",
    accent: "#C07D2F",
  },
  {
    id: "fornecedores",
    label: "Fornecedores",
    icon: "🏢",
    color: "#1A7A6E",
    bg: "#F0FAF9",
    border: "#7ECDC6",
    accent: "#1A7A6E",
  },
  {
    id: "assistentes",
    label: "Assistentes",
    icon: "👥",
    color: "#5B3FA6",
    bg: "#F5F2FF",
    border: "#B5A0E0",
    accent: "#5B3FA6",
  },
  {
    id: "outros",
    label: "Outros",
    icon: "➕",
    color: "#C05020",
    bg: "#FFF5F0",
    border: "#F0A080",
    accent: "#C05020",
  },
];

const FIELD_TEMPLATES = {
  produtos: [
    { key: "descricao", label: "Descrição", type: "text", placeholder: "Ex: Caixa de papelão P" },
    { key: "quantidade", label: "Qtd", type: "number", placeholder: "0", small: true },
    { key: "unidade", label: "Unidade", type: "select", options: ["un", "cx", "kg", "m²", "h"], small: true },
    { key: "valor", label: "Valor Unit. (R$)", type: "number", placeholder: "0,00", small: true },
  ],
  fornecedores: [
    { key: "nome", label: "Nome / Empresa", type: "text", placeholder: "Ex: Transportadora XYZ" },
    { key: "servico", label: "Serviço", type: "text", placeholder: "Ex: Frete de mudança" },
    { key: "quantidade", label: "Qtd", type: "number", placeholder: "1", small: true },
    { key: "valor", label: "Valor (R$)", type: "number", placeholder: "0,00", small: true },
  ],
  assistentes: [
    { key: "nome", label: "Nome", type: "text", placeholder: "Ex: Assistente João" },
    { key: "funcao", label: "Função", type: "text", placeholder: "Ex: Embalagem e etiquetagem" },
    { key: "horas", label: "Horas", type: "number", placeholder: "8", small: true },
    { key: "valor", label: "R$/hora", type: "number", placeholder: "0,00", small: true },
  ],
  outros: [
    { key: "descricao", label: "Descrição", type: "text", placeholder: "Ex: Taxa de estacionamento" },
    { key: "categoria", label: "Categoria", type: "select", options: ["Deslocamento", "Taxa", "Aluguel", "Seguro", "Outros"] },
    { key: "quantidade", label: "Qtd", type: "number", placeholder: "1", small: true },
    { key: "valor", label: "Valor (R$)", type: "number", placeholder: "0,00", small: true },
  ],
};

function calcItemTotal(cat, item) {
  const q = parseFloat(item.quantidade) || 1;
  const v = parseFloat(item.valor) || 0;
  if (cat === "assistentes") return q * v; // horas × valor/hora
  return q * v;
}

function fmtBRL(v) {
  return v.toLocaleString("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function ItemRow({ cat, item, onRemove, onChange }) {
  const fields = FIELD_TEMPLATES[cat];
  const total = calcItemTotal(cat, item);
  const c = CATEGORIES.find((c) => c.id === cat);

  return (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: "1fr repeat(3, auto) 80px 36px",
        gap: "8px",
        alignItems: "center",
        padding: "10px 14px",
        background: "#fff",
        border: `1px solid #eee`,
        borderRadius: "10px",
        marginBottom: "8px",
        transition: "box-shadow 0.15s",
      }}
      onMouseEnter={(e) => (e.currentTarget.style.boxShadow = "0 2px 12px rgba(0,0,0,0.07)")}
      onMouseLeave={(e) => (e.currentTarget.style.boxShadow = "none")}
    >
      {fields.map((f) =>
        f.type === "select" ? (
          <select
            key={f.key}
            value={item[f.key] || ""}
            onChange={(e) => onChange(f.key, e.target.value)}
            style={{
              padding: "6px 8px",
              border: "1px solid #ddd",
              borderRadius: "7px",
              fontSize: "13px",
              background: "#fafafa",
              color: "#333",
              width: f.small ? "90px" : "100%",
              cursor: "pointer",
            }}
          >
            {f.options.map((o) => (
              <option key={o} value={o}>
                {o}
              </option>
            ))}
          </select>
        ) : (
          <input
            key={f.key}
            type={f.type}
            value={item[f.key] || ""}
            placeholder={f.placeholder}
            onChange={(e) => onChange(f.key, e.target.value)}
            style={{
              padding: "6px 10px",
              border: "1px solid #ddd",
              borderRadius: "7px",
              fontSize: "13px",
              background: "#fafafa",
              color: "#333",
              width: f.small ? "70px" : "100%",
              minWidth: f.small ? "60px" : undefined,
              boxSizing: "border-box",
            }}
          />
        )
      )}
      <div
        style={{
          textAlign: "right",
          fontSize: "13px",
          fontWeight: 600,
          color: c.accent,
          minWidth: "80px",
          fontFamily: "monospace",
        }}
      >
        R$ {fmtBRL(total)}
      </div>
      <button
        onClick={onRemove}
        style={{
          background: "none",
          border: "none",
          cursor: "pointer",
          color: "#bbb",
          fontSize: "16px",
          lineHeight: 1,
          padding: "4px",
          borderRadius: "6px",
          transition: "color 0.15s, background 0.15s",
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.color = "#e55";
          e.currentTarget.style.background = "#fff0f0";
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.color = "#bbb";
          e.currentTarget.style.background = "none";
        }}
        title="Remover"
      >
        ×
      </button>
    </div>
  );
}

export default function ItensCustos() {
  const [active, setActive] = useState("produtos");
  const [items, setItems] = useState({ produtos: [], fornecedores: [], assistentes: [], outros: [] });

  const addItem = (cat) => {
    const fields = FIELD_TEMPLATES[cat];
    const blank = Object.fromEntries(fields.map((f) => [f.key, f.type === "select" ? f.options[0] : ""]));
    setItems((prev) => ({ ...prev, [cat]: [...prev[cat], blank] }));
  };

  const removeItem = (cat, idx) => {
    setItems((prev) => ({ ...prev, [cat]: prev[cat].filter((_, i) => i !== idx) }));
  };

  const updateItem = (cat, idx, key, val) => {
    setItems((prev) => ({
      ...prev,
      [cat]: prev[cat].map((item, i) => (i === idx ? { ...item, [key]: val } : item)),
    }));
  };

  const catTotal = (cat) => items[cat].reduce((sum, item) => sum + calcItemTotal(cat, item), 0);
  const grandTotal = CATEGORIES.reduce((sum, c) => sum + catTotal(c.id), 0);
  const activeCat = CATEGORIES.find((c) => c.id === active);
  const fields = FIELD_TEMPLATES[active];

  return (
    <div
      style={{
        fontFamily: "'Nunito', 'Segoe UI', sans-serif",
        display: "flex",
        height: "calc(100vh - 120px)",
        minHeight: "500px",
        gap: "0",
        background: "#f4f5f8",
        borderRadius: "14px",
        overflow: "hidden",
        boxShadow: "0 4px 32px rgba(0,0,0,0.10)",
      }}
    >
      {/* SIDEBAR */}
      <div
        style={{
          width: "220px",
          flexShrink: 0,
          background: "#fff",
          borderRight: "1px solid #eee",
          display: "flex",
          flexDirection: "column",
          padding: "20px 0",
        }}
      >
        <div style={{ padding: "0 18px 16px", borderBottom: "1px solid #f0f0f0" }}>
          <div style={{ fontSize: "11px", fontWeight: 700, letterSpacing: "0.08em", color: "#aaa", textTransform: "uppercase" }}>
            Itens & Custos
          </div>
        </div>

        <div style={{ flex: 1, padding: "12px 10px", display: "flex", flexDirection: "column", gap: "4px" }}>
          {CATEGORIES.map((cat) => {
            const isActive = active === cat.id;
            const count = items[cat.id].length;
            const total = catTotal(cat.id);
            return (
              <button
                key={cat.id}
                onClick={() => setActive(cat.id)}
                style={{
                  display: "flex",
                  flexDirection: "column",
                  alignItems: "flex-start",
                  padding: "12px 14px",
                  borderRadius: "10px",
                  border: "none",
                  cursor: "pointer",
                  background: isActive ? cat.bg : "transparent",
                  borderLeft: isActive ? `3px solid ${cat.accent}` : "3px solid transparent",
                  transition: "all 0.15s",
                  textAlign: "left",
                  width: "100%",
                }}
                onMouseEnter={(e) => { if (!isActive) e.currentTarget.style.background = "#f8f8f8"; }}
                onMouseLeave={(e) => { if (!isActive) e.currentTarget.style.background = "transparent"; }}
              >
                <div style={{ display: "flex", alignItems: "center", gap: "8px", width: "100%" }}>
                  <span style={{ fontSize: "16px" }}>{cat.icon}</span>
                  <span
                    style={{
                      fontSize: "13px",
                      fontWeight: isActive ? 700 : 500,
                      color: isActive ? cat.accent : "#555",
                      flex: 1,
                    }}
                  >
                    {cat.label}
                  </span>
                  <span
                    style={{
                      fontSize: "11px",
                      fontWeight: 600,
                      background: isActive ? cat.accent : "#e8e8e8",
                      color: isActive ? "#fff" : "#888",
                      borderRadius: "20px",
                      padding: "1px 7px",
                      minWidth: "20px",
                      textAlign: "center",
                    }}
                  >
                    {count}
                  </span>
                </div>
                {total > 0 && (
                  <div
                    style={{
                      fontSize: "11px",
                      color: cat.accent,
                      fontWeight: 600,
                      marginTop: "4px",
                      marginLeft: "24px",
                      fontFamily: "monospace",
                    }}
                  >
                    R$ {fmtBRL(total)}
                  </div>
                )}
              </button>
            );
          })}
        </div>

        {/* Grand Total */}
        <div
          style={{
            margin: "10px",
            padding: "14px",
            background: "linear-gradient(135deg, #1A7A6E, #5B3FA6)",
            borderRadius: "12px",
            color: "#fff",
          }}
        >
          <div style={{ fontSize: "10px", fontWeight: 700, letterSpacing: "0.1em", opacity: 0.8, marginBottom: "4px", textTransform: "uppercase" }}>
            Total Geral
          </div>
          <div style={{ fontSize: "18px", fontWeight: 800, fontFamily: "monospace", letterSpacing: "-0.5px" }}>
            R$ {fmtBRL(grandTotal)}
          </div>
        </div>
      </div>

      {/* MAIN CONTENT */}
      <div style={{ flex: 1, display: "flex", flexDirection: "column", overflow: "hidden" }}>
        {/* Header */}
        <div
          style={{
            padding: "20px 28px 16px",
            background: "#fff",
            borderBottom: "1px solid #eee",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
            <div
              style={{
                width: "40px",
                height: "40px",
                borderRadius: "10px",
                background: activeCat.bg,
                border: `1px solid ${activeCat.border}`,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                fontSize: "20px",
              }}
            >
              {activeCat.icon}
            </div>
            <div>
              <div style={{ fontSize: "17px", fontWeight: 700, color: "#222" }}>{activeCat.label}</div>
              <div style={{ fontSize: "12px", color: "#999" }}>
                {items[active].length} {items[active].length === 1 ? "item" : "itens"} · R$ {fmtBRL(catTotal(active))}
              </div>
            </div>
          </div>
          <button
            onClick={() => addItem(active)}
            style={{
              display: "flex",
              alignItems: "center",
              gap: "7px",
              padding: "9px 18px",
              background: activeCat.accent,
              color: "#fff",
              border: "none",
              borderRadius: "9px",
              fontSize: "13px",
              fontWeight: 700,
              cursor: "pointer",
              boxShadow: `0 2px 10px ${activeCat.accent}40`,
              transition: "opacity 0.15s, transform 0.1s",
            }}
            onMouseEnter={(e) => (e.currentTarget.style.opacity = "0.88")}
            onMouseLeave={(e) => (e.currentTarget.style.opacity = "1")}
          >
            <span style={{ fontSize: "17px", lineHeight: 1 }}>+</span> Adicionar {activeCat.label.replace(/s$/, "")}
          </button>
        </div>

        {/* Column Headers */}
        {items[active].length > 0 && (
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "1fr repeat(3, auto) 80px 36px",
              gap: "8px",
              padding: "8px 28px",
              background: "#f9f9fb",
              borderBottom: "1px solid #eee",
            }}
          >
            {fields.map((f) => (
              <div
                key={f.key}
                style={{
                  fontSize: "10px",
                  fontWeight: 700,
                  color: "#aaa",
                  textTransform: "uppercase",
                  letterSpacing: "0.06em",
                  width: f.small ? (f.type === "select" ? "90px" : "70px") : undefined,
                }}
              >
                {f.label}
              </div>
            ))}
            <div style={{ fontSize: "10px", fontWeight: 700, color: "#aaa", textTransform: "uppercase", letterSpacing: "0.06em", textAlign: "right" }}>
              Subtotal
            </div>
            <div />
          </div>
        )}

        {/* Items List */}
        <div style={{ flex: 1, overflow: "auto", padding: "16px 28px" }}>
          {items[active].length === 0 ? (
            <div
              style={{
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                justifyContent: "center",
                height: "100%",
                color: "#ccc",
                gap: "14px",
              }}
            >
              <div
                style={{
                  width: "72px",
                  height: "72px",
                  borderRadius: "50%",
                  background: activeCat.bg,
                  border: `2px dashed ${activeCat.border}`,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  fontSize: "28px",
                }}
              >
                {activeCat.icon}
              </div>
              <div style={{ textAlign: "center" }}>
                <div style={{ fontSize: "15px", fontWeight: 600, color: "#bbb" }}>Nenhum item ainda</div>
                <div style={{ fontSize: "13px", color: "#ccc", marginTop: "4px" }}>
                  Clique em "+ Adicionar" para incluir {activeCat.label.toLowerCase()}
                </div>
              </div>
              <button
                onClick={() => addItem(active)}
                style={{
                  padding: "10px 22px",
                  background: activeCat.bg,
                  color: activeCat.accent,
                  border: `1.5px dashed ${activeCat.border}`,
                  borderRadius: "10px",
                  fontSize: "13px",
                  fontWeight: 700,
                  cursor: "pointer",
                  transition: "background 0.15s",
                }}
              >
                + Adicionar primeiro item
              </button>
            </div>
          ) : (
            items[active].map((item, idx) => (
              <ItemRow
                key={idx}
                cat={active}
                item={item}
                onRemove={() => removeItem(active, idx)}
                onChange={(key, val) => updateItem(active, idx, key, val)}
              />
            ))
          )}
        </div>

        {/* Footer subtotal */}
        {items[active].length > 0 && (
          <div
            style={{
              padding: "14px 28px",
              background: "#fff",
              borderTop: "1px solid #eee",
              display: "flex",
              justifyContent: "flex-end",
              alignItems: "center",
              gap: "10px",
            }}
          >
            <span style={{ fontSize: "13px", color: "#999" }}>Subtotal {activeCat.label}:</span>
            <span
              style={{
                fontSize: "16px",
                fontWeight: 800,
                color: activeCat.accent,
                fontFamily: "monospace",
                background: activeCat.bg,
                padding: "4px 14px",
                borderRadius: "8px",
              }}
            >
              R$ {fmtBRL(catTotal(active))}
            </span>
          </div>
        )}
      </div>
    </div>
  );
}
