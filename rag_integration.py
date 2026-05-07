"""
rag_integration.py - RAG系统集成示例

展示如何将清洗后的Docker文档数据集成到LangChain RAG系统中
"""

import json
from pathlib import Path
from typing import List, Dict
from langchain_community.document_loaders import JSONLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings, ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser


class DockerRAGSystem:
    """Docker文档RAG系统"""
    
    def __init__(self, data_dir: str = "processed_data", persist_dir: str = "chroma_db"):
        self.data_dir = Path(data_dir)
        self.persist_dir = persist_dir
        
        # 初始化embedding模型
        self.embeddings = OllamaEmbeddings(model="nomic-embed-text")
        
        # 初始化向量数据库
        self.vectorstore = None
        
        # 初始化LLM
        self.llm = ChatOllama(model="qwen2.5:7b", temperature=0)
        
    def load_documents(self) -> List:
        """加载清洗后的文档"""
        json_file = self.data_dir / "docker_docs.json"
        
        if not json_file.exists():
            raise FileNotFoundError(f"Data file not found: {json_file}")
        
        print(f"Loading documents from {json_file}...")
        
        # 使用JSONLoader加载
        loader = JSONLoader(
            file_path=str(json_file),
            jq_schema='.[]',
            text_content=False
        )
        
        documents = loader.load()
        print(f"Loaded {len(documents)} documents")
        
        return documents
    
    def filter_by_type(self, documents: List, doc_type: str) -> List:
        """按文档类型过滤"""
        filtered = [
            doc for doc in documents 
            if doc.metadata.get('doc_type') == doc_type
        ]
        print(f"Filtered to {len(filtered)} {doc_type} documents")
        return filtered
    
    def build_vectorstore(self, documents: List = None, use_filter: bool = False):
        """构建向量数据库"""
        if documents is None:
            documents = self.load_documents()
        
        # 可选：只为特定类型构建索引
        if use_filter:
            # 为每种类型创建独立的vectorstore
            for doc_type in ['get-started', 'guides', 'manuals', 'reference']:
                type_docs = self.filter_by_type(documents, doc_type)
                if type_docs:
                    vs = Chroma.from_documents(
                        documents=type_docs,
                        embedding=self.embeddings,
                        persist_directory=f"{self.persist_dir}_{doc_type}"
                    )
                    vs.persist()
                    print(f"Built vectorstore for {doc_type}")
        else:
            # 构建统一的vectorstore
            self.vectorstore = Chroma.from_documents(
                documents=documents,
                embedding=self.embeddings,
                persist_directory=self.persist_dir
            )
            self.vectorstore.persist()
            print("Built unified vectorstore")
    
    def load_vectorstore(self, doc_type: str = None):
        """加载已有的向量数据库"""
        if doc_type:
            persist_dir = f"{self.persist_dir}_{doc_type}"
        else:
            persist_dir = self.persist_dir
        
        self.vectorstore = Chroma(
            persist_directory=persist_dir,
            embedding_function=self.embeddings
        )
        print(f"Loaded vectorstore from {persist_dir}")
    
    def create_retriever(self, doc_type: str = None, k: int = 4):
        """创建检索器"""
        if self.vectorstore is None:
            self.load_vectorstore(doc_type)
        
        retriever = self.vectorstore.as_retriever(
            search_kwargs={"k": k}
        )
        
        # 可以添加元数据过滤
        if doc_type:
            retriever = self.vectorstore.as_retriever(
                search_kwargs={
                    "k": k,
                    "filter": {"doc_type": doc_type}
                }
            )
        
        return retriever
    
    def build_rag_chain(self, doc_type: str = None):
        """构建完整的RAG链"""
        retriever = self.create_retriever(doc_type)
        
        # 定义提示词模板（针对Docker运维优化）
        template = """你是Docker运维与部署专家助手。基于以下上下文回答问题。

上下文信息：
{context}

问题：{question}

请提供专业、准确的回答。如果上下文中没有相关信息，请明确说明。

回答："""
        
        prompt = ChatPromptTemplate.from_template(template)
        
        # 构建RAG链
        rag_chain = (
            {"context": retriever, "question": RunnablePassthrough()}
            | prompt
            | self.llm
            | StrOutputParser()
        )
        
        return rag_chain
    
    def query(self, question: str, doc_type: str = None) -> str:
        """执行查询"""
        chain = self.build_rag_chain(doc_type)
        answer = chain.invoke(question)
        return answer
    
    def hybrid_search(self, question: str, top_k: int = 2) -> Dict[str, str]:
        """混合搜索：从不同类型获取答案"""
        results = {}
        
        # 从每个类型检索
        for doc_type in ['get-started', 'guides', 'manuals', 'reference']:
            try:
                retriever = self.create_retriever(doc_type, k=top_k)
                docs = retriever.invoke(question)
                
                if docs:
                    # 合并该类型的结果
                    context = "\n\n".join([doc.page_content for doc in docs])
                    results[doc_type] = context
            except Exception as e:
                print(f"Error searching {doc_type}: {e}")
        
        # 如果有结果，用LLM综合回答
        if results:
            combined_context = "\n\n===\n\n".join([
                f"[{k.upper()}]\n{v}" for k, v in results.items()
            ])
            
            template = """你是Docker运维专家。综合以下来自不同文档类型的信息回答问题。

{context}

问题：{question}

请综合以上信息给出完整回答，并注明信息来源类型。

回答："""
            
            prompt = ChatPromptTemplate.from_template(template)
            chain = prompt | self.llm | StrOutputParser()
            
            answer = chain.invoke({
                "context": combined_context,
                "question": question
            })
            
            return answer
        else:
            return "未找到相关文档。"


def demo():
    """演示用法"""
    print("=" * 60)
    print("Docker RAG系统演示")
    print("=" * 60)
    
    # 初始化系统
    rag_system = DockerRAGSystem()
    
    # 1. 加载并构建索引
    print("\n1. 构建向量数据库...")
    rag_system.build_vectorstore()
    
    # 2. 简单查询示例
    print("\n2. 执行查询示例...")
    
    questions = [
        ("如何安装Docker？", "get-started"),
        ("如何在Docker中运行MySQL？", "guides"),
        ("Docker Desktop如何配置代理？", "manuals"),
        ("docker build命令有哪些参数？", "reference"),
    ]
    
    for question, doc_type in questions:
        print(f"\n问题: {question}")
        print(f"文档类型: {doc_type}")
        answer = rag_system.query(question, doc_type)
        print(f"回答: {answer[:200]}...")
        print("-" * 60)
    
    # 3. 混合搜索示例
    print("\n3. 混合搜索示例...")
    complex_question = "如何在生产环境部署Docker应用并确保安全性？"
    print(f"问题: {complex_question}")
    answer = rag_system.hybrid_search(complex_question)
    print(f"回答: {answer[:300]}...")


if __name__ == "__main__":
    demo()
