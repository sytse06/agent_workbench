± uv run python scripts/scan/simple_ast_scanner.py overview
🔍 Code Overview
==================================================
📊 Summary:
  Classes: 136
  Functions: 63

📦 Classes:
  AgentConfigBase (src/agent_workbench/models/schemas.py:116)
    ↳ inherits from: BaseModel
    Methods (0):

  AgentConfigConflictError (src/agent_workbench/api/exceptions.py:97)
    ↳ inherits from: ConflictError
    Methods (1):
      • __init__(self, detail)

  AgentConfigCreate (src/agent_workbench/models/schemas.py:124)
    ↳ inherits from: AgentConfigBase
    Methods (0):

  AgentConfigInDB (src/agent_workbench/models/schemas.py:138)
    ↳ inherits from: AgentConfigBase
    Methods (0):

  AgentConfigModel (src/agent_workbench/models/database.py:167)
    ↳ inherits from: Base, TimestampMixin
    Methods (0):

  AgentConfigNotFoundError (src/agent_workbench/api/exceptions.py:86)
    ↳ inherits from: NotFoundError
    Methods (1):
      • __init__(self, config_id)

  AgentConfigResponse (src/agent_workbench/models/schemas.py:149)
    ↳ inherits from: AgentConfigInDB
    Methods (0):

  AgentConfigUpdate (src/agent_workbench/models/schemas.py:130)
    ↳ inherits from: BaseModel
    Methods (0):

  AgentWorkbenchError (src/agent_workbench/core/exceptions.py:6)
    ↳ inherits from: Exception
    Methods (1):
      • __init__(self, message, error_code)

  AnthropicProvider (src/agent_workbench/services/providers.py:197)
    ↳ inherits from: ProviderFactory
    Methods (1):
      • create_model(self, model_config)

  BusinessProfile (src/agent_workbench/models/business_models.py:23)
    ↳ inherits from: BaseModel
    Methods (1):
      • validate_website_url(cls, v)

  BusinessProfileDB (src/agent_workbench/models/business_models.py:71)
    ↳ inherits from: Base
    Methods (0):

  ChatRequest (src/agent_workbench/services/chat_models.py:22)
    ↳ inherits from: BaseModel
    Methods (0):

  ChatResponse (src/agent_workbench/services/chat_models.py:32)
    ↳ inherits from: BaseModel
    Methods (0):

  ChatService (src/agent_workbench/services/llm_service.py:19)
    Methods (3):
      • __init__(self, model_config)
      • chat_model(self)
      • _create_chat_model(self)

  ConflictError (src/agent_workbench/api/exceptions.py:53)
    ↳ inherits from: HTTPException
    Methods (1):
      • __init__(self, detail, error_code)

  ConsolidatedWorkbenchService (src/agent_workbench/services/consolidated_service.py:30)
    Methods (3):
      • __init__(self)
      • _ensure_uuid(self, conversation_id)
      • _convert_to_response(self, final_state)

  ConsolidatedWorkflowRequest (src/agent_workbench/models/consolidated_state.py:63)
    ↳ inherits from: BaseModel
    Methods (0):

  ConsolidatedWorkflowResponse (src/agent_workbench/models/consolidated_state.py:76)
    ↳ inherits from: BaseModel
    Methods (0):

  ContextService (src/agent_workbench/services/context_service.py:7)
    Methods (0):

  ContextUpdateRequest (src/agent_workbench/models/state_requests.py:56)
    ↳ inherits from: BaseModel
    Methods (0):

  ConversationBase (src/agent_workbench/models/schemas.py:42)
    ↳ inherits from: BaseModel
    Methods (0):

  ConversationCreate (src/agent_workbench/models/schemas.py:49)
    ↳ inherits from: ConversationBase
    Methods (0):

  ConversationError (src/agent_workbench/core/exceptions.py:31)
    ↳ inherits from: AgentWorkbenchError
    Methods (1):
      • __init__(self, message, conversation_id)

  ConversationInDB (src/agent_workbench/models/schemas.py:61)
    ↳ inherits from: ConversationBase
    Methods (0):

  ConversationModel (src/agent_workbench/models/database.py:35)
    ↳ inherits from: Base, TimestampMixin
    Methods (0):

  ConversationNotFoundError (src/agent_workbench/api/exceptions.py:66)
    ↳ inherits from: NotFoundError
    Methods (1):
      • __init__(self, conversation_id)

  ConversationResponse (src/agent_workbench/services/chat_models.py:40)
    ↳ inherits from: BaseModel
    Methods (0):

  ConversationService (src/agent_workbench/services/conversation_service.py:11)
    Methods (0):

  ConversationState (src/agent_workbench/models/standard_messages.py:24)
    ↳ inherits from: BaseModel
    Methods (0):

  ConversationStateDB (src/agent_workbench/models/conversation_state.py:11)
    ↳ inherits from: Base
    Methods (0):

  ConversationSummary (src/agent_workbench/models/schemas.py:173)
    ↳ inherits from: BaseModel
    Methods (0):

  ConversationUpdate (src/agent_workbench/models/schemas.py:55)
    ↳ inherits from: ConversationBase
    Methods (0):

  CreateConversationRequest (src/agent_workbench/services/chat_models.py:51)
    ↳ inherits from: BaseModel
    Methods (0):

  DatabaseConfig (src/agent_workbench/models/config.py:6)
    ↳ inherits from: BaseModel
    Methods (0):

  DatabaseError (src/agent_workbench/api/exceptions.py:8)
    ↳ inherits from: HTTPException
    Methods (1):
      • __init__(self, detail, error_code)

  DatabaseManager (src/agent_workbench/api/database.py:13)
    Methods (1):
      • __init__(self, config)

  DirectChatRequest (src/agent_workbench/api/routes/direct_chat.py:18)
    ↳ inherits from: BaseModel
    Methods (0):

  DirectChatResponse (src/agent_workbench/api/routes/direct_chat.py:29)
    ↳ inherits from: BaseModel
    Methods (0):

  DutchSEOPrompts (src/agent_workbench/core/dutch_prompts.py:6)
    Methods (5):
      • get_coaching_system_prompt(business_type)
      • get_analysis_prompt(website_url, business_context)
      • get_recommendations_prompt(analysis_results, business_profile)
      • get_implementation_guidance_prompt(recommendation, experience_level)
      • get_monitoring_prompt(business_profile)

  ErrorResponse (src/agent_workbench/models/schemas.py:166)
    ↳ inherits from: BaseModel
    Methods (0):

  HealthCheckResponse (src/agent_workbench/models/schemas.py:158)
    ↳ inherits from: BaseModel
    Methods (0):

  InterfaceCreationError (src/agent_workbench/ui/mode_factory.py:32)
    ↳ inherits from: ModeFactoryError
    Methods (0):

  InvalidModeError (src/agent_workbench/ui/mode_factory.py:26)
    ↳ inherits from: ModeFactoryError
    Methods (0):

  LLMProviderError (src/agent_workbench/core/exceptions.py:15)
    ↳ inherits from: AgentWorkbenchError
    Methods (1):
      • __init__(self, message, provider)

  LangGraphStateBridge (src/agent_workbench/services/langgraph_bridge.py:15)
    Methods (4):
      • __init__(self, state_manager, context_service)
      • _convert_messages_to_standard(self, messages)
      • _convert_context_data(self, context)
      • merge_workflow_context(self, base_context, workflow_context)

  MessageBase (src/agent_workbench/models/schemas.py:78)
    ↳ inherits from: BaseModel
    Methods (0):

  MessageConverter (src/agent_workbench/services/message_converter.py:15)
    Methods (3):
      • to_langchain_messages(messages)
      • from_langchain_message(message)
      • to_standard_messages(messages)

  MessageCreate (src/agent_workbench/models/schemas.py:87)
    ↳ inherits from: MessageBase
    Methods (0):

  MessageInDB (src/agent_workbench/models/schemas.py:100)
    ↳ inherits from: MessageBase
    Methods (0):

  MessageModel (src/agent_workbench/models/database.py:95)
    ↳ inherits from: Base
    Methods (0):

  MessageNotFoundError (src/agent_workbench/api/exceptions.py:77)
    ↳ inherits from: NotFoundError
    Methods (1):
      • __init__(self, message_id)

  MessageResponse (src/agent_workbench/models/schemas.py:110)
    ↳ inherits from: MessageInDB
    Methods (0):

  MessageUpdate (src/agent_workbench/models/schemas.py:93)
    ↳ inherits from: BaseModel
    Methods (0):

  MistralProvider (src/agent_workbench/services/providers.py:226)
    ↳ inherits from: ProviderFactory
    Methods (1):
      • create_model(self, model_config)

  ModeDetector (src/agent_workbench/services/mode_detector.py:13)
    Methods (5):
      • __init__(self, db_session)
      • detect_mode_from_environment(self)
      • detect_mode_from_request(self, request)
      • is_valid_mode(self, mode)
      • get_default_model_config_for_mode(self, mode)

  ModeFactory (src/agent_workbench/ui/mode_factory.py:38)
    Methods (7):
      • __init__(self)
      • create_interface(self, mode)
      • _determine_mode_safe(self, requested_mode)
      • _is_valid_mode(self, mode)
      • get_available_modes(self)
      • register_extension_mode(self, mode_name, interface_factory)
      • create_multi_mode_interface(self)

  ModeFactoryError (src/agent_workbench/ui/mode_factory.py:20)
    ↳ inherits from: Exception
    Methods (0):

  ModelConfig (src/agent_workbench/models/schemas.py:10)
    ↳ inherits from: BaseModel
    Methods (0):

  ModelConfigService (src/agent_workbench/services/model_config_service.py:17)
    Methods (10):
      • __init__(self)
      • refresh_config(self)
      • get_provider_choices(self)
      • get_model_options(self)
      • get_model_choices_for_ui(self)
      • get_provider_choices_for_ui(self)
      • parse_model_selection(self, display_name)
      • get_default_model_config(self)
      • _get_display_name(self, model_name)
      • get_models_by_provider(self, provider)

  ModelConfigurationError (src/agent_workbench/core/exceptions.py:23)
    ↳ inherits from: AgentWorkbenchError
    Methods (1):
      • __init__(self, message, model_config)

  ModelInfo (src/agent_workbench/services/chat_models.py:12)
    ↳ inherits from: BaseModel
    Methods (0):

  ModelOption (src/agent_workbench/services/model_config_service.py:9)
    Methods (0):

  ModelRegistry (src/agent_workbench/services/providers.py:23)
    Methods (7):
      • __init__(self)
      • _initialize_default_providers(self)
      • register_provider(self, config)
      • get_provider(self, provider_name)
      • get_available_providers(self)
      • get_provider_models(self, provider_name)
      • validate_model_config(self, provider, model_name)

  ModelTestRequest (src/agent_workbench/api/routes/direct_chat.py:40)
    ↳ inherits from: BaseModel
    Methods (0):

  ModelTestResponse (src/agent_workbench/api/routes/direct_chat.py:49)
    ↳ inherits from: BaseModel
    Methods (0):

  NotFoundError (src/agent_workbench/api/exceptions.py:22)
    ↳ inherits from: HTTPException
    Methods (1):
      • __init__(self, resource, resource_id, error_code)

  OllamaProvider (src/agent_workbench/services/providers.py:147)
    ↳ inherits from: ProviderFactory
    Methods (1):
      • create_model(self, model_config)

  OpenAIProvider (src/agent_workbench/services/providers.py:168)
    ↳ inherits from: ProviderFactory
    Methods (1):
      • create_model(self, model_config)

  OpenRouterProvider (src/agent_workbench/services/providers.py:117)
    ↳ inherits from: ProviderFactory
    Methods (1):
      • create_model(self, model_config)

  ProviderConfig (src/agent_workbench/services/providers.py:12)
    Methods (0):

  ProviderFactory (src/agent_workbench/services/providers.py:100)
    ↳ inherits from: ABC
    Methods (1):
      • create_model(self, model_config)

  RetryExhaustedError (src/agent_workbench/core/exceptions.py:46)
    ↳ inherits from: AgentWorkbenchError
    Methods (1):
      • __init__(self, message, attempts)

  SEOAnalysisContext (src/agent_workbench/models/business_models.py:43)
    ↳ inherits from: BaseModel
    Methods (0):

  SEOCoachModeHandler (src/agent_workbench/services/mode_handlers.py:200)
    Methods (2):
      • __init__(self, llm_service, context_service)
      • _get_dutch_coaching_config(self, state)

  SimpleLangGraphClient (src/agent_workbench/ui/components/simple_client.py:12)
    Methods (1):
      • __init__(self)

  StandardMessage (src/agent_workbench/models/standard_messages.py:13)
    ↳ inherits from: BaseModel
    Methods (0):

  StateManager (src/agent_workbench/services/state_manager.py:17)
    Methods (1):
      • __init__(self, db_session)

  StatefulLLMService (src/agent_workbench/services/stateful_llm_service.py:18)
    Methods (1):
      • __init__(self, llm_service, db_session)

  StreamingError (src/agent_workbench/core/exceptions.py:39)
    ↳ inherits from: AgentWorkbenchError
    Methods (1):
      • __init__(self, message)

  TemporaryManager (src/agent_workbench/services/temporary_manager.py:14)
    Methods (1):
      • __init__(self, db_session)

  TestAgentWorkbenchError (tests/unit/core/test_exceptions.py:10)
    Methods (2):
      • test_agent_workbench_error_creation(self)
      • test_agent_workbench_error_with_error_code(self)

  TestBusinessProfileForm (tests/ui/test_seo_coach_interface.py:21)
    Methods (13):
      • test_get_business_profile_form_components(self)
      • test_validate_business_profile_valid(self)
      • test_validate_business_profile_empty_name(self)
      • test_validate_business_profile_whitespace_name(self)
      • test_validate_business_profile_empty_url(self)
      • test_validate_business_profile_invalid_url_format(self)
      • test_validate_business_profile_ftp_url(self)
      • test_validate_business_profile_invalid_business_type(self)
      • test_validate_business_profile_all_valid_types(self, business_type)
      • test_create_business_profile_dict_complete(self)
      • test_create_business_profile_dict_with_whitespace(self)
      • test_create_business_profile_dict_empty_location(self)
      • test_create_business_profile_dict_whitespace_location(self)

  TestChatRequest (tests/unit/services/test_chat_models.py:77)
    Methods (2):
      • test_chat_request_creation(self)
      • test_chat_request_with_conversation_id(self)

  TestChatResponse (tests/unit/services/test_chat_models.py:104)
    Methods (1):
      • test_chat_response_creation(self)

  TestChatRoutes (tests/unit/api/routes/test_chat.py:15)
    Methods (5):
      • setup_method(self)
      • test_chat_completion(self, mock_create_chat_service)
      • test_chat_completion_with_conversation(self, mock_create_chat_service)
      • test_chat_completion_invalid_request(self, mock_create_chat_service)
      • test_stream_chat(self)

  TestChatService (tests/unit/services/test_llm_service.py:17)
    Methods (3):
      • setup_method(self)
      • test_chat_service_initialization(self)
      • test_chat_model_property(self)

  TestConsolidatedServiceIntegration (tests/ui/test_seo_coach_integration.py:408)
    Methods (0):

  TestConsolidatedWorkbenchService (tests/unit/services/test_consolidated_service.py:84)
    Methods (1):
      • test_convert_to_response(self, service, sample_workbench_state)

  TestConvenienceFunctions (tests/unit/services/test_llm_service.py:175)
    Methods (0):

  TestConversationResponse (tests/unit/services/test_chat_models.py:165)
    Methods (2):
      • test_conversation_response_creation(self)
      • test_conversation_response_with_model_config(self)

  TestConversationRoutes (tests/unit/api/routes/test_conversations.py:13)
    Methods (7):
      • test_get_conversations(self)
      • test_get_conversations_with_limit(self)
      • test_create_conversation(self, mock_conversation_service)
      • test_create_conversation_with_model_config(self, mock_conversation_service)
      • test_create_conversation_with_extra_fields(self)
      • test_get_conversation_by_id(self)
      • test_delete_conversation(self)

  TestConversationService (tests/unit/services/test_conversation_service.py:13)
    Methods (1):
      • setup_method(self)

  TestConversationSummary (tests/unit/services/test_chat_models.py:124)
    Methods (2):
      • test_conversation_summary_creation(self)
      • test_conversation_summary_with_model_config(self)

  TestCreateConversationRequest (tests/unit/services/test_chat_models.py:218)
    Methods (2):
      • test_create_conversation_request_creation(self)
      • test_create_conversation_request_with_model_config(self)

  TestDeploymentScenarios (tests/ui/test_dual_mode_integration.py:393)
    Methods (3):
      • test_docker_environment_simulation(self)
      • test_production_environment_simulation(self)
      • test_staging_environment_simulation(self)

  TestDocumentProcessingExtension (tests/ui/test_extension_pathways.py:87)
    Methods (3):
      • test_document_extension_registration(self)
      • test_document_extension_isolation(self)
      • test_document_extension_feature_placeholder(self)

  TestDualModeDeployment (tests/ui/test_dual_mode_integration.py:13)
    Methods (5):
      • test_workbench_mode_deployment(self)
      • test_seo_coach_mode_deployment(self)
      • test_invalid_mode_fallback(self)
      • test_detailed_health_check_workbench(self)
      • test_detailed_health_check_seo_coach(self)

  TestDutchMessages (tests/ui/test_seo_coach_interface.py:207)
    Methods (7):
      • test_dutch_messages_dict_exists(self)
      • test_required_message_keys_exist(self)
      • test_get_dutch_message_existing_key(self)
      • test_get_dutch_message_missing_key(self)
      • test_get_dutch_message_with_formatting(self)
      • test_get_dutch_message_without_formatting_params(self)
      • test_all_messages_are_dutch(self)

  TestEnvironmentIntegration (tests/ui/test_mode_factory.py:248)
    Methods (3):
      • test_app_mode_environment_variable(self)
      • test_no_environment_variable(self)
      • test_explicit_mode_overrides_environment(self)

  TestErrorHandlingIntegration (tests/ui/test_dual_mode_integration.py:275)
    Methods (4):
      • test_interface_creation_error_fallback(self)
      • test_invalid_mode_error_handling(self)
      • test_mode_info_error_handling(self)
      • test_health_check_degraded_state(self)

  TestExtensionIntegration (tests/ui/test_extension_pathways.py:255)
    Methods (5):
      • test_extension_mode_determination(self)
      • test_extension_environment_variable_support(self)
      • test_extension_mode_validation(self)
      • test_extension_error_handling(self)
      • test_extension_logging(self)

  TestExtensionRegistry (tests/ui/test_extension_pathways.py:14)
    Methods (5):
      • test_extension_registry_initialization(self)
      • test_extension_mode_registration(self)
      • test_multiple_extension_registration(self)
      • test_extension_mode_conflict_prevention(self)
      • test_extension_mode_available_modes_integration(self)

  TestLLMProviderError (tests/unit/core/test_exceptions.py:30)
    Methods (2):
      • test_llm_provider_error_creation(self)
      • test_llm_provider_error_with_provider(self)

  TestLangGraphIntegration (tests/ui/test_dual_mode_integration.py:179)
    Methods (0):

  TestLogging (tests/ui/test_mode_factory.py:296)
    Methods (3):
      • test_successful_interface_creation_logging(self)
      • test_invalid_mode_warning_logging(self)
      • test_extension_registration_logging(self)

  TestMCPToolExtension (tests/ui/test_extension_pathways.py:155)
    Methods (2):
      • test_mcp_tool_extension_registration(self)
      • test_mcp_tool_extension_feature_placeholder(self)

  TestModeFactory (tests/ui/test_mode_factory.py:36)
    Methods (10):
      • test_mode_factory_initialization(self)
      • test_mode_determination_logic(self)
      • test_interface_creation_success(self)
      • test_interface_creation_invalid_mode(self)
      • test_interface_creation_factory_returns_none(self)
      • test_interface_creation_factory_exception(self)
      • test_extension_mode_registration(self)
      • test_extension_mode_conflict(self)
      • test_extension_mode_interface_creation(self)
      • test_multi_mode_interface_not_implemented(self)

  TestModeFactoryHelperFunctions (tests/ui/test_mode_factory.py:183)
    Methods (5):
      • test_create_interface_for_mode_success(self)
      • test_create_interface_for_mode_error_handling(self)
      • test_get_mode_from_environment(self)
      • test_validate_mode_configuration(self)
      • test_get_available_modes_helper(self)

  TestModeIsolation (tests/ui/test_dual_mode_integration.py:102)
    Methods (3):
      • test_no_cross_mode_state_contamination(self)
      • test_mode_registry_isolation(self)
      • test_environment_isolation_between_tests(self)

  TestModelConfig (tests/unit/services/test_chat_models.py:15)
    Methods (2):
      • test_model_config_creation(self)
      • test_model_config_with_custom_values(self)

  TestModelConfigurationError (tests/unit/core/test_exceptions.py:52)
    Methods (2):
      • test_model_configuration_error_creation(self)
      • test_model_configuration_error_with_config(self)

  TestModelInfo (tests/unit/services/test_chat_models.py:57)
    Methods (1):
      • test_model_info_creation(self)

  TestModelRegistry (tests/unit/services/test_providers.py:42)
    Methods (6):
      • test_model_registry_initialization(self)
      • test_register_provider(self)
      • test_get_provider(self)
      • test_get_provider_not_found(self)
      • test_get_available_providers(self)
      • test_validate_model_config(self)

  TestModelRoutes (tests/unit/api/routes/test_models.py:12)
    Methods (3):
      • test_get_providers(self)
      • test_get_provider_models(self, mock_provider_registry)
      • test_get_provider_models_invalid_provider(self)

  TestMultiModeExtension (tests/ui/test_extension_pathways.py:215)
    Methods (2):
      • test_multi_mode_interface_not_implemented(self)
      • test_multi_mode_extension_feature_placeholder(self)

  TestPerformanceIntegration (tests/ui/test_dual_mode_integration.py:344)
    Methods (2):
      • test_mode_switching_performance(self)
      • test_interface_creation_caching(self)

  TestPhase2Readiness (tests/ui/test_extension_pathways.py:333)
    Methods (4):
      • test_extension_registry_persistence(self)
      • test_backward_compatibility_with_extensions(self)
      • test_extension_namespace_isolation(self)
      • test_extension_api_stability(self)

  TestProviderConfig (tests/unit/services/test_providers.py:18)
    Methods (1):
      • test_provider_config_creation(self)

  TestProviderFactories (tests/unit/services/test_providers.py:121)
    Methods (7):
      • test_provider_factories_exist(self)
      • test_openrouter_provider_creation(self, mock_chat_openai)
      • test_ollama_provider_creation(self, mock_chat_ollama)
      • test_openai_provider_creation(self, mock_chat_openai)
      • test_anthropic_provider_creation(self, mock_chat_anthropic)
      • test_mistral_provider_creation(self, mock_chat_mistral)
      • test_provider_factory_import_error(self)

  TestRetryDecorators (tests/unit/core/test_retry.py:13)
    Methods (2):
      • test_retry_api_call_success(self)
      • test_retry_database_operation_success(self)

  TestSEOCoachApp (tests/ui/test_seo_coach_interface.py:294)
    Methods (4):
      • test_create_seo_coach_app(self)
      • test_seo_coach_app_has_required_components(self)
      • test_seo_coach_app_structure(self)
      • test_seo_coach_app_css_styling(self)

  TestSEOCoachAppIntegration (tests/ui/test_seo_coach_integration.py:365)
    Methods (2):
      • test_seo_coach_app_full_creation(self)
      • test_seo_coach_app_event_handlers_attached(self)

  TestSEOCoachIntegration (tests/ui/test_seo_coach_integration.py:19)
    Methods (0):

  TestValidationResult (tests/unit/services/test_chat_models.py:239)
    Methods (2):
      • test_validation_result_creation(self)
      • test_validation_result_with_errors(self)

  TimestampMixin (src/agent_workbench/models/database.py:26)
    Methods (0):

  ValidationError (src/agent_workbench/api/exceptions.py:41)
    ↳ inherits from: HTTPException
    Methods (1):
      • __init__(self, detail, error_code)

  ValidationResult (src/agent_workbench/services/chat_models.py:60)
    ↳ inherits from: BaseModel
    Methods (0):

  WorkbenchLangGraphService (src/agent_workbench/services/langgraph_service.py:15)
    Methods (3):
      • __init__(self, state_bridge, llm_service, context_service)
      • _build_workflow(self)
      • _create_initial_state(self, request)

  WorkbenchModeHandler (src/agent_workbench/services/mode_handlers.py:18)
    Methods (3):
      • __init__(self, llm_service, context_service)
      • _apply_parameter_overrides(self, config, overrides)
      • _build_technical_context(self, state)

  WorkbenchState (src/agent_workbench/models/consolidated_state.py:14)
    ↳ inherits from: TypedDict
    Methods (0):

  WorkflowExecution (src/agent_workbench/models/business_models.py:55)
    ↳ inherits from: BaseModel
    Methods (0):

  WorkflowExecutionDB (src/agent_workbench/models/business_models.py:88)
    ↳ inherits from: Base
    Methods (0):

  WorkflowNodes (src/agent_workbench/services/workflow_nodes.py:14)
    Methods (3):
      • __init__(self, state_bridge, llm_service, context_service)
      • _build_seo_coaching_context(self, business_profile, seo_analysis, context)
      • _get_dutch_coaching_config(self)

  WorkflowOrchestrator (src/agent_workbench/services/workflow_orchestrator.py:14)
    Methods (3):
      • __init__(self, state_bridge, workbench_handler, seo_coach_handler)
      • _build_consolidated_workflow(self)
      • _route_by_mode(self, state)

  WorkflowUpdate (src/agent_workbench/models/consolidated_state.py:90)
    ↳ inherits from: BaseModel
    Methods (0):
