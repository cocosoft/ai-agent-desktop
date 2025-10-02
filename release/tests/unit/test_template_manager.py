"""
代理模板管理器单元测试
测试模板管理器的功能
"""

import pytest
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch

from src.core.template_manager import TemplateManager, get_template_manager, create_predefined_templates
from src.core.agent_model import AgentRegistry, AgentTemplate, AgentType, AgentConfig, AgentCapabilityMapping


class TestTemplateManager:
    """模板管理器测试"""
    
    @pytest.fixture
    def agent_registry(self):
        """创建代理注册表"""
        return AgentRegistry()
    
    @pytest.fixture
    def template_manager(self, agent_registry):
        """创建模板管理器"""
        return TemplateManager(agent_registry)
    
    @pytest.fixture
    def sample_template_data(self):
        """创建示例模板数据"""
        return {
            "name": "测试模板",
            "description": "测试模板描述",
            "agent_type": AgentType.TEXT_GENERATION,
            "base_capabilities": ["text_generation", "text_summarization"],
            "recommended_models": {
                "text_generation": ["gpt-3.5-turbo", "gpt-4"],
                "text_summarization": ["gpt-3.5-turbo"]
            },
            "default_settings": {
                "max_concurrent_tasks": 3,
                "auto_start": True
            },
            "category": "test",
            "tags": ["test", "template"]
        }
    
    def test_template_manager_creation(self, template_manager):
        """测试模板管理器创建"""
        assert template_manager is not None
        assert template_manager.agent_registry is not None
        assert template_manager.logger is not None
        assert isinstance(template_manager.custom_templates, dict)
    
    def test_create_template(self, template_manager, sample_template_data):
        """测试创建模板"""
        template = template_manager.create_template(**sample_template_data)
        
        assert template is not None
        assert template.name == sample_template_data["name"]
        assert template.description == sample_template_data["description"]
        assert template.agent_type == sample_template_data["agent_type"]
        assert template.base_capabilities == sample_template_data["base_capabilities"]
        assert template.recommended_models == sample_template_data["recommended_models"]
        assert template.default_settings == sample_template_data["default_settings"]
        assert template.category == sample_template_data["category"]
        assert template.tags == sample_template_data["tags"]
        
        # 验证模板已添加到自定义模板
        assert template.template_id in template_manager.custom_templates
    
    def test_get_template_default(self, template_manager, agent_registry):
        """测试获取默认模板"""
        # 获取默认模板
        template = template_manager.get_template("text_generation_basic")
        
        assert template is not None
        assert template.name == "基础文本生成代理"
        assert template.agent_type == AgentType.TEXT_GENERATION
    
    def test_get_template_custom(self, template_manager, sample_template_data):
        """测试获取自定义模板"""
        # 创建自定义模板
        template = template_manager.create_template(**sample_template_data)
        
        # 获取自定义模板
        retrieved_template = template_manager.get_template(template.template_id)
        
        assert retrieved_template is not None
        assert retrieved_template.template_id == template.template_id
        assert retrieved_template.name == template.name
    
    def test_list_all_templates(self, template_manager, sample_template_data):
        """测试列出所有模板"""
        # 创建自定义模板
        template_manager.create_template(**sample_template_data)
        
        # 获取所有模板
        all_templates = template_manager.list_all_templates()
        
        assert len(all_templates) > 0
        
        # 应该包含默认模板和自定义模板
        default_template_names = [t.name for t in template_manager.agent_registry.list_templates()]
        custom_template_names = [t.name for t in template_manager.custom_templates.values()]
        
        for template in all_templates:
            assert template.name in default_template_names or template.name in custom_template_names
    
    def test_search_templates(self, template_manager, sample_template_data):
        """测试搜索模板"""
        # 创建自定义模板
        template_manager.create_template(**sample_template_data)
        
        # 搜索模板
        results = template_manager.search_templates("测试")
        
        assert len(results) > 0
        assert any("测试" in template.name for template in results)
    
    def test_search_templates_by_category(self, template_manager, sample_template_data):
        """测试按分类搜索模板"""
        # 创建自定义模板
        template_manager.create_template(**sample_template_data)
        
        # 按分类搜索
        results = template_manager.search_templates("", category="test")
        
        assert len(results) > 0
        assert all(template.category == "test" for template in results)
    
    def test_export_template(self, template_manager, sample_template_data):
        """测试导出模板"""
        # 创建自定义模板
        template = template_manager.create_template(**sample_template_data)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            export_path = f.name
        
        try:
            # 导出模板
            success = template_manager.export_template(template.template_id, export_path)
            
            assert success is True
            
            # 验证导出的文件内容
            with open(export_path, 'r', encoding='utf-8') as f:
                exported_data = json.load(f)
            
            assert exported_data["name"] == template.name
            assert exported_data["description"] == template.description
            assert exported_data["agent_type"] == template.agent_type.value
            
        finally:
            # 清理临时文件
            if os.path.exists(export_path):
                os.unlink(export_path)
    
    def test_import_template(self, template_manager, sample_template_data):
        """测试导入模板"""
        # 创建模板数据文件
        template_data = {
            "template_id": "test_import_template",
            "name": "导入测试模板",
            "description": "导入测试模板描述",
            "agent_type": "text_generation",
            "base_capabilities": ["text_generation"],
            "recommended_models": {
                "text_generation": ["gpt-3.5-turbo"]
            },
            "default_settings": {
                "max_concurrent_tasks": 2,
                "auto_start": False
            },
            "category": "imported",
            "tags": ["imported"],
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00"
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
            json.dump(template_data, f, ensure_ascii=False)
            import_path = f.name
        
        try:
            # 导入模板
            imported_template = template_manager.import_template(import_path)
            
            assert imported_template is not None
            assert imported_template.name == template_data["name"]
            assert imported_template.description == template_data["description"]
            assert imported_template.agent_type.value == template_data["agent_type"]
            
            # 验证模板已添加到自定义模板
            assert imported_template.template_id in template_manager.custom_templates
            
        finally:
            # 清理临时文件
            if os.path.exists(import_path):
                os.unlink(import_path)
    
    def test_duplicate_template(self, template_manager, sample_template_data):
        """测试复制模板"""
        # 创建原始模板
        original_template = template_manager.create_template(**sample_template_data)
        
        # 复制模板
        new_name = "复制的测试模板"
        new_description = "复制的测试模板描述"
        duplicated_template = template_manager.duplicate_template(
            original_template.template_id, new_name, new_description
        )
        
        assert duplicated_template is not None
        assert duplicated_template.name == new_name
        assert duplicated_template.description == new_description
        assert duplicated_template.agent_type == original_template.agent_type
        assert duplicated_template.base_capabilities == original_template.base_capabilities
        assert duplicated_template.recommended_models == original_template.recommended_models
        assert duplicated_template.default_settings == original_template.default_settings
        
        # 验证新模板已添加到自定义模板
        assert duplicated_template.template_id in template_manager.custom_templates
    
    def test_get_template_categories(self, template_manager, sample_template_data):
        """测试获取模板分类"""
        # 创建自定义模板
        template_manager.create_template(**sample_template_data)
        
        categories = template_manager.get_template_categories()
        
        assert len(categories) > 0
        assert "test" in categories  # 我们创建的模板分类
    
    def test_get_templates_by_category(self, template_manager, sample_template_data):
        """测试按分类获取模板"""
        # 创建自定义模板
        template_manager.create_template(**sample_template_data)
        
        templates = template_manager.get_templates_by_category("test")
        
        assert len(templates) > 0
        assert all(template.category == "test" for template in templates)
    
    def test_update_template(self, template_manager, sample_template_data):
        """测试更新模板"""
        # 创建模板
        template = template_manager.create_template(**sample_template_data)
        
        # 更新模板
        new_name = "更新后的模板名称"
        new_description = "更新后的模板描述"
        success = template_manager.update_template(
            template.template_id,
            name=new_name,
            description=new_description
        )
        
        assert success is True
        
        # 验证更新
        updated_template = template_manager.get_template(template.template_id)
        assert updated_template.name == new_name
        assert updated_template.description == new_description
    
    def test_delete_template(self, template_manager, sample_template_data):
        """测试删除模板"""
        # 创建模板
        template = template_manager.create_template(**sample_template_data)
        
        # 删除模板
        success = template_manager.delete_template(template.template_id)
        
        assert success is True
        
        # 验证模板已删除
        assert template.template_id not in template_manager.custom_templates
    
    def test_create_template_from_agent(self, template_manager, agent_registry):
        """测试从代理配置创建模板"""
        # 创建代理配置
        agent_config = AgentConfig(
            agent_id="test_agent",
            name="测试代理",
            description="测试代理描述",
            agent_type=AgentType.TEXT_GENERATION,
            capabilities=[
                AgentCapabilityMapping(
                    capability_id="text_generation",
                    model_id="gpt-3.5-turbo",
                    priority=1,
                    enabled=True
                ),
                AgentCapabilityMapping(
                    capability_id="text_summarization",
                    model_id="gpt-3.5-turbo",
                    priority=2,
                    enabled=True
                )
            ],
            max_concurrent_tasks=3,
            auto_start=True,
            health_check_interval=30,
            max_restart_attempts=3,
            restart_delay=5
        )
        
        # 从代理配置创建模板
        template_name = "从代理创建的模板"
        template_description = "从代理配置创建的模板描述"
        template = template_manager.create_template_from_agent(
            agent_config, template_name, template_description
        )
        
        assert template is not None
        assert template.name == template_name
        assert template.description == template_description
        assert template.agent_type == agent_config.agent_type
        assert len(template.base_capabilities) == 2
        assert "text_generation" in template.base_capabilities
        assert "text_summarization" in template.base_capabilities
        assert template.default_settings["max_concurrent_tasks"] == 3
        assert template.default_settings["auto_start"] is True


class TestGlobalFunctions:
    """全局函数测试"""
    
    @pytest.fixture
    def agent_registry(self):
        """创建代理注册表"""
        return AgentRegistry()
    
    def test_get_template_manager(self, agent_registry):
        """测试获取全局模板管理器"""
        manager1 = get_template_manager(agent_registry)
        manager2 = get_template_manager(agent_registry)
        
        assert manager1 is not None
        assert manager2 is not None
        assert manager1 is manager2  # 应该是同一个实例
    
    def test_create_predefined_templates(self, agent_registry):
        """测试创建预定义模板"""
        template_manager = create_predefined_templates(agent_registry)
        
        assert template_manager is not None
        
        # 验证预定义模板已创建
        all_templates = template_manager.list_all_templates()
        
        # 应该包含默认模板和预定义模板
        template_names = [t.name for t in all_templates]
        
        assert "专业翻译代理" in template_names
        assert "智能问答代理" in template_names
        assert "高效文本摘要代理" in template_names


class TestTemplateIntegration:
    """模板集成测试"""
    
    @pytest.fixture
    def agent_registry(self):
        """创建代理注册表"""
        return AgentRegistry()
    
    @pytest.fixture
    def template_manager(self, agent_registry):
        """创建模板管理器"""
        return TemplateManager(agent_registry)
    
    def test_template_to_agent_creation(self, template_manager, agent_registry):
        """测试从模板创建代理"""
        # 获取默认模板
        template = template_manager.get_template("text_generation_basic")
        assert template is not None
        
        # 从模板创建代理
        agent_config = agent_registry.create_agent_from_template(
            template.template_id,
            "从模板创建的代理",
            "从模板创建的代理描述"
        )
        
        assert agent_config is not None
        assert agent_config.name == "从模板创建的代理"
        assert agent_config.agent_type == template.agent_type
        assert len(agent_config.capabilities) == len(template.base_capabilities)
        
        # 验证代理已注册
        assert agent_config.agent_id in agent_registry.agents
    
    def test_template_management_workflow(self, template_manager, agent_registry):
        """测试模板管理完整工作流"""
        # 1. 创建模板
        template_data = {
            "name": "工作流测试模板",
            "description": "工作流测试模板描述",
            "agent_type": AgentType.CODE_GENERATION,
            "base_capabilities": ["code_generation"],
            "recommended_models": {
                "code_generation": ["gpt-4", "claude-3-sonnet"]
            },
            "default_settings": {
                "max_concurrent_tasks": 2,
                "auto_start": True
            },
            "category": "workflow",
            "tags": ["workflow", "test"]
        }
        
        template = template_manager.create_template(**template_data)
        assert template is not None
        
        # 2. 导出模板
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            export_path = f.name
        
        try:
            success = template_manager.export_template(template.template_id, export_path)
            assert success is True
            
            # 3. 删除模板
            success = template_manager.delete_template(template.template_id)
            assert success is True
            
            # 4. 导入模板
            imported_template = template_manager.import_template(export_path)
            assert imported_template is not None
            assert imported_template.name == template_data["name"]
            
        finally:
            if os.path.exists(export_path):
                os.unlink(export_path)


# 运行测试
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
