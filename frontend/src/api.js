const API_BASE = "";

export async function checkHealth() {
  const res = await fetch(`${API_BASE}/api/health`);
  if (!res.ok) throw new Error("فشل الاتصال بالخادم");
  return res.json();
}

export async function checkCvHealth() {
  const res = await fetch(`${API_BASE}/api/cv-health`);
  if (!res.ok) return { available: false };
  return res.json();
}

export async function searchByName(text, birthYear) {
  const res = await fetch(`${API_BASE}/api/search/name`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, birth_year: birthYear || null }),
  });

  const data = await res.json();
  if (!res.ok) {
    throw new Error(data.detail || "فشل البحث بالاسم");
  }
  return data;
}

export async function searchByImage(file, queryName) {
  const form = new FormData();
  form.append("file", file);
  form.append("query_name", queryName || "");

  const res = await fetch(`${API_BASE}/api/search/image`, {
    method: "POST",
    body: form,
  });

  const data = await res.json();
  if (!res.ok) {
    throw new Error(data.detail || "فشل البحث بالصورة");
  }
  return data;
}
