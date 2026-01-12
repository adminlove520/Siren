# Changelog

All notable changes to this project will be documented in this file.

## [1.0.14] - 2026-01-12
### Fixed
- 修复 MissAV 时长解析逻辑，支持秒转分钟。
- 修复 Jable 时长解析，从列表页卡片提取。
- 修复 HohoJ 时长解析，增加多级回退匹配。
- 修复 Memo (memojav.com) 时长解析，支持 ISO 8601 格式转换。
- 修复各爬虫 `Tag.find()` 参数冲突导致的报错。
- 优化全站反爬绕过方案 (Safari 15.5 模拟)。

## [1.0.0] - 2026-01-12
### Added
- 从 Java 迁移至 Python 异步架构。
- 使用 SQLite 存储数据。
- 复刻所有原始 Discord 机器人指令。
- 增加 Docker 支持与 CI/CD 工作流。
