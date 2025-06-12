# ChatBI

一个基于 **Tailwind CSS** + **ECharts** + **LLM 驱动**的交互式数据可视化演示。用户在右侧聊天窗口输入自然语言查询，前端通过 AI 生成 SQL、调用后端接口拉取数据，并实时在左侧渲染表格和图表。支持多种图表类型、主题切换，以及一键展开深度解析。

![image](https://github.com/user-attachments/assets/269236b7-8b59-492c-9194-1ff33429b71a)

## 主要功能

- **智能对话**：通过聊天框输入业务提问（如“各职称专家数量”），自动生成 SQL 并执行查询。
- **多样图表**：柱状图、折线图、饼图、散点图、折柱混合图，满足常见可视化需求。
- **主题切换**：ECharts 内置主题（default、vintage、macarons、dark）一键切换。
- **布局自适应**：左右两栏布局，左侧固定展示技术细节（SQL、Raw Data、图表），右侧聊天框独立滚动。
- **深度解析**：点击“展开解析”后，异步并行调用第二个 LLM 节点，获得文字分析（开发中）。


## 快速开始

1. **安装依赖**

   ```
   npm install            # 前端 Tailwind 和工具链
   pip install -r requirements.txt  # Python: Flask, OpenAI SDK 等
   ```

2. **编译 CSS**

   ```
   npm run build          # 生成 dist/style.css
   ```

3. **启动后端**

   ```
   python run.py
   ```

4. **启动静态服务器**

   ```
   npx serve .            # 或 python -m http.server 8080
   ```

5. **访问 Demo** 打开浏览器访问 `http://localhost:5000`（或静态服务器端口），即可开始互动！

## 使用说明

1. 在右侧聊天输入框输入自然语言问题，按 Enter 或点击“发送”。
2. 等待片刻，左侧将自动展示：
   - 生成的 SQL 语句
   - 原始数据表格
   - 根据默认或选定主题的图表
3. 可通过“图表类型”下拉切换可视化类型；通过“主题”下拉更换样式。
4. 点击“展开解析”按钮，会异步调 `/api/analysis`，展示对当前查询结果的文字解读（开发中）。

## 开发与定制

- **增加图表类型**：编辑 `js/main.js` 中 `renderChart` 方法，添加 ECharts Option 即可。
- **扩展主题**：在 `index.html` 引入更多 ECharts 主题脚本，并在主题下拉中添加对应 `value`。
- **后端接入**：在 `query_service.py` 中添加新的路由或并行 LLM 节点调用逻辑。


## 许可证

Apache 2.0 © 2025 Caho1
