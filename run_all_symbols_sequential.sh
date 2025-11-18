#!/bin/bash
# 顺序运行所有品种的分批分析
# 等待BTCUSD完成后，依次运行其他品种

cd /home/ubuntu/Order-Flow-Imbalance-analysis

LOG_FILE="all_symbols_sequential.log"

echo "================================================================================" | tee -a $LOG_FILE
echo "所有品种顺序分批分析" | tee -a $LOG_FILE
echo "开始时间: $(date '+%Y-%m-%d %H:%M:%S')" | tee -a $LOG_FILE
echo "================================================================================" | tee -a $LOG_FILE
echo "" | tee -a $LOG_FILE

# 品种列表（BTCUSD已经在运行，所以从ETHUSD开始）
SYMBOLS=("ETHUSD" "EURUSD" "USDJPY" "XAGUSD" "XAUUSD")

# 等待BTCUSD完成
echo "[等待BTCUSD完成]" | tee -a $LOG_FILE
echo "检查BTCUSD分析状态..." | tee -a $LOG_FILE

if pgrep -f "run_btc_batch_analysis.py" > /dev/null; then
    echo "  BTCUSD分析正在运行，等待完成..." | tee -a $LOG_FILE
    
    # 等待BTC分析完成
    while pgrep -f "run_btc_batch_analysis.py" > /dev/null; do
        completed=$(grep -c '保存到:' btc_batch_output.log 2>/dev/null || echo 0)
        echo "  [$(date '+%H:%M:%S')] BTCUSD进度: $completed / 40 任务" | tee -a $LOG_FILE
        sleep 120  # 每2分钟检查一次
    done
    
    echo "  ✓ BTCUSD分析已完成！" | tee -a $LOG_FILE
else
    echo "  ⚠ BTCUSD分析未运行" | tee -a $LOG_FILE
fi

echo "" | tee -a $LOG_FILE

# 依次运行其他品种
for i in "${!SYMBOLS[@]}"; do
    SYMBOL="${SYMBOLS[$i]}"
    NUM=$((i + 2))  # BTCUSD是1，所以从2开始
    TOTAL=$((${#SYMBOLS[@]} + 1))
    
    echo "================================================================================" | tee -a $LOG_FILE
    echo "[$NUM/$TOTAL] 开始处理: $SYMBOL" | tee -a $LOG_FILE
    echo "时间: $(date '+%Y-%m-%d %H:%M:%S')" | tee -a $LOG_FILE
    echo "================================================================================" | tee -a $LOG_FILE
    echo "" | tee -a $LOG_FILE
    
    # 运行该品种的分析
    python3 -u scripts/run_single_symbol_batch.py $SYMBOL 2>&1 | tee ${SYMBOL}_batch_output.log
    
    echo "" | tee -a $LOG_FILE
    echo "✓ $SYMBOL 处理完成" | tee -a $LOG_FILE
    echo "" | tee -a $LOG_FILE
done

echo "================================================================================" | tee -a $LOG_FILE
echo "✅ 所有品种分析完成！" | tee -a $LOG_FILE
echo "完成时间: $(date '+%Y-%m-%d %H:%M:%S')" | tee -a $LOG_FILE
echo "================================================================================" | tee -a $LOG_FILE
echo "" | tee -a $LOG_FILE

# 显示结果摘要
echo "结果文件:" | tee -a $LOG_FILE
echo "" | tee -a $LOG_FILE
echo "合并文件:" | tee -a $LOG_FILE
ls -lh results/*_merged_bars_with_ofi.csv 2>/dev/null | tee -a $LOG_FILE
echo "" | tee -a $LOG_FILE
echo "摘要文件:" | tee -a $LOG_FILE
ls -lh results/*_batch_summary.csv 2>/dev/null | tee -a $LOG_FILE
echo "" | tee -a $LOG_FILE

