/* ================================
   CURRENCY FORMATTER
================================ */

function formatCurrency(amount) {
    return "₹" + Number(amount).toLocaleString("en-IN", {
        maximumFractionDigits: 2
    });
}

/* ================================
   SEARCH - TRANSACTIONS PAGE
================================ */

const searchInput = document.getElementById("searchInput");

if (searchInput) {

    searchInput.addEventListener("keyup", function () {

        const searchValue = searchInput.value.toLowerCase();
        const rows = document.querySelectorAll(".transaction-table tbody tr");

        rows.forEach(function (row) {

            const rowText = row.textContent.toLowerCase();

            if (rowText.includes(searchValue)) {
                row.style.display = "";
            } else {
                row.style.display = "none";
            }

        });

    });

}


/* ================================
   DASHBOARD - TOTAL SPENDING
================================ */

const totalSpending = document.getElementById("totalSpending");

if (totalSpending) {

    fetch("http://127.0.0.1:5000/api/transactions/monthly", {
        credentials: "include"
    })
        .then(response => response.json())
        .then(data => {

            let total = 0;

            data.monthly_spending.forEach(item => {
                total += item.total_spending;
            });

            totalSpending.textContent = formatCurrency(total);

        })
        .catch(error => {
            console.log("Error:", error);
        });

}


/* ================================
   DASHBOARD - TOTAL TRANSACTIONS
================================ */

const totalTransactions = document.getElementById("totalTransactions");

if (totalTransactions) {

    fetch("http://127.0.0.1:5000/api/transactions", {
        credentials: "include"
    })
        .then(response => response.json())
        .then(data => {

            totalTransactions.textContent = data.transactions.length;

        })
        .catch(error => {
            console.log("Error:", error);
        });

}


/* ================================
   DASHBOARD - HIGHEST EXPENSE
================================ */

const highestExpense = document.getElementById("highestExpense");

if (highestExpense) {

    fetch("http://127.0.0.1:5000/api/transactions", {
        credentials: "include"
    })
        .then(response => response.json())
        .then(data => {

            const transactions = data.transactions;

            let highest = 0;

            transactions.forEach(transaction => {

                if (transaction.amount > highest) {
                    highest = transaction.amount;
                }

            });

            highestExpense.textContent = formatCurrency(highest);

        })
        .catch(error => {
            console.log("Error:", error);
        });

}


/* ================================
   DASHBOARD - AVERAGE EXPENSE
================================ */

const averageExpense = document.getElementById("averageExpense");

if (averageExpense) {

    fetch("http://127.0.0.1:5000/api/transactions", {
        credentials: "include"
    })
        .then(response => response.json())
        .then(data => {

            const transactions = data.transactions;

            let total = 0;

            transactions.forEach(transaction => {
                total += transaction.amount;
            });

            const average = transactions.length ? total / transactions.length : 0;

            averageExpense.textContent = formatCurrency(average);

        })
        .catch(error => {
            console.log("Error:", error);
        });

}


/* ================================
   DASHBOARD - RECENT TRANSACTIONS
================================ */

const recentTransactions = document.getElementById("recentTransactions");

if (recentTransactions) {

    fetch("http://127.0.0.1:5000/api/transactions", {
        credentials: "include"
    })
        .then(response => response.json())
        .then(data => {

            const transactions = data.transactions;

            transactions.forEach(transaction => {

                const row = document.createElement("tr");

                [transaction.date, transaction.description, transaction.category, formatCurrency(transaction.amount)]
                    .forEach(value => {
                        const cell = document.createElement("td");
                        cell.textContent = value;
                        row.appendChild(cell);
                    });

                recentTransactions.appendChild(row);

            });

        })
        .catch(error => {
            console.log("Error:", error);
        });

}


/* ================================
   ADD TRANSACTION
================================ */

const transactionForm = document.getElementById("transactionForm");

if (transactionForm) {

    transactionForm.addEventListener("submit", function(event) {

        event.preventDefault();

        const date = document.getElementById("date").value;
        const description = document.getElementById("description").value;
        const category = document.getElementById("category").value;
        const amount = document.getElementById("amount").value;

        fetch("http://127.0.0.1:5000/api/transactions", {
            method: "POST",
            credentials: "include",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                date: date,
                description: description,
                category: category,
                amount: Number(amount)
            })
        })
        .then(response => response.json())
        .then(data => {

            console.log(data);

            window.location.href = "index.html";

        })
        .catch(error => {
            console.log("Error:", error);
        });

    });

}


/* ================================
   TRANSACTIONS PAGE
================================ */

const transactionsList = document.getElementById("transactionsList");

if (transactionsList) {

    fetch("http://127.0.0.1:5000/api/transactions", {
        credentials: "include"
    })
        .then(response => response.json())
        .then(data => {

            const transactions = data.transactions;

            transactions.forEach(transaction => {

                const row = document.createElement("tr");

                [transaction.date, transaction.description, transaction.category, formatCurrency(transaction.amount)]
                    .forEach(value => {
                        const cell = document.createElement("td");
                        cell.textContent = value;
                        row.appendChild(cell);
                    });

                transactionsList.appendChild(row);

            });

        })
        .catch(error => {
            console.log("Error:", error);
        });

}


/* ================================
   ANALYSIS PAGE - SUMMARY
================================ */

const analysisTotal = document.getElementById("analysisTotal");
const analysisHighest = document.getElementById("analysisHighest");
const analysisAverage = document.getElementById("analysisAverage");

if (analysisTotal || analysisHighest || analysisAverage) {

    fetch("http://127.0.0.1:5000/api/transactions", {
        credentials: "include"
    })
        .then(response => response.json())
        .then(data => {

            const transactions = data.transactions;

            let total = 0;
            let highest = 0;

            transactions.forEach(transaction => {

                total += transaction.amount;

                if (transaction.amount > highest) {
                    highest = transaction.amount;
                }

            });

            const average = transactions.length ? total / transactions.length : 0;

            if (analysisTotal) analysisTotal.textContent = formatCurrency(total);
            if (analysisHighest) analysisHighest.textContent = formatCurrency(highest);
            if (analysisAverage) analysisAverage.textContent = formatCurrency(average);

        })
        .catch(error => {
            console.log("Error:", error);
        });

}


/* ================================
   ANALYSIS PAGE - CATEGORY SPENDING
================================ */

const categoryAnalysis = document.getElementById("categoryAnalysis");

if (categoryAnalysis) {

    fetch("http://127.0.0.1:5000/api/transactions", {
        credentials: "include"
    })
        .then(response => response.json())
        .then(data => {

            const transactions = data.transactions;

            const categories = {};

            transactions.forEach(transaction => {

                const category = transaction.category;

                if (!categories[category]) {
                    categories[category] = 0;
                }

                categories[category] += transaction.amount;

            });

            for (const category in categories) {

                const item = document.createElement("div");

                item.className = "card";

                const heading = document.createElement("h3");
                heading.textContent = category;
                const amount = document.createElement("p");
                amount.textContent = formatCurrency(categories[category]);
                item.append(heading, amount);

                categoryAnalysis.appendChild(item);

            }

        })
        .catch(error => {
            console.log("Error:", error);
        });

}


/* ================================
   ANALYSIS PAGE - SPENDING CHART
================================ */

const spendingChart = document.getElementById("spendingChart");

if (spendingChart) {

    fetch("http://127.0.0.1:5000/api/transactions", {
        credentials: "include"
    })
        .then(response => response.json())
        .then(data => {

            const transactions = data.transactions;

            const categories = {};

            transactions.forEach(transaction => {

                const category = transaction.category;

                if (!categories[category]) {
                    categories[category] = 0;
                }

                categories[category] += transaction.amount;

            });

            new Chart(spendingChart, {

                type: "bar",

                data: {

                    labels: Object.keys(categories),

                    datasets: [{
                        label: "Spending",
                        data: Object.values(categories)
                    }]

                }

            });

        })
        .catch(error => {
            console.log("Error:", error);
        });

}


/* ================================
   REPORTS PAGE
================================ */

const reportTotal = document.getElementById("reportTotal");
const reportTransactions = document.getElementById("reportTransactions");
const reportHighest = document.getElementById("reportHighest");
const reportAverage = document.getElementById("reportAverage");
const reportTransactionsList = document.getElementById("reportTransactionsList");

if (reportTotal || reportTransactionsList) {

    fetch("http://127.0.0.1:5000/api/transactions", {
        credentials: "include"
    })
        .then(response => response.json())
        .then(data => {

            const transactions = data.transactions;

            let total = 0;
            let highest = 0;

            transactions.forEach(transaction => {

                total += transaction.amount;

                if (transaction.amount > highest) {
                    highest = transaction.amount;
                }

                if (reportTransactionsList) {

                    const row = document.createElement("tr");

                    [transaction.date, transaction.description, transaction.category, formatCurrency(transaction.amount)]
                        .forEach(value => {
                            const cell = document.createElement("td");
                            cell.textContent = value;
                            row.appendChild(cell);
                        });

                    reportTransactionsList.appendChild(row);

                }

            });

            const average = total / transactions.length;

            if (reportTotal) reportTotal.textContent = formatCurrency(total);
            if (reportTransactions) reportTransactions.textContent = transactions.length;
            if (reportHighest) reportHighest.textContent = formatCurrency(highest);
            if (reportAverage) reportAverage.textContent = formatCurrency(average);

        })
        .catch(error => {
            console.log("Error:", error);
        });

}


/* ================================
   REPORTS PAGE - EXPORT CSV
================================ */

const exportReport = document.getElementById("exportReport");

if (exportReport) {

    exportReport.addEventListener("click", function () {

        fetch("http://127.0.0.1:5000/api/transactions", {
            credentials: "include"
        })
            .then(response => response.json())
            .then(data => {

                const transactions = data.transactions;

                let csv = "Date,Description,Category,Amount\n";

                transactions.forEach(transaction => {

                    csv += `"${transaction.date}","${transaction.description}","${transaction.category}","${formatCurrency(transaction.amount)}"\n`;

                });

                const blob = new Blob([csv], {
                    type: "text/csv"
                });

                const url = URL.createObjectURL(blob);

                const link = document.createElement("a");

                link.href = url;
                link.download = "finquery_report.csv";

                link.click();

                URL.revokeObjectURL(url);

            })
            .catch(error => {
                console.log("Error:", error);
            });

    });

}


/* ================================
   REGISTER
================================ */

const registerForm = document.getElementById("registerForm");

if (registerForm) {

    registerForm.addEventListener("submit", async function(event) {

        event.preventDefault();

        const message = document.getElementById("registerMessage");
        const submitButton = registerForm.querySelector('button[type="submit"]');
        const name = document.getElementById("name").value;
        const email = document.getElementById("email").value;
        const password = document.getElementById("password").value;

        submitButton.disabled = true;
        message.textContent = "Creating your account...";
        message.classList.remove("error");

        try {
            const response = await fetch("http://127.0.0.1:5000/api/register", {
                method: "POST",
                credentials: "include",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ name, email, password })
            });
            const result = await response.json().catch(() => ({}));
            if (!response.ok) throw new Error(result.message || `Server error (${response.status}).`);

            message.textContent = "Account created. Opening login...";
            window.location.href = "login.html";
        } catch (error) {
            message.textContent = error instanceof TypeError
                ? "Cannot reach the API. Keep the backend running and open this page at http://127.0.0.1:5500."
                : error.message || "Account could not be created.";
            message.classList.add("error");
        } finally {
            submitButton.disabled = false;
        }

    });

}


/* ================================
   LOGIN
================================ */

const loginForm = document.getElementById("loginForm");

if (loginForm) {

    loginForm.addEventListener("submit", async function(event) {

        event.preventDefault();

        const message = document.getElementById("loginMessage");
        const submitButton = loginForm.querySelector('button[type="submit"]');
        const email = document.getElementById("email").value;
        const password = document.getElementById("password").value;

        submitButton.disabled = true;
        message.textContent = "Signing in...";
        message.classList.remove("error");

        try {
            const response = await fetch("http://127.0.0.1:5000/api/login", {
                method: "POST",
                credentials: "include",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email, password })
            });
            const result = await response.json().catch(() => ({}));
            if (!response.ok || !result.success) {
                throw new Error(result.message || "Email or password is incorrect.");
            }

            message.textContent = "Login successful. Opening your dashboard...";
            window.location.href = "index.html";
        } catch (error) {
            message.textContent = error instanceof TypeError
                ? "Cannot reach the API. Keep the backend running and open this page at http://127.0.0.1:5500."
                : error.message || "Login failed.";
            message.classList.add("error");
        } finally {
            submitButton.disabled = false;
        }

    });

}


/* ================================
   PAGE PROTECTION
================================ */

const currentPage = window.location.pathname;

if (
    currentPage.includes("index.html") ||
    currentPage.includes("analysis.html") ||
    currentPage.includes("transactions.html") ||
    currentPage.includes("add-transaction.html") ||
    currentPage.includes("reports.html") ||
    currentPage.includes("import.html")
) {

    fetch("http://127.0.0.1:5000/api/me", {
        credentials: "include"
    })
        .then(response => {

            if (!response.ok) {

                window.location.href = "login.html";

            }

            return response.json();

        })
        .then(result => {

            if (!result.logged_in) {

                window.location.href = "login.html";

            }

        })
        .catch(error => {

            console.log("Session check error:", error);

            window.location.href = "login.html";

        });

}


/* ================================
   MONTHLY BUDGET AND INSIGHT
================================ */

const budgetSpentAmount = document.getElementById("budgetSpentAmount");
const budgetTargetAmount = document.getElementById("budgetTargetAmount");
const budgetProgress = document.getElementById("budgetProgress");
const monthlyBudgetLabel = document.getElementById("monthlyBudgetLabel");
const monthlyInsight = document.getElementById("monthlyInsight");

window.refreshSidebarSummary = () => {
    if (!budgetSpentAmount) return;
    fetch("http://127.0.0.1:5000/api/sidebar-summary", {
        credentials: "include"
    })
        .then(async response => {
            const result = await response.json();
            if (!response.ok) throw new Error(result.message || "Could not load budget summary");
            return result;
        })
        .then(summary => {
            budgetSpentAmount.textContent = formatCurrency(summary.spent);
            budgetTargetAmount.textContent = formatCurrency(summary.budget);
            budgetProgress.style.width = `${summary.progress_percent}%`;
            budgetProgress.style.backgroundColor = summary.percent_used >= 100
                ? "#ef9a9a"
                : summary.percent_used >= 80 ? "#edb95e" : "#78c69c";
            monthlyBudgetLabel.textContent = `${Number(summary.percent_used).toLocaleString("en-IN", { maximumFractionDigits: 1 })}% used in ${summary.period_label}`;
            monthlyInsight.textContent = summary.insight;
        })
        .catch(error => {
            console.error("Could not load monthly budget:", error);
            monthlyInsight.textContent = "Could not load this month's budget summary.";
        });
};

window.refreshSidebarSummary();


/* ================================
   FINANCE QUESTION AND CHART API
================================ */

const financeQuestionForm = document.getElementById("financeQuestionForm");
const financeQuestionInput = document.getElementById("financeQuestion");
const financeAnswer = document.getElementById("financeAnswer");
const financeQuestionButton = document.getElementById("financeQuestionButton");
const financeChartContainer = document.getElementById("financeChartContainer");
const financeAnswerCanvas = document.getElementById("financeAnswerChart");
let financeAnswerChart = null;

if (financeQuestionForm) {
    financeQuestionForm.addEventListener("submit", async event => {
        event.preventDefault();
        financeQuestionButton.disabled = true;
        financeAnswer.textContent = "Analyzing your transactions...";

        try {
            const response = await fetch("http://127.0.0.1:5000/api/assistant/query", {
                method: "POST",
                credentials: "include",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ question: financeQuestionInput.value.trim() })
            });
            const result = await response.json();
            if (!response.ok) {
                throw new Error(result.message || "Could not analyze that question.");
            }

            financeAnswer.textContent = result.answer;
            if (financeAnswerChart) {
                financeAnswerChart.destroy();
                financeAnswerChart = null;
            }

            if (result.chart && result.chart.labels.length) {
                financeChartContainer.hidden = false;
                const colors = ["#2e7d5b", "#73a88d", "#edb95e", "#6f8fc7", "#d77a61", "#a58ac3", "#65aeb0"];
                const isPie = result.chart.type === "pie";
                financeAnswerChart = new Chart(financeAnswerCanvas, {
                    type: result.chart.type,
                    data: {
                        labels: result.chart.labels,
                        datasets: [{
                            label: result.chart.label,
                            data: result.chart.values,
                            backgroundColor: isPie ? colors : "rgba(46, 125, 91, 0.72)",
                            borderColor: isPie ? "#ffffff" : "#2e7d5b",
                            borderWidth: isPie ? 2 : 1,
                            fill: false,
                            tension: 0.25
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: { display: isPie, position: "bottom" },
                            tooltip: {
                                callbacks: {
                                    label: context => `${context.dataset.label}: ₹${Number(context.raw).toLocaleString("en-IN")}`
                                }
                            }
                        },
                        scales: isPie ? {} : {
                            y: {
                                beginAtZero: true,
                                ticks: { callback: value => `₹${Number(value).toLocaleString("en-IN")}` }
                            }
                        }
                    }
                });
            } else {
                financeChartContainer.hidden = true;
            }
        } catch (error) {
            financeAnswer.textContent = error.message || "Could not connect to the backend.";
            financeChartContainer.hidden = true;
        } finally {
            financeQuestionButton.disabled = false;
        }
    });
}

