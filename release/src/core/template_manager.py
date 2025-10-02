"""
代理模板管理器
负责代理模板的创建、导入、导出、分享等管理功能
"""

import json
import os
import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path

from .agent_model import AgentTemplate, AgentType, AgentRegistry
from ..utils.logger import get_log_manager


class TemplateManager:
    """代理模板管理器"""
    
    def __init__(self, agent_registry: AgentRegistry):
        self.agent_registry = agent_registry
        self.logger = get_log_manager().logger
        self.custom_templates: Dict[str, AgentTemplate] = {}
        self._load_custom_templates()
    
    def _load_custom_templates(self):
        """加载自定义模板"""
        # 从配置文件加载自定义模板
        config_dir = Path("config/templates")
        config_dir.mkdir(parents=True, exist_ok=True)
        
        template_files = list(config_dir.glob("*.json"))
        for template_file in template_files:
            try:
                with open(template_file, 'r', encoding='utf-8') as f:
                    template_data = json.load(f)
                
                template = AgentTemplate.from_dict(template_data)
                self.custom_templates[template.template_id] = template
                self.logger.info(f"加载自定义模板: {template.name}")
                
            except Exception as e:
                self.logger.error(f"加载模板文件失败 {template_file}: {str(e)}")
    
    def create_template(self, name: str, description: str, agent_type: AgentType,
                       base_capabilities: List[str], recommended_models: Dict[str, List[str]],
                       default_settings: Dict[str, Any], category: str = "custom",
                       tags: List[str] = None) -> Optional[AgentTemplate]:
        """创建自定义模板"""
        try:
            template_id = f"custom_{str(uuid.uuid4())[:8]}"
            
            template = AgentTemplate(
                template_id=template_id,
                name=name,
                description=description,
                agent_type=agent_type,
                base_capabilities=base_capabilities,
                recommended_models=recommended_models,
                default_settings=default_settings,
                category=category,
                tags=tags or []
            )
            
            # 保存到自定义模板
            self.custom_templates[template_id] = template
            
            # 保存到文件
            self._save_template_to_file(template)
            
            self.logger.info(f"创建自定义模板: {name}")
            return template
            
        except Exception as e:
            self.logger.error(f"创建模板失败: {str(e)}")
            return None
    
    def _save_template_to_file(self, template: AgentTemplate):
        """保存模板到文件"""
        try:
            config_dir = Path("config/templates")
            config_dir.mkdir(parents=True, exist_ok=True)
            
            template_file = config_dir / f"{template.template_id}.json"
            with open(template_file, 'w', encoding='utf-8') as f:
                json.dump(template.to_dict(), f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            self.logger.error(f"保存模板文件失败: {str(e)}")
    
    def update_template(self, template_id: str, **kwargs) -> bool:
        """更新模板"""
        template = self.get_template(template_id)
        if not template:
            return False
        
        try:
            # 更新模板属性
            for key, value in kwargs.items():
                if hasattr(template, key):
                    setattr(template, key, value)
            
            template.updated_at = datetime.now()
            
            # 保存到文件
            self._save_template_to_file(template)
            
            self.logger.info(f"更新模板: {template.name}")
            return True
            
        except Exception as e:
            self.logger.error(f"更新模板失败: {str(e)}")
            return False
    
    def delete_template(self, template_id: str) -> bool:
        """删除模板"""
        if template_id not in self.custom_templates:
            return False
        
        try:
            template = self.custom_templates[template_id]
            
            # 删除文件
            config_dir = Path("config/templates")
            template_file = config_dir / f"{template_id}.json"
            if template_file.exists():
                template_file.unlink()
            
            # 从内存中删除
            del self.custom_templates[template_id]
            
            self.logger.info(f"删除模板: {template.name}")
            return True
            
        except Exception as e:
            self.logger.error(f"删除模板失败: {str(e)}")
            return False
    
    def get_template(self, template_id: str) -> Optional[AgentTemplate]:
        """获取模板（包括默认模板和自定义模板）"""
        # 先检查自定义模板
        if template_id in self.custom_templates:
            return self.custom_templates[template_id]
        
        # 然后检查默认模板
        return self.agent_registry.get_template(template_id)
    
    def list_all_templates(self) -> List[AgentTemplate]:
        """列出所有模板（默认模板 + 自定义模板）"""
        default_templates = self.agent_registry.list_templates()
        custom_templates = list(self.custom_templates.values())
        return default_templates + custom_templates
    
    def search_templates(self, query: str, category: Optional[str] = None) -> List[AgentTemplate]:
        """搜索模板"""
        all_templates = self.list_all_templates()
        results = []
        
        for template in all_templates:
            # 按名称和描述搜索
            if (query.lower() in template.name.lower() or 
                query.lower() in template.description.lower()):
                if category is None or template.category == category:
                    results.append(template)
        
        return results
    
    def export_template(self, template_id: str, export_path: str) -> bool:
        """导出模板到文件"""
        template = self.get_template(template_id)
        if not template:
            return False
        
        try:
            template_data = template.to_dict()
            
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(template_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"导出模板到: {export_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"导出模板失败: {str(e)}")
            return False
    
    def import_template(self, import_path: str) -> Optional[AgentTemplate]:
        """从文件导入模板"""
        try:
            with open(import_path, 'r', encoding='utf-8') as f:
                template_data = json.load(f)
            
            # 验证模板数据
            required_fields = ["template_id", "name", "description", "agent_type"]
            for field in required_fields:
                if field not in template_data:
                    raise ValueError(f"缺少必需字段: {field}")
            
            # 创建新模板ID避免冲突
            original_id = template_data["template_id"]
            template_data["template_id"] = f"imported_{str(uuid.uuid4())[:8]}"
            
            template = AgentTemplate.from_dict(template_data)
            
            # 保存为自定义模板
            self.custom_templates[template.template_id] = template
            self._save_template_to_file(template)
            
            self.logger.info(f"导入模板: {template.name} (原ID: {original_id})")
            return template
            
        except Exception as e:
            self.logger.error(f"导入模板失败: {str(e)}")
            return None
    
    def duplicate_template(self, template_id: str, new_name: str, new_description: str = None) -> Optional[AgentTemplate]:
        """复制模板"""
        template = self.get_template(template_id)
        if not template:
            return None
        
        try:
            new_template_id = f"copy_{str(uuid.uuid4())[:8]}"
            
            new_template = AgentTemplate(
                template_id=new_template_id,
                name=new_name,
                description=new_description or template.description,
                agent_type=template.agent_type,
                base_capabilities=template.base_capabilities.copy(),
                recommended_models=template.recommended_models.copy(),
                default_settings=template.default_settings.copy(),
                category=template.category,
                tags=template.tags.copy()
            )
            
            # 保存为自定义模板
            self.custom_templates[new_template_id] = new_template
            self._save_template_to_file(new_template)
            
            self.logger.info(f"复制模板: {template.name} -> {new_name}")
            return new_template
            
        except Exception as e:
            self.logger.error(f"复制模板失败: {str(e)}")
            return None
    
    def get_template_categories(self) -> List[str]:
        """获取所有模板分类"""
        all_templates = self.list_all_templates()
        categories = set()
        
        for template in all_templates:
            categories.add(template.category)
        
        return sorted(list(categories))
    
    def get_templates_by_category(self, category: str) -> List[AgentTemplate]:
        """按分类获取模板"""
        all_templates = self.list_all_templates()
        return [t for t in all_templates if t.category == category]
    
    def create_template_from_agent(self, agent_config, template_name: str, template_description: str) -> Optional[AgentTemplate]:
        """从现有代理配置创建模板"""
        try:
            template_id = f"from_agent_{str(uuid.uuid4())[:8]}"
            
            # 提取基础能力
            base_capabilities = [mapping.capability_id for mapping in agent_config.capabilities]
            
            # 构建推荐模型映射
            recommended_models = {}
            for mapping in agent_config.capabilities:
                if mapping.capability_id not in recommended_models:
                    recommended_models[mapping.capability_id] = []
                if mapping.model_id and mapping.model_id not in recommended_models[mapping.capability_id]:
                    recommended_models[mapping.capability_id].append(mapping.model_id)
            
            # 构建默认设置
            default_settings = {
                "max_concurrent_tasks": agent_config.max_concurrent_tasks,
                "auto_start": agent_config.auto_start,
                "priority": agent_config.priority.value,
                "health_check_interval": agent_config.health_check_interval,
                "max_restart_attempts": agent_config.max_restart_attempts,
                "restart_delay": agent_config.restart_delay
            }
            
            template = AgentTemplate(
                template_id=template_id,
                name=template_name,
                description=template_description,
                agent_type=agent_config.agent_type,
                base_capabilities=base_capabilities,
                recommended_models=recommended_models,
                default_settings=default_settings,
                category="from_agent",
                tags=["from_existing_agent"]
            )
            
            # 保存为自定义模板
            self.custom_templates[template_id] = template
            self._save_template_to_file(template)
            
            self.logger.info(f"从代理创建模板: {template_name}")
            return template
            
        except Exception as e:
            self.logger.error(f"从代理创建模板失败: {str(e)}")
            return None


# 全局模板管理器实例
_template_manager: Optional[TemplateManager] = None


def get_template_manager(agent_registry: AgentRegistry) -> TemplateManager:
    """获取全局模板管理器实例"""
    global _template_manager
    if _template_manager is None:
        _template_manager = TemplateManager(agent_registry)
    return _template_manager


# 预定义模板创建函数
def create_predefined_templates(agent_registry: AgentRegistry):
    """创建预定义模板"""
    template_manager = get_template_manager(agent_registry)
    
    # 翻译代理模板
    translation_template = template_manager.create_template(
        name="专业翻译代理",
        description="用于多语言翻译的专业代理模板",
        agent_type=AgentType.TRANSLATION,
        base_capabilities=["translation"],
        recommended_models={
            "translation": ["gpt-4", "claude-3-sonnet", "deepseek-translator"]
        },
        default_settings={
            "max_concurrent_tasks": 4,
            "auto_start": True,
            "priority": "normal"
        },
        category="translation",
        tags=["translation", "multilingual", "professional"]
    )
    
    # 问答代理模板
    qa_template = template_manager.create_template(
        name="智能问答代理",
        description="用于问答和知识检索的智能代理模板",
        agent_type=AgentType.QUESTION_ANSWERING,
        base_capabilities=["question_answering"],
        recommended_models={
            "question_answering": ["gpt-4", "claude-3-sonnet", "llama-3-70b"]
        },
        default_settings={
            "max_concurrent_tasks": 3,
            "auto_start": True,
            "priority": "high"
        },
        category="qa",
        tags=["qa", "knowledge", "intelligent"]
    )
    
    # 文本摘要代理模板
    summarization_template = template_manager.create_template(
        name="高效文本摘要代理",
        description="用于文本摘要和内容提炼的高效代理模板",
        agent_type=AgentType.TEXT_SUMMARIZATION,
        base_capabilities=["text_summarization"],
        recommended_models={
            "text_summarization": ["gpt-3.5-turbo", "claude-3-haiku", "bart-large-cnn"]
        },
        default_settings={
            "max_concurrent_tasks": 6,
            "auto_start": True,
            "priority": "normal"
        },
        category="summarization",
        tags=["summarization", "efficient", "content"]
    )
    
    return template_manager
