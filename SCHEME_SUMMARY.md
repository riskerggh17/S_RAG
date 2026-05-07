# Docker文档数据清洗完整方案总结

## 🎯 核心策略：差异化处理四类文档

```
原始Docker文档 (raw_data/docker/content/)
│
├── 📘 get-started/     → 入门教程
│   ├── 特点: 概念介绍、快速上手
│   ├── 分块: 800 chars (小块)
│   └── 用途: 新手问答、概念解释
│
├── 📗 guides/          → 实践指南 (101个子目录)
│   ├── 特点: 代码示例、步骤详解
│   ├── 分块: 1200 chars (中块)
│   └── 用途: 实操问题、最佳实践
│
├── 📙 manuals/         → 产品手册 (26个子目录)
│   ├── 特点: 配置参数、运维指导
│   ├── 分块: 1000 chars (标准块)
│   └── 用途: 配置查询、故障排查
│
└── 📕 reference/       → API参考 (6个子目录)
    ├── 特点: 技术规格、命令定义
    ├── 分块: 600 chars (小块)
    └── 用途: 精确查询、参数确认
```

## 🔄 数据处理流程

```
Step 1: 读取Markdown文件
    ↓
Step 2: 提取YAML Front Matter (title, description, keywords)
    ↓
Step 3: 清理Markdown格式
    - 移除图片引用、外部链接
    - 保留代码块、标题层级
    ↓
Step 4: 按章节分割 (## 二级标题)
    ↓
Step 5: 智能分块 (根据doc_type调整大小)
    ↓
Step 6: 生成增强元数据
    ↓
Step 7: 输出JSON格式
```

## 📦 输出数据结构

```json
{
  "page_content": "Docker enables you to separate your applications...",
  "metadata": {
    "doc_type": "get-started",
    "source_file": "get-started/docker-overview.md",
    "title": "What is Docker?",
    "description": "Get an in-depth overview...",
    "keywords": "docker, container, platform",
    "section": "The Docker platform"
  }
}
```

## 🛠️ 使用工具

### 1. 数据清洗脚本
```bash
python data_cleaner.py
```
**输出**: `processed_data/docker_docs.json`

### 2. RAG集成示例
```bash
python rag_integration.py
```
**功能**: 
- 构建向量数据库
- 执行语义检索
- 混合搜索策略

## 💡 关键设计决策

### 为什么不同文档类型用不同分块大小？

| 文档类型 | 分块大小 | 原因 |
|---------|---------|------|
| get-started | 800 | 概念简单，小块便于理解 |
| guides | 1200 | 需要保留完整步骤和代码 |
| manuals | 1000 | 平衡上下文和精确度 |
| reference | 600 | 参数定义需精确匹配 |

### 元数据过滤的优势

```python
# 用户只想了解实操指南
retriever = vectorstore.as_retriever(
    search_kwargs={
        "filter": {"doc_type": "guides"}
    }
)

# 用户查询API参数
retriever = vectorstore.as_retriever(
    search_kwargs={
        "filter": {"doc_type": "reference"}
    }
)
```

## 🚀 快速开始

### Step 1: 安装依赖
```bash
pip install pyyaml langchain-community langchain-chroma langchain-ollama
```

### Step 2: 运行数据清洗
```bash
python data_cleaner.py
```

### Step 3: 验证结果
```bash
# 查看统计信息
cat processed_data/statistics.json

# 检查数据质量
python -c "import json; print(json.load(open('processed_data/docker_docs.json'))[0])"
```

### Step 4: 启动RAG服务
```bash
python rag_integration.py
```

## 📊 预期成果

```
输入: ~380个Markdown文件
  ↓
输出: ~2350个高质量文档分块
  ↓
应用: Docker运维RAG助手
  - 概念问答 (get-started)
  - 实操指导 (guides)
  - 配置查询 (manuals)
  - API参考 (reference)
```

## 🔧 高级优化方向

### 1. 代码块特殊处理
```python
# 提取代码示例作为独立chunk
code_blocks = extract_code_sections(content)
for code in code_blocks:
    create_chunk(
        content=code,
        metadata={"type": "code_example", "language": "bash"}
    )
```

### 2. 跨文档关联
```python
# 在metadata中添加related_docs
metadata['related_docs'] = find_related_documents(title, keywords)
```

### 3. 问答对生成
```python
# 基于章节标题生成Q&A
for section in sections:
    qa_pair = {
        "question": f"如何{section['title']}?",
        "answer": section['content']
    }
```

### 4. 多路召回
```python
# 同时从多个类型检索
results = {
    "concept": search("get-started", query),
    "practice": search("guides", query),
    "config": search("manuals", query),
    "api": search("reference", query)
}
# LLM综合回答
```

## ⚠️ 注意事项

1. **编码统一**: 所有文件使用UTF-8编码
2. **增量更新**: 修改脚本支持只处理新增文件
3. **质量抽检**: 定期检查chunk质量和完整性
4. **版本管理**: 为不同Docker版本文档打标签

## 📈 效果评估指标

- ✅ Chunk数量合理性（不过大也不过小）
- ✅ 元数据完整性（title, doc_type必填）
- ✅ 代码块保留率（guides类型>90%）
- ✅ 检索准确率（人工抽样评估）

## 🎓 学习资源

- [LangChain文档加载器](https://python.langchain.com/docs/modules/data_connection/document_loaders/)
- [Chroma向量数据库](https://docs.trychroma.com/)
- [Ollama Embeddings](https://ollama.com/library/nomic-embed-text)

---

**下一步行动**:
1. ✅ 运行 `python data_cleaner.py` 清洗数据
2. ✅ 检查 `processed_data/statistics.json` 验证结果
3. ✅ 运行 `python rag_integration.py` 测试RAG系统
4. 🔜 根据实际需求调整分块策略和元数据
