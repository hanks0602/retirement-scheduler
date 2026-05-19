階段一：專案環境與 Git 初始化 (Project Setup)
[x] Task 1: 建立基礎開發環境

在專案資料夾建立 requirements.txt（寫入 streamlit, pandas, plotly）。

在 VS Code 終端機執行 pip install -r requirements.txt 確保套件安裝成功。

[x] Task 2: 建立基礎檔案與 Git 追蹤

將你現有的 CSV 檔案放入專案根目錄。

建立主程式 app.py 與 .gitignore（排除 __pycache__/ 與 venv/ 等雜物）。

完成 Git 的首次 commit 並確保與 GitHub 遠端倉庫連線。

階段二：核心計算引擎開發 (Core Logic Engine)
[x] Task 3: 讀取與清理 CSV 基準資料

用 Pandas 讀取 CSV，清理或重新映射包含中文字元與括號的欄位名稱（如：將 期初投資資產(6%) 改為乾淨的 Key 方便後續程式計算）。

[x] Task 4: 撰寫動態模擬邏輯（Simulation Loop）

設計一個 Python 函式（計算引擎），輸入引數包含：初始年薪、通膨率、投資回報率、調薪率、買房年份、買房總價、支出級距等。

使用 for 迴圈模擬 2027 到 2080 年的資產變化。

關鍵邏輯防呆：確保 2030 年買房時，會扣除 500 萬自備款與 75 萬車款；2040 年扣除 75 萬第二台車款；2041 年起薪資收入歸零，改由資產提領。

[x] Task 5: 核心指標計算測試

計算出「退休首年總支出」與「4% 安全提領金」。

比對手動輸入與預設 CSV 在完全不改參數時，2040 年底的期末資產是否能對齊 3,234 萬元。

階段三：Streamlit 使用者介面設計 (UI/UX Layout)
[x] Task 6: 控制面板（Sidebar）元件配置

設計「資料模式切換」：切換【使用 CSV 基準資料】與【自訂手動模擬】。

建立各項參數的動態滑桿（Slider）與輸入框（Number Input）：

基本年薪、調薪率、投資回報率（預設 6%）。

通膨率（預設 2~3%）、支出情境切換（高中低按鈕或下拉選單）。

重大支出微調（買房年份、房貸利率、車款預算）。

[x] Task 7: 資訊看板（KPI Cards）呈現

在網頁最上方，用 st.columns 呈現三大核心數據：預估退休年齡（或是否能順利 2040 退休）、2040 終局總流動資產、財務自由健康度（安全/合理/危險）。

階段四：互動視覺化與資料表格 (Data Visualization)
[x] Task 8: 繪製資產累積曲線 (Plotly Line Chart)

用 Plotly 繪製 2027 - 2080 年的「期末投資資產」折線圖。

確保圖表能動態反應使用者的參數（例如：改到 2032 年買房，資產下跌的谷底點要隨之移動）。

[x] Task 9: 繪製收支交叉對比圖 (Plotly Bar Chart)

繪製歷年的長條圖，堆疊呈現「實質薪資 + 投資收益」，並與「總支出」對比，直觀展現 2040 年後黃金交叉的被動收入流。

[x] Task 10: 動態資料表格展示

在網頁底部使用 st.dataframe 秀出計算後的完整 Excel 報表，並將金額格式化為百萬元（或千元）以便閱讀。

階段五：測試與雲端部署 (Testing & Deployment)
[ ] Task 11: 一鍵部署至 Streamlit Cloud

在本地確認調整任何參數時，網頁圖表和 KPI 都會即時動態更新（無 Bug 閃退）。

將最終代碼 git push 到 GitHub。

登入 Streamlit Community Cloud，綁定 GitHub 倉庫，完成線上發布。