// test_statistics.js

let chartInstance = null;
let currentExportData = {};
const canvasContainer = document.querySelector(".analytics-canvas");
let selectedDate = null;
let selectedMonth = null;
let selectedYear = null;

// Получить статистику по тестам
async function fetchTestCountData() {
    try {
        const response = await fetch('/api/test-count-data/');
        if (!response.ok) {
            throw new Error(`Ошибка HTTP: ${response.status}`);
        }
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Ошибка при получении данных:', error.message);
        return [];
    }
}

function processTestCountData(data) {
    let start, end;

    if (selectedDate) {
        const selected = new Date(selectedDate);
        start = new Date(selected);
        end = new Date(selected);
    } else if (selectedMonth !== null && selectedYear !== null) {
        start = new Date(selectedYear, selectedMonth, 1);
        end = new Date(selectedYear, selectedMonth + 1, 0);
        end.setHours(23, 59, 59, 999);
    } else {
        ({ start, end } = getDateRange());
    }

    const allDates = generateDateRange(start, end);
    const groupedData = {};
    allDates.forEach(date => {
        const key = formatDate(date);
        groupedData[key] = 0;
    });

    data.forEach(({ created_at }) => {
        const dateKey = formatDate(new Date(created_at));
        if (groupedData[dateKey] !== undefined) {
            groupedData[dateKey]++;
        }
    });

    currentExportData = {
        meta: {
            dateRange: { start: formatDate(start), end: formatDate(end) },
            generatedAt: new Date().toISOString()
        },
        data: groupedData
    };

    return groupedData;
}

function renderTestCountChart(data, chartType) {
    const groupedData = processTestCountData(data);
    const labels = Object.keys(groupedData).sort();
    const counts = labels.map(date => groupedData[date]);

    const filteredLabels = labels.filter((date, index) => counts[index] > 0);
    const filteredData = filteredLabels.map(date => groupedData[date]);
    const backgroundColors = filteredLabels.map(() => getRandomColor());

    canvasContainer.innerHTML = '<canvas id="testCountChart"></canvas>';
    const ctx = document.getElementById("testCountChart").getContext("2d");

    if (chartInstance) chartInstance.destroy();

    if (chartType === 'bar') {
        chartInstance = new Chart(ctx, {
            type: 'bar',
            data: {
                labels,
                datasets: [{
                    label: 'Количество тестов',
                    data: counts,
                    backgroundColor: '#4CAF50',
                    borderRadius: 5,
                    barPercentage: 0.6,
                    categoryPercentage: 0.5
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: { title: { display: true, text: 'Дата' } },
                    y: {
                        title: { display: true, text: 'Количество тестов' },
                        beginAtZero: true,
                        ticks: { stepSize: 1, precision: 0 }
                    }
                },
                plugins: {
                    legend: {
                        display: true,
                        position: 'top',
                        labels: { font: { size: 14 }, boxWidth: 20, padding: 15 }
                    }
                }
            }
        });
    } else if (chartType === 'pie') {
        chartInstance = new Chart(ctx, {
            type: 'pie',
            data: {
                labels: filteredLabels,
                datasets: [{
                    label: 'Количество тестов',
                    data: filteredData,
                    backgroundColor: backgroundColors
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: true,
                        position: 'top',
                        labels: { font: { size: 14 }, boxWidth: 20, padding: 15 }
                    }
                }
            }
        });
    }
}

function renderTestCountTable(data) {
    const groupedData = processTestCountData(data);
    const dates = Object.keys(groupedData).sort();

    const tableHTML = `
        <table class="analytics-table">
            <thead><tr><th>Дата</th><th>Количество тестов</th></tr></thead>
            <tbody>
                ${dates.map(date => `<tr><td>${date}</td><td>${groupedData[date]}</td></tr>`).join('')}
                <tr class="total-row"><td>Итого</td><td>${dates.reduce((sum, d) => sum + groupedData[d], 0)}</td></tr>
            </tbody>
        </table>
    `;

    canvasContainer.innerHTML = tableHTML;
}

// Пример инициализации (можно вызывать при загрузке кнопки или страницы)
document.getElementById("btn-test-count").addEventListener("click", async () => {
    const data = await fetchTestCountData();
    renderTestCountChart(data, 'bar');
});
