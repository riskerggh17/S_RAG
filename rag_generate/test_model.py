from huggingface_hub import snapshot_download

# 自动下载整个模型仓库到本地目录
local_dir = r"E:\py_obj\S_RAG\models\bge-m3"
snapshot_download(
    repo_id="BAAI/bge-m3",
    local_dir=local_dir,
    # 如果你只想要 safetensors 格式，可以加这个参数
    # ignore_patterns=["*.bin", "*.pt"]
)
print(f"模型已下载到: {local_dir}")