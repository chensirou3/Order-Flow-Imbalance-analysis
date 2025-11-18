#!/bin/bash
# 顺序运行所有品种的分批分析
# 等待BTC完成后，自动运行其他品种

cd /home/ubuntu/Order-Flow-Imbalance-analysis

echo "================================================================================"
echo "顺序分批分析 - 所有品种"
echo "开始时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo "================================================================================"
echo ""

# 检查BTC分析是否正在运行
echo "[1/6] 检查BTCUSD分析状态..."
if pgrep -f "run_btc_batch_analysis.py" > /dev/null; then
    echo "  ✓ BTCUSD分析正在运行，等待完成..."
    
    # 等待BTC分析完成
    while pgrep -f "run_btc_batch_analysis.py" > /dev/null; do
        completed=$(grep -c '保存到:' btc_batch_output.log 2>/dev/null || echo 0)
        echo "  进度: $completed / 40 任务已完成 ($(date '+%H:%M:%S'))"
        sleep 60  # 每分钟检查一次
    done
    
    echo "  ✓ BTCUSD分析已完成！"
else
    echo "  ⚠ BTCUSD分析未运行，将跳过等待"
fi

echo ""
echo "================================================================================"
echo "[2/6] 开始运行其他品种的分析..."
echo "================================================================================"
echo ""

# 运行所有品种的分析（包括BTC，但会跳过已完成的）
python3 -u scripts/run_all_symbols_batch_analysis.py 2>&1 | tee all_symbols_batch_output.log

echo ""
echo "================================================================================"
echo "✅ 所有品种分析完成！"
echo "完成时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo "================================================================================"
echo ""

# 显示结果摘要
echo "结果文件:"
ls -lh results/*_merged_bars_with_ofi.csv 2>/dev/null || echo "  未找到合并文件"
echo ""
ls -lh results/*_batch_summary.csv 2>/dev/null || echo "  未找到摘要文件"
echo ""

