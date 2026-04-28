# from utils.reranker import *
#
#
# class TestReranker:
#     class TestReplaceCites:
#
#         def test_replace_cites(self, answer_data_cites, answer_data_cites_reranked):
#             ga = answer_data_cites.get('answer')
#             answer = GeneratedAnswer(**ga)
#             expected_answer_reranked = SearchSummarizationOutput(**answer_data_cites_reranked)
#
#             actual_answer_reranked = replace_cites(answer, 1)
#
#             assert expected_answer_reranked == actual_answer_reranked
#
#     class TestAssignNewGlobalRank:
#
#         def test_assign_new_global_rank(self):
#             first_cite = InLineCite(start_offset=0, end_offset=1, source_guid='', content_type='CASE',
#                                     inline_global_rank=1, supporting_passages=[], royalty_id='0')
#             second_cite = InLineCite(start_offset=2, end_offset=3, source_guid='', content_type='CASE',
#                                      inline_global_rank=99, supporting_passages=[], royalty_id='0')
#             third_cite = InLineCite(start_offset=4, end_offset=5, source_guid='', content_type='CASE',
#                                     inline_global_rank=54, supporting_passages=[], royalty_id='0')
#             cites = [first_cite, second_cite, third_cite]
#             actual_cites_reranked = assign_new_global_rank(cites)
#
#             assert actual_cites_reranked[0] == first_cite
#             assert actual_cites_reranked[0].inline_global_rank == 1
#             assert actual_cites_reranked[1] == third_cite
#             assert actual_cites_reranked[1].inline_global_rank == 2
#             assert actual_cites_reranked[2] == second_cite
#             assert actual_cites_reranked[2].inline_global_rank == 3
