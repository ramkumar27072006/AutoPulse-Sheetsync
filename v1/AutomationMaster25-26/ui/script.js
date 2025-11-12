const API_URL = "https://script.google.com/macros/s/AKfycbxYourDeploymentID/exec";

async function loadDashboardData() {
  try {
    const response = await fetch(API_URL);
    const result = await response.json();

    if (!result.data || result.data.length === 0) {
      renderEmptyState("No data available or API issue.");
      return;
    }

    renderTable(result.data);
    renderChart(result.data);
    renderSummary(result.data);
  } catch (error) {
    console.error("Error fetching data:", error);
    renderEmptyState("Failed to load data. Check API or permissions.");
  }
}

function renderSummary(data) {
  const firstItem = data[0];
  document.getElementById("countryTitle").textContent = `Latest Update: ${firstItem.date}`;
  document.getElementById("updateTime").textContent = `Last Updated: ${new Date().toLocaleString()}`;
}

function renderTable(data) {
  const tableBody = document.querySelector("#dataTable tbody");
  tableBody.innerHTML = "";

  data.forEach((row) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${row.category}</td>
      <td>${row.latest}</td>
      <td>${row.previous}</td>
      <td>${row.growth ?? "--"}</td>
    `;
    tableBody.appendChild(tr);
  });
}

function renderChart(data) {
  const ctx = document.getElementById("chart").getContext("2d");
  const labels = data.map((r) => r.category);
  const latest = data.map((r) => r.latest);
  const previous = data.map((r) => r.previous);

  if (window.chartInstance) {
    window.chartInstance.destroy();
  }

  window.chartInstance = new Chart(ctx, {
    type: "bar",
    data: {
      labels,
      datasets: [
        {
          label: "Latest",
          data: latest,
          backgroundColor: "#3b82f6",
        },
        {
          label: "Previous",
          data: previous,
          backgroundColor: "#64748b",
        },
      ],
    },
    options: {
      responsive: true,
      scales: {
        y: {
          beginAtZero: true,
          grid: { color: "#475569" },
          ticks: { color: "#cbd5e1" },
        },
        x: {
          grid: { color: "#334155" },
          ticks: { color: "#cbd5e1" },
        },
      },
      plugins: {
        legend: {
          labels: { color: "#e2e8f0" },
        },
      },
    },
  });
}

function renderEmptyState(message) {
  const tableBody = document.querySelector("#dataTable tbody");
  tableBody.innerHTML = `<tr><td colspan="4">${message}</td></tr>`;
  document.getElementById("countryTitle").textContent = "No Data";
  document.getElementById("updateTime").textContent = "";
}

loadDashboardData();
