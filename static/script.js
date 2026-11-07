document.addEventListener("DOMContentLoaded", function () {

    /* =====================================================
       1. SMOOTH SCROLL TO RESULTS
    ===================================================== */

    function scrollToResults() {
        const params = new URLSearchParams(window.location.search);

        const hasSearch = params.has("q") &&
            params.get("q").trim().length > 0;

        const targetIds = [
            "analysis-results",
            "research-results",
            "plant-results",
            "results",
            "search-results"
        ];

        let target = null;

        // A submitted search should take the user directly
        // to the result section, not leave them at the page top.
        if (hasSearch) {
            for (const id of targetIds) {
                const element = document.getElementById(id);

                if (element) {
                    target = element;
                    break;
                }
            }
        }

        // POST-based pages such as Plant Intelligence and
        // Traditional Knowledge use their result containers.
        if (!target) {
            const analysis = document.getElementById("analysis-results");
            const documentResults = document.getElementById("results");

            if (analysis) {
                target = analysis;
            } else if (documentResults) {
                target = documentResults;
            }
        }

        if (!target) return;

        // Wait for the page layout to settle before scrolling.
        requestAnimationFrame(function () {
            setTimeout(function () {
                const navbar = document.querySelector(".navbar, .site-header");
                const navbarHeight = navbar
                    ? navbar.getBoundingClientRect().height
                    : 0;

                const targetPosition =
                    target.getBoundingClientRect().top +
                    window.scrollY -
                    navbarHeight -
                    22;

                window.scrollTo({
                    top: Math.max(0, targetPosition),
                    behavior: "smooth"
                });

                target.classList.add("search-highlight");

                setTimeout(function () {
                    target.classList.remove("search-highlight");
                }, 1900);

            }, 180);
        });
    }

    scrollToResults();


    /* =====================================================
       2. DOCUMENT UPLOAD VALIDATION
    ===================================================== */

    const fileInput = document.getElementById("document");
    const fileName = document.getElementById("fileName");
    const uploadForm = document.getElementById("uploadForm");
    const uploadButton = document.getElementById("uploadButton");

    if (fileInput && fileName) {

        fileInput.addEventListener("change", function () {

            const file = fileInput.files[0];

            if (!file) {
                fileName.textContent = "No file selected";
                return;
            }

            const extension = file.name
                .split(".")
                .pop()
                .toLowerCase();

            if (!["pdf", "txt"].includes(extension)) {
                fileInput.value = "";
                fileName.textContent =
                    "Please select a PDF or TXT file.";
                return;
            }

            const maxSize = 10 * 1024 * 1024;

            if (file.size > maxSize) {
                fileInput.value = "";
                fileName.textContent =
                    "File exceeds the 10 MB limit.";
                return;
            }

            const sizeInKB = (file.size / 1024).toFixed(1);

            fileName.textContent =
                `${file.name} · ${sizeInKB} KB`;
        });
    }

    if (uploadForm && uploadButton) {

        uploadForm.addEventListener("submit", function (event) {

            if (!fileInput || !fileInput.files.length) {
                event.preventDefault();

                if (fileName) {
                    fileName.textContent =
                        "Please select a PDF or TXT file first.";
                }

                return;
            }

            uploadButton.disabled = true;
            uploadButton.textContent = "Analyzing Document...";

        });
    }


    /* =====================================================
       3. ANALYTICS DASHBOARD
    ===================================================== */

    const dataElement = document.getElementById("analytics-data");

    if (!dataElement || !window.Plotly) {
        return;
    }

    let data;

    try {
        data = JSON.parse(dataElement.textContent);
    } catch (error) {
        console.error("Analytics data could not be read:", error);
        return;
    }

    const coverageChart = document.getElementById("coverageChart");
    const compoundChart = document.getElementById("compoundChart");

    const coverageLabels = Array.isArray(data.coverage_labels)
        ? data.coverage_labels
        : [];

    const coverageValues = Array.isArray(data.coverage_values)
        ? data.coverage_values
        : [];

    const compoundLabels = Array.isArray(data.compound_labels)
        ? data.compound_labels
        : [];

    const compoundValues = Array.isArray(data.compound_values)
        ? data.compound_values
        : [];

    const chartFont = {
        family: "DM Sans, Segoe UI, Arial, sans-serif",
        color: "#647568",
        size: 11
    };

    const commonConfig = {
        responsive: true,
        displayModeBar: false,
        displaylogo: false
    };

    const commonLayout = {
        autosize: true,
        paper_bgcolor: "rgba(0,0,0,0)",
        plot_bgcolor: "rgba(0,0,0,0)",
        font: chartFont,
        margin: {
            t: 18,
            r: 20,
            b: 45,
            l: 45
        },
        hoverlabel: {
            bgcolor: "#ffffff",
            bordercolor: "#e2e9e0",
            font: {
                family: "DM Sans, Arial, sans-serif",
                color: "#26382d"
            }
        }
    };


    /* =====================================================
       4. COVERAGE DONUT CHART
    ===================================================== */

    if (coverageChart) {

        const validCoverage = coverageLabels
            .map(function (label, index) {
                return {
                    label: String(label),
                    value: Number(coverageValues[index]) || 0
                };
            })
            .filter(function (item) {
                return item.value > 0;
            });

        if (validCoverage.length > 0) {

            const labels = validCoverage.map(item => item.label);
            const values = validCoverage.map(item => item.value);
            const total = values.reduce((sum, value) => sum + value, 0);

            Plotly.newPlot(
                coverageChart,
                [{
                    type: "pie",
                    labels: labels,
                    values: values,
                    hole: 0.68,
                    sort: true,
                    direction: "clockwise",
                    textinfo: "none",
                    hovertemplate:
                        "<b>%{label}</b><br>" +
                        "Records: %{value}<br>" +
                        "Share: %{percent}<extra></extra>",
                    marker: {
                        colors: [
                            "#315c46",
                            "#6e9278",
                            "#a5bea0",
                            "#c9d9c4",
                            "#8ba99a",
                            "#d9e6d4",
                            "#547b64",
                            "#b3c8b2"
                        ],
                        line: {
                            color: "#ffffff",
                            width: 3
                        }
                    }
                }],
                {
                    ...commonLayout,
                    showlegend: true,
                    legend: {
                        orientation: "h",
                        x: 0.5,
                        xanchor: "center",
                        y: -0.12,
                        font: {
                            size: 10,
                            color: "#647568"
                        }
                    },
                    annotations: [{
                        text:
                            `<b>${total}</b><br>` +
                            "<span style='font-size:10px;color:#78867b'>" +
                            "Plant records</span>",
                        showarrow: false,
                        x: 0.5,
                        y: 0.5,
                        font: {
                            size: 22,
                            color: "#315c46"
                        }
                    }]
                },
                commonConfig
            );

        } else {
            coverageChart.innerHTML =
                '<div class="empty-state">' +
                '<h3>No Coverage Data</h3>' +
                '<p>Coverage information is not available in the dataset.</p>' +
                '</div>';
        }
    }


    /* =====================================================
       5. COMPOUND RANKING CHART
    ===================================================== */

    if (compoundChart) {

        const compoundData = compoundLabels
            .map(function (label, index) {
                return {
                    label: String(label),
                    value: Number(compoundValues[index]) || 0
                };
            })
            .filter(function (item) {
                return item.value > 0;
            })
            .sort(function (a, b) {
                return a.value - b.value;
            })
            .slice(-10);

        if (compoundData.length > 0) {

            Plotly.newPlot(
                compoundChart,
                [{
                    type: "bar",
                    orientation: "h",
                    x: compoundData.map(item => item.value),
                    y: compoundData.map(item => item.label),
                    text: compoundData.map(item => item.value),
                    textposition: "outside",
                    cliponaxis: false,
                    hovertemplate:
                        "<b>%{y}</b><br>" +
                        "Records: %{x}<extra></extra>",
                    marker: {
                        color: compoundData.map(function (_, index) {
                            return index === compoundData.length - 1
                                ? "#315c46"
                                : "#9bb79d";
                        }),
                        line: {
                            width: 0
                        },
                        cornerradius: 7
                    }
                }],
                {
                    ...commonLayout,
                    margin: {
                        t: 15,
                        r: 35,
                        b: 40,
                        l: 130
                    },
                    bargap: 0.38,
                    showlegend: false,
                    xaxis: {
                        title: {
                            text: "Number of records",
                            font: {
                                size: 10,
                                color: "#78867b"
                            }
                        },
                        rangemode: "tozero",
                        showgrid: true,
                        gridcolor: "#edf1eb",
                        zeroline: false,
                        tickfont: {
                            size: 10,
                            color: "#78867b"
                        }
                    },
                    yaxis: {
                        automargin: true,
                        showgrid: false,
                        tickfont: {
                            size: 10,
                            color: "#536458"
                        }
                    }
                },
                commonConfig
            );

        } else {
            compoundChart.innerHTML =
                '<div class="empty-state">' +
                '<h3>No Compound Data</h3>' +
                '<p>Compound records are not available in the dataset.</p>' +
                '</div>';
        }
    }


    /* =====================================================
       6. RESPONSIVE CHART RESIZE
    ===================================================== */

    window.addEventListener("resize", function () {

        [coverageChart, compoundChart].forEach(function (chart) {

            if (
                chart &&
                chart.data &&
                window.Plotly
            ) {
                Plotly.Plots.resize(chart);
            }

        });

    });

});