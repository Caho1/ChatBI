/**
 * ChatBI 前端交互脚本
 * -----------------------------------------------------
 * 依赖：TailwindCSS、highlight.js、sql-formatter、ECharts
 */

/* ---------- highlight.js 初始化 ---------- */
if (window.hljs) {
    hljs.configure({ languages: ["sql", "json"] });
    hljs.highlightAll();
}

document.addEventListener("DOMContentLoaded", () => {
    /* ---------- DOM 缓存 ---------- */
    const $ = (sel) => document.querySelector(sel);
    const chatForm  = $("#chat-form");
    const chatInput = $("#chat-input");
    const chatWin   = $("#chat-window");
    const sqlCodeEl = $("#sql-code");
    const rawBox    = $("#raw-data-box");
    const chartBox  = $("#chart-box");
    const drawBtn   = $("#draw-btn");
    const chartTypeSel = $("#chart-type");
    const sendBtn   = chatForm.querySelector("button[type='submit']");
    const themeSel = $("#theme-select");

    /* ---------- 状态 ---------- */
    let latestData = null;            // 最新 raw_data，供制图

    /* ---------- 配置 ---------- */
    const API_URL = "http://127.0.0.1:5000/api/query";

    /* ---------- 发送提问 ---------- */
    chatForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const q = chatInput.value.trim();
        if (!q) return;

        chatInput.value = "";
        chatInput.disabled = true;
        sendBtn.disabled = true;
        addMsg(q, "user");
        const thinking = addMsg("正在思考中…", "ai", true);

        try {
            const res = await fetch(API_URL, {
                method : "POST",
                headers: { "Content-Type": "application/json" },
                body   : JSON.stringify({ question: q }),
            });
            thinking.remove();

            const data = await res.json();
            if (!res.ok) throw new Error(data.error || "请求失败");

            updateTechDetails(data.sql_query, data.raw_data);
            addMsg(data.summary, "ai");
        } catch (err) {
            thinking.remove();
            addMsg(`❌ ${err.message}`, "ai-error");
        } finally {
            chatInput.disabled = false;
            sendBtn.disabled = false;
            chatInput.focus();
        }
    });

    // drawBtn 点击事件，传入 theme
    drawBtn.addEventListener("click", () => {
        if (!latestData?.length) {
            alert("暂无数据，请先提问获得数据后再绘制！");
            return;
        }
        renderChart(chartTypeSel.value, themeSel.value, latestData);
    });
    /* ---------- 技术面板渲染 ---------- */
    function updateTechDetails(sql, data) {
        latestData = data;                 // 保存供绘图

        // ---- SQL ----
        const formattedSql = window.sqlFormatter
            ? sqlFormatter.format(sql || "-- 未能生成 SQL --", { language: "mysql" })
            : (sql || "-- 未能生成 SQL --");
        sqlCodeEl.textContent = formattedSql;
        if (window.hljs) hljs.highlightElement(sqlCodeEl);

        // ---- Raw Data ----
        rawBox.innerHTML = renderRawData(data);

        if (latestData && latestData.length) {
            const type  = chartTypeSel.value;    // 图表类型下拉
            const theme = themeSel ? themeSel.value : undefined;  // 如果有主题下拉
            renderChart("bar", undefined, latestData);
        }
    }

    /* ---------- Raw Data → 表格/JSON ---------- */
    function renderRawData(data) {
        // 二维数组 -> 表格
        if (Array.isArray(data) && data.length && Array.isArray(data[0])) {
            const rows = data
                .map((r) => `<tr><td class="px-2 py-1 border">${r[0]}</td>
                         <td class="px-2 py-1 border text-right">${r[1]}</td></tr>`)
                .join("");
            return `<table class="table-auto border-collapse text-sm">
                <thead><tr><th class="px-2 py-1 border">类别</th>
                           <th class="px-2 py-1 border">数值</th></tr></thead>
                <tbody>${rows}</tbody>
              </table>`;
        }

        // 其他 → JSON
        const txt = typeof data === "string"
            ? data
            : JSON.stringify(data, null, 2);
        const code = `<pre class="whitespace-pre-wrap"><code>${txt}</code></pre>`;
        // 增加高亮
        setTimeout(() => {
            const c = rawBox.querySelector("code");
            if (c && window.hljs) hljs.highlightElement(c);
        }, 0);
        return code;
    }

    /* ---------- 渲染 ECharts ---------- */
    function renderChart(type, theme, data) {
        if (!window.echarts) return;

        const labels = data.map((r) => String(r[0]));
        const values = data.map((r) => r[1]);

        let option;

        if (type === "pie") {
            option = {
                tooltip: { trigger: "item" },
                legend : { orient: "vertical", left: "left" },
                series : [{
                    type : "pie",
                    radius: "60%",
                    data  : labels.map((l, i) => ({ name: l, value: values[i] })),
                    label : { formatter: "{b}: {c}" },
                }],
            };

        } else if (type === "scatter") {
            option = {
                tooltip: { trigger: "item" },
                xAxis: { type: "category", data: labels },
                yAxis: { type: "value" },
                series: [{
                    type: "scatter",
                    data: values.map((v, i) => [labels[i], v]),
                    symbolSize: 10,
                }],
            };
        } else if (type === "barline") {
            option = {
                tooltip: { trigger: "axis" },
                xAxis: { type: "category", data: labels },
                yAxis: [
                    { type: "value", name: "柱" },
                    { type: "value", name: "线", position: "right" },
                ],
                legend: { data: ["柱", "线"] },
                series: [
                    { name: "柱", type: "bar", data: values },
                    { name: "线", type: "line", yAxisIndex: 1, data: values },
                ],
            };
        }
        else {
            option = {
                tooltip: { trigger: "axis" },
                xAxis  : { type: "category", data: labels },
                yAxis  : { type: "value" },
                series : [{
                    name : "数值",
                    type : type,
                    data : values,
                    label: { show: true, position: "top" },
                }],
            };
        }

        chartBox.classList.remove("hidden");
        let chart = echarts.getInstanceByDom(chartBox);
        if (chart) chart.dispose();

        chart = echarts.init(chartBox, theme || undefined);
        chart.setOption(option);
        window.addEventListener("resize", () => chart.resize());
    }

    /* ---------- 聊天气泡 ---------- */
    function addMsg(text, role = "ai", thinking = false) {
        const wrap = document.createElement("div");
        const bubble = document.createElement("div");
        wrap.classList.add("flex");
        bubble.classList.add("rounded-lg", "px-4", "py-2", "max-w-md",
            "whitespace-pre-wrap");

        if (role === "user") {
            wrap.classList.add("justify-end");
            bubble.classList.add("bg-gray-600", "text-white");
        } else if (role === "ai-error") {
            wrap.classList.add("justify-start");
            bubble.classList.add("bg-red-500", "text-white");
        } else {
            wrap.classList.add("justify-start");
            bubble.classList.add("bg-gray-200", "text-black");
        }

        if (thinking) {
            bubble.innerHTML = `
        <div class="flex items-center space-x-1">
          <span>${text}</span>
          ${["0", ".2", ".4"].map(
                (d) => `<span class="w-2 h-2 bg-black rounded-full animate-pulse"
                         style="animation-delay:${d}s"></span>`
            ).join("")}
        </div>`;
        } else {
            bubble.textContent = text;
        }

        wrap.appendChild(bubble);
        chatWin.appendChild(wrap);
        chatWin.scrollTop = chatWin.scrollHeight;
        return wrap;
    }
});
