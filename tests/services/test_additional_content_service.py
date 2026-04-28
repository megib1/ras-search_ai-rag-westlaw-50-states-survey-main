# import asyncio
# from unittest.mock import patch
#
# import pytest
# from aalp_service.v2.config import CobaltSettings
# from aalp_service.v2.rag.config import RAGSettings
# from conversation_core.shared.enums import AdditionalContentTypes
#
# from app.models.search_summarization_result import AdditionalSupportingMaterial, AdditionalContent
# from app.services.additional_content_service import additional_content_search
#
# pytest_plugins = ('pytest_asyncio',)
#
#
# class TestAdditionalContentService:
#
#     @pytest.mark.asyncio
#     @patch('conversation_core.cobalt.services.cobalt_search_service.search')
#     async def test_additional_content_search(self,
#                                              mock_search,
#                                              additional_content_data):
#         mock_search.return_value = additional_content_data
#         question = "This is a test question?"
#         jurisdictions = ["ALLCASES"]
#         content_types = [AdditionalContentTypes.ADMIN, AdditionalContentTypes.KNOWHOW,
#                          AdditionalContentTypes.ANALYTICAL]
#         include_snippets = False
#         expected = AdditionalSupportingMaterial(
#             admin_decision=[AdditionalContent(content_type=AdditionalContentTypes.ADMIN,
#                                               global_rank=1,
#                                               source_guid="I101b55cb923811e8a5b3e3d9e23d7429"),
#                             AdditionalContent(content_type=AdditionalContentTypes.ADMIN,
#                                               global_rank=2,
#                                               source_guid="If1fa6018955311e598dc8b09b4f043e0"),
#                             AdditionalContent(content_type=AdditionalContentTypes.ADMIN,
#                                               global_rank=3,
#                                               source_guid="I746c922ceb5111e79bf099c0ee06c731")],
#             practical_law=[AdditionalContent(content_type=AdditionalContentTypes.KNOWHOW,
#                                              global_rank=1,
#                                              source_guid="Ibabdd72c642411e38578f7ccc38dcbee"),
#                            AdditionalContent(content_type=AdditionalContentTypes.KNOWHOW,
#                                              global_rank=2,
#                                              source_guid="I1c635e4aef2811e28578f7ccc38dcbee"),
#                            AdditionalContent(content_type=AdditionalContentTypes.KNOWHOW,
#                                              global_rank=3,
#                                              source_guid="I62f25edc34a211ed9f24ec7b211d8087")],
#             secondary_sources=[AdditionalContent(content_type=AdditionalContentTypes.ANALYTICAL,
#                                                  global_rank=1,
#                                                  source_guid="I767da1715aef11dbbe1cf2d29fe2afe6"),
#                                AdditionalContent(content_type=AdditionalContentTypes.ANALYTICAL,
#                                                  global_rank=2,
#                                                  source_guid="I1de43b5534c211dea066a526b6d82c9d"),
#                                AdditionalContent(content_type=AdditionalContentTypes.ANALYTICAL,
#                                                  global_rank=3,
#                                                  source_guid="Ia8280e05cb6e11db9199e1357fb88e60")]
#         )
#         loop = asyncio.get_event_loop()
#         task = loop.create_task(
#             additional_content_search(question,
#                                       jurisdictions,
#                                       content_types,
#                                       RAGSettings(cobalt_settings=CobaltSettings()),
#                                       include_snippets))
#         await task
#         actual: AdditionalSupportingMaterial = task.result()
#         assert actual == expected
#
#     @pytest.mark.asyncio
#     @patch('conversation_core.cobalt.services.cobalt_search_service.snippets')
#     @patch('conversation_core.cobalt.services.cobalt_search_service.search')
#     async def test_additional_content_search_with_snippets(self,
#                                                            mock_search,
#                                                            mock_snippets,
#                                                            additional_content_data,
#                                                            additional_content_snippets_data):
#         mock_search.return_value = additional_content_data
#         mock_snippets.return_value = additional_content_snippets_data
#         question = "This is a test question?"
#         jurisdictions = ["ALLCASES"]
#         content_types = [AdditionalContentTypes.ADMIN, AdditionalContentTypes.KNOWHOW,
#                          AdditionalContentTypes.ANALYTICAL]
#         include_snippets = True
#         loop = asyncio.get_event_loop()
#         task = loop.create_task(
#             additional_content_search(question,
#                                       jurisdictions,
#                                       content_types,
#                                       RAGSettings(cobalt_settings=CobaltSettings()),
#                                       include_snippets))
#         await task
#         actual: AdditionalSupportingMaterial = task.result()
#         assert len(actual.admin_decision) == 3
#         assert len(actual.practical_law) == 3
#         assert len(actual.secondary_sources) == 3
#         for admin in actual.admin_decision:
#             assert len(admin.snippets) == 4
#         for pract_law in actual.practical_law:
#             assert len(pract_law.snippets) == 4
#         for sec_src in actual.secondary_sources:
#             assert len(sec_src.snippets) == 4
#
#     @pytest.mark.asyncio
#     async def test_no_additional_content_search(self):
#         question = "This is a test question?"
#         jurisdictions = ["ALLCASES"]
#         content_types = []
#         include_snippets = True
#         loop = asyncio.get_event_loop()
#         task = loop.create_task(
#             additional_content_search(question,
#                                       jurisdictions,
#                                       content_types,
#                                       RAGSettings(),
#                                       include_snippets
#                                       ))
#         await task
#         actual: AdditionalSupportingMaterial = task.result()
#         assert actual is None
