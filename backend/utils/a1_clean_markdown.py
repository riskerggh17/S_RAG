# a1_clean_markdown.py
import os
import re
import json
import glob
from tqdm import tqdm

class MDCleaner:
    def __init__(self, source_dir: str, output_file: str, source: str, category: str = 'all'):
        self.source_dir = source_dir  # 原始数据地址
        self.output_file = output_file  # 输出文件地址
        self.source = source  # 数据来源标识
        self.category = category  # 分类标识
        # 1. 正则匹配图片: ![alt](src) -> 删除
        self.image_pattern = re.compile(r'!\[[^\]]*\]\([^\)]+\)')
        # 2. 正则匹配链接: [text](url) -> 保留 [text]
        self.link_pattern = re.compile(r'\[([^\]]+)\]\([^\)]+\)')
        # 3. 正则匹配 HTML 标签: <div> -> 删除
        self.html_pattern = re.compile(r'<[^>]+>')
        # 4. 正则匹配代码块: ```lang ... ``` -> 包裹保护
        # 使用非贪婪匹配，确保能正确处理多个代码块
        self.code_block_pattern = re.compile(r'```(\w*)\n([\s\S]*?)\n```')

    def process_content(self, content: str) -> str:
        """
        执行核心清洗逻辑
        """
        # --- 1. 清洗阶段 ---
        # 删除图片
        content = self.image_pattern.sub('', content)
        # 简化链接，只保留文本部分
        content = self.link_pattern.sub(r'[\1]', content)
        # 删除 HTML 标签
        content = self.html_pattern.sub('', content)
        # --- 2. 代码块保护阶段 ---
        
        def replace_code_block(match):
            lang = match.group(1) or "text" # 获取语言，默认为 text
            code = match.group(2).strip()
            # 使用与 get-started 相同的标记格式
            # 这样后续的切片器可以统一处理
            wrapper = (
                f"\n###CODE_BLOCK_START###|lang={lang}\n"
                f"{code}\n"
                f"###CODE_BLOCK_END###\n"
            )
            return wrapper
            
        content = self.code_block_pattern.sub(replace_code_block, content)
        # --- 3. 格式化收尾 ---
        # 将多个连续空行合并为两个换行符，保持文本整洁
        content = re.sub(r'\n{3,}', '\n\n', content)
        return content.strip()
    
    def clean(self):
        """
        遍历 guides 文件夹，处理所有 .md 文件
        """
        # 确保输出目录存在
        os.makedirs(os.path.dirname(self.output_file), exist_ok=True)
        cleaned_data = []
        success_count = 0
        failed_count = 0
        # 构建 glob 搜索路径
        search_pattern = os.path.join(self.source_dir, "**", "*.md").replace("\\", "/")
        print(f"🔍 正在扫描: {search_pattern}")
        file_list = glob.glob(search_pattern, recursive=True)
        if not file_list:
            print(f"⚠️ 警告：在 {self.source_dir} 中未找到任何 Markdown 文件。")
            return
        for file_path in tqdm(file_list, desc="🧹 正在清洗文件", total=len(file_list), unit="file"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    raw_content = f.read()
                # 执行清洗
                final_content = self.process_content(raw_content)
                # 构造元数据
                # 提取相对路径，例如: guides/deployment.md
                relative_path = os.path.relpath(file_path, os.path.dirname(self.source_dir))
                doc = {
                    "id": relative_path.replace("\\", "/"),
                    "source": self.source,           # 数据来源
                    "category": self.category,         # 分类标记：
                    "path": relative_path.replace("\\", "/"),
                    "content": final_content      # 处理后的文本
                }
                cleaned_data.append(doc)
                success_count += 1
                # print(f"✅ 已处理: {relative_path}")
                
            except Exception as e:
                failed_count += 1
                print(f"❌ 处理失败 {file_path}: {file_path}")
                print(f"   错误详情: {e}")
        
        if cleaned_data:
            # 写入 JSON 文件
            with open(self.output_file, 'w', encoding='utf-8') as f:
                json.dump(cleaned_data, f, indent=2, ensure_ascii=False)
            print(f"💾 数据已保存至: {self.output_file}")
        else:
            print("\n⚠️ 未生成任何有效数据，跳过保存。")

        print("-" * 30)
        print("📊 清洗任务统计报告")
        print("-" * 30)
        print(f"📂 扫描文件总数: {len(file_list)}")
        print(f"✅ 清洗成功: {success_count}")
        print(f"❌ 清洗失败: {failed_count}")
        print("-" * 30)
        if failed_count > 0:
            print("⚠️ 请检查上方错误日志以修复问题文件。")
        else:
            print("🎉 所有文件处理完成！")

# # --- 执行入口 ---
# if __name__ == "__main__":
#     source = "docker"
#     category = "reference"
#     # --- 路径配置 ---
#     # 自动计算路径
#     current_dir = os.path.dirname(os.path.abspath(__file__))
#     root_dir = os.path.dirname(current_dir)
#     # 注意：请根据你实际的文件夹结构调整这里的 'content' 层级
#     source_directory = os.path.join(root_dir, "raw_data", "docker", "content", category)
#     output_json = os.path.join(root_dir, "cleaned_data", f"docker_{category}.json")
#     print(f"🚀 源目录：{source_directory}")
#     print(f"🚀 输出文件：{output_json}")
#     # 运行清洗
#     print(f"🚀 开始清洗 {category} 文件夹...")
#     cleaner = MDCleaner(source_directory, output_json, source, category)
#     cleaner.clean()