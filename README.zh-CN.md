# CASI-Net：代码与数值验证开源仓库

这是论文 **《Observability-Aware Counterfactual Water-Surface Inference for Heterogeneous SAR–Optical Flood Change Detection》** 对应的**仅代码版**。

**公开内容：** 核心水面反演和物理推断参考算法、统计评价及校准工具、论文冻结参数、论文已报告的汇总结果对照表、数学单元测试、GitHub Actions、完整性哈希及 MIT 许可证文本。

**不公开内容：** 卫星影像、真实事件 ID 与空间边界、逐事件预测和标签、水位站点/HEC-RAS 原始记录、原始 conformal 校准分数、作者训练权重。也不包含完整神经网络训练流水线。`templates/` 中只有**空白字段表头**，`reference/` 中只有论文已发表/已报告的汇总结果，均不是原始实验观测。

## 安装及代码测试

```bash
python -m pip install -e . pytest
python -m pytest -q
python scripts/check_reported_arithmetic.py
python scripts/verify_repository_checksums.py
```

数值测试使用测试程序内构造的小型数组，不需要任何原始数据文件。**测试通过证明这些数学和程序检查点可运行，不代表重新训练了 CASI-Net，也不代表已经从原始数据独立复算出论文 F1 或 HEC-RAS 结果。**

## 仓库核心结构

- `casinet_repro/`：IRLS/ADMM 参考求解器、DEM 空间相关误差采样、conformal 校准、双时相源约束可达性、融合、bootstrap、指标计算及水动力参考评价。
- `configs/`：按正文和 Supplementary Material 整理的报告参数。
- `reference/`：主文表格及补充材料表格的**已报告汇总值**，供算术一致性检查使用。
- `templates/`：仅含列名的本地私有数据输入结构。
- `scripts/`：数据审查、评价与统计核验代码。真实数据必须由研究者在本地单独提供。
- `tests/`：不依赖影像、事件列表和模型权重的程序单元测试。
- `.github/workflows/ci.yml`：GitHub 自动测试。
- `SHA256SUMS.txt`：公开文件 SHA-256 校验清单。

本版定位为 **CASI-Net Code and Numerical Verification**，不是带权重的端到端模型复现包。发布前需由代码权利人确认 MIT 开源授权；不涉及第三方影像及数据授权。更多信息见 `docs/PUBLIC_CODE_RELEASE_CHECKLIST.md`。
